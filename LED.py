import argparse
import serial
import time

BEGIN = b'\xfa'
MODE = {
    'off': b'\x04',
    'auto': b'\x05',
    'rainbow': b'\x01',
    'breathing': b'\x02',
    'cycle': b'\x03',
}
BRIGHTNESS = {
    '1': b'\x05',
    '2': b'\x04',
    '3': b'\x03',
    '4': b'\x02',
    '5': b'\x01',
}
SPEED = {
    '1': b'\x05',
    '2': b'\x04',
    '3': b'\x03',
    '4': b'\x02',
    '5': b'\x01',
}

def checksum(mode, brightness, speed):
    int_checksum = (int.from_bytes(BEGIN)
                    + int.from_bytes(MODE[mode])
                    + int.from_bytes(BRIGHTNESS[brightness])
                    + int.from_bytes(SPEED[speed])) & 0xff
    return int_checksum.to_bytes()

def control(serial_port, mode, brightness, speed):
    s = serial.Serial(serial_port, 10000)  # The baud rate is fixed at 10000
    for i in [BEGIN,
              MODE[mode],
              BRIGHTNESS[brightness],
              SPEED[speed],
              checksum(mode, brightness, speed)]:
        s.write(i)
        time.sleep(0.005)
    s.close()

def main():
    parser = argparse.ArgumentParser(description='Control LED lights')
    parser.add_argument('mode', choices=MODE.keys(), help='LED mode')
    parser.add_argument('--brightness', choices=BRIGHTNESS.keys(), default='3', help='LED brightness (default: 3)')
    parser.add_argument('--speed', choices=SPEED.keys(), default='3', help='LED speed (default: 3)')
    parser.add_argument('--serial-port', default='COM3', help='Serial port (default: COM3)')
    args = parser.parse_args()

    control(args.serial_port, args.mode, args.brightness, args.speed)

if __name__ == '__main__':
    main()

