# driver_sim.py
import time
import socketio

sio = socketio.Client   ()

SERVER = "http://localhost:8000/ws"  # connect to same path used in server

trip_id = "trip123"
driver_id = "driver_1"

# Simulated path (lat, lng)
path = [
    (12.9716, 77.5946),
    (12.9720, 77.5952),
    (12.9725, 77.5960),
    (12.9730, 77.5968),
    (12.9737, 77.5975),
]

@sio.event
def connect():
    print("Connected to server")
    # announce / join room as driver
    sio.emit("join_trip", {"trip_id": trip_id, "role": "driver", "driver_id": driver_id})

@sio.event
def ack(data):
    print("Server ack:", data)

@sio.event
def disconnect():
    print("Disconnected from server")

def run_sim():
    sio.connect(SERVER, transports=["websocket"])
    try:
        for lat, lng in path:
            payload = {
                "trip_id": trip_id,
                "driver_id": driver_id,
                "lat": lat,
                "lng": lng,
                "speed": 20.0,
                "heading": 90
            }
            sio.emit("location_update", payload)
            print("Sent:", payload)
            time.sleep(2)  # wait 2s between updates
    finally:
        sio.disconnect()

if __name__ == "__main__":
    run_sim()
