#!/usr/bin/env python3
"""
Controls the RGB LED on a T9 Plus mini PC via a serial connection.

This script sends a 5-byte command packet to the device's serial port
to set the LED mode, brightness, and animation speed.
"""

import argparse
import sys
import time
from typing import Dict, List

# It's good practice to handle the case where the required library isn't installed.
try:
    import serial
except ImportError:
    print("Error: The 'pyserial' library is required. Please install it using 'pip install pyserial'")
    sys.exit(1)

# --- Protocol Constants ---

# The baud rate is fixed at 10000 for the device's controller.
BAUD_RATE: int = 10000

# The first byte sent in every command sequence.
BEGIN_BYTE: bytes = b'\xfa'

# Maps user-friendly mode names to their corresponding byte codes.
MODE_BYTES: Dict[str, bytes] = {
    'off':       b'\x04',
    'auto':      b'\x05',
    'rainbow':   b'\x01',
    'breathing': b'\x02',
    'cycle':     b'\x03',
}

# Maps brightness levels (1-5) to their byte codes.
# Note: The device uses inverted logic (level 5 is brightest).
BRIGHTNESS_BYTES: Dict[str, bytes] = {
    '5': b'\x01',  # Brightest
    '4': b'\x02',
    '3': b'\x03',
    '2': b'\x04',
    '1': b'\x05',  # Dimmest
}

# Maps speed levels (1-5) to their byte codes.
# Note: The device uses inverted logic (level 5 is fastest).
SPEED_BYTES: Dict[str, bytes] = {
    '5': b'\x01',  # Fastest
    '4': b'\x02',
    '3': b'\x03',
    '2': b'\x04',
    '1': b'\x05',  # Slowest
}


def build_command_packet(mode: str, brightness: str, speed: str) -> List[bytes]:
    """
    Constructs the 5-byte command sequence to be sent to the LED controller.

    Args:
        mode: The desired LED mode (e.g., 'rainbow').
        brightness: The brightness level as a string ('1' through '5').
        speed: The speed level as a string ('1' through '5').

    Returns:
        A list of single-byte objects representing the full command packet.
    """
    mode_byte = MODE_BYTES[mode]
    brightness_byte = BRIGHTNESS_BYTES[brightness]
    speed_byte = SPEED_BYTES[speed]

    # The checksum is the sum of the command bytes, truncated to 8 bits.
    checksum_val = (BEGIN_BYTE[0] + mode_byte[0] + brightness_byte[0] + speed_byte[0]) & 0xFF
    checksum_byte = checksum_val.to_bytes(1, 'big')

    return [
        BEGIN_BYTE,
        mode_byte,
        brightness_byte,
        speed_byte,
        checksum_byte,
    ]


def send_command(serial_port: str, packet: List[bytes], verbose: bool) -> None:
    """
    Opens the serial port and sends the command packet byte by byte.

    Args:
        serial_port: The name of the serial port (e.g., 'COM3' or '/dev/ttyUSB0').
        packet: The 5-byte command packet to send.
        verbose: If True, prints detailed debugging information.

    Raises:
        serial.SerialException: If the port cannot be opened or written to.
    """
    print(f"Connecting to {serial_port} at {BAUD_RATE} baud...")
    # Using a 'with' statement ensures the serial port is automatically closed.
    with serial.Serial(serial_port, BAUD_RATE, timeout=1) as s:
        print("Sending command packet...")
        for byte_to_send in packet:
            s.write(byte_to_send)
            # The hex representation is useful for debugging the protocol.
            if verbose:
                print(f"  -> Sent {byte_to_send.hex()}")
            # A small delay seems to be required between sending each byte.
            time.sleep(0.005)
    print("Command sent successfully.")


def main() -> None:
    """Parses command-line arguments and orchestrates sending the LED command."""
    # Set a platform-specific default for the serial port for user convenience.
    default_port = 'COM3' if sys.platform.startswith('win') else '/dev/ttyUSB0'

    parser = argparse.ArgumentParser(
        description='Control the LED lights on a T9 Plus mini PC.',
        formatter_class=argparse.RawTextHelpFormatter  # For better help text formatting
    )

    parser.add_argument(
        'mode',
        choices=MODE_BYTES.keys(),
        help='The desired LED mode.'
    )
    parser.add_argument(
        '--brightness',
        choices=BRIGHTNESS_BYTES.keys(),
        default='3',
        help='LED brightness (1=dimmest, 5=brightest).\nDefault: 3'
    )
    parser.add_argument(
        '--speed',
        choices=SPEED_BYTES.keys(),
        default='3',
        help='LED animation speed (1=slowest, 5=fastest).\nDefault: 3'
    )
    parser.add_argument(
        '--serial-port',
        default=default_port,
        help=f'The serial port to use.\nDefault: {default_port}'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output to show each byte being sent.'
    )

    args = parser.parse_args()

    if not args.verbose:
        print(f"Mode: {args.mode}, Brightness: {args.brightness}, Speed: {args.speed}")

    try:
        command_packet = build_command_packet(args.mode, args.brightness, args.speed)
        send_command(args.serial_port, command_packet, args.verbose)
    except serial.SerialException as e:
        print(f"\nError: Could not open serial port '{args.serial_port}'.")
        print(f"Details: {e}")
        print("Please ensure the device is connected and you have selected the correct port.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
