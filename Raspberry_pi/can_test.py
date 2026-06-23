import can
import time

bus = can.interface.Bus(channel='can0', bustype='socketcan')

print("CAN 송신 시작...")

while True:
    for speed_cmd in [0, 1, 2]:
        msg = can.Message(
            arbitration_id=0x100,
            data=[speed_cmd, 0, 0, 0, 0, 0, 0, 0],
            is_extended_id=False
        )
        bus.send(msg)
        print(f"송신: ID=0x100, data[0]={speed_cmd}")
        time.sleep(2)
