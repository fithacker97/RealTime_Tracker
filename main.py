# main.py
import asyncio
import socketio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
app.mount("/ws", socketio.ASGIApp(sio))   # Socket.IO endpoint is /ws

# (Optional) serve a simple HTML page for testing
app.mount("/static", StaticFiles(directory="static"), name="static")

# Keep track of driver -> trip mapping (in-memory)
# For production use persistent store (Redis)
drivers = {}  # driver_sid -> {"trip_id":..., "driver_id":...}

@sio.event
async def connect(sid, environ):
    print("Client connected:", sid)

@sio.event
async def disconnect(sid):
    print("Client disconnected:", sid)
    drivers.pop(sid, None)

# Passenger joins a trip room to receive updates
@sio.event
async def join_trip(sid, data):
    """
    data = {"trip_id": "trip123", "role": "passenger" or "driver", "driver_id": "..."}
    """
    trip_id = data.get("trip_id")
    role = data.get("role", "passenger")
    if not trip_id:
        return
    await sio.save_session(sid, {"trip_id": trip_id, "role": role})
    await sio.enter_room(sid, trip_id)
    print(f"{sid} joined room {trip_id} as {role}")

# Driver sends live location updates to their trip room
@sio.event
async def location_update(sid, data):
    """
    data example:
    {
      "trip_id": "trip123",
      "driver_id": "drv_1",
      "lat": 12.9716,
      "lng": 77.5946,
      "speed": 12.3,
      "heading": 120
    }
    """
    trip_id = data.get("trip_id")
    if not trip_id:
        return
    # Broadcast to everyone in that trip room except sender
    await sio.emit("location_update", data, room=trip_id, skip_sid=sid)
    # Optionally send ack to driver
    await sio.emit("ack", {"status": "ok"}, to=sid)

# Simple HTTP root to explain
@app.get("/", response_class=HTMLResponse)
async def index():
    return "<h3>Socket.IO location tracker backend running. Socket endpoint: /ws</h3>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
