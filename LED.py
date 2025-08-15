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

# For custom baud rates on Linux, we may need to perform a little magic.
if 'linux' in sys.platform:
    import fcntl
    import termios
    import ctypes

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


def _set_custom_baud_rate(fd: int, baudrate: int) -> None:
    """
    Sets a non-standard baud rate for a serial port file descriptor.

    This is a workaround for an issue where recent glibc updates have caused
    pyserial's default method of setting custom baud rates to fail with an
    'Invalid argument' error. This implementation mirrors the C version by
    using the termios2 struct and ioctl calls to set the rate directly.

    Args:
        fd: The file descriptor of the open serial port.
        baudrate: The desired non-standard baud rate.

    Raises:
        IOError: If the ioctl calls fail.
    """
    # The termios2 struct definition, based on <asm-generic/termbits.h>
    # NCCS is typically 32 on modern Linux systems.
    NCCS = 32
    BOTHER = 0o010000  # From <asm/termbits.h>

    class Termios2(ctypes.Structure):
        _fields_ = [
            ("c_iflag", ctypes.c_uint),
            ("c_oflag", ctypes.c_uint),
            ("c_cflag", ctypes.c_uint),
            ("c_lflag", ctypes.c_uint),
            ("c_line", ctypes.c_ubyte),
            ("c_cc", ctypes.c_ubyte * NCCS),
            ("c_ispeed", ctypes.c_uint),
            ("c_ospeed", ctypes.c_uint),
        ]

    # Calculate ioctl request numbers for termios2
    # These definitions are from <asm-generic/ioctl.h>
    _IOC_NRBITS = 8
    _IOC_TYPEBITS = 8
    _IOC_SIZEBITS = 14
    _IOC_DIRBITS = 2
    _IOC_WRITE = 1
    _IOC_READ = 2
    _IOC_NRSHIFT = 0
    _IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
    _IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
    _IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

    def _IOC(dir, type, nr, size):
        return (
            (dir << _IOC_DIRSHIFT) |
            (type << _IOC_TYPESHIFT) |
            (nr << _IOC_NRSHIFT) |
            (size << _IOC_SIZESHIFT)
        )

    def _IOR(type, nr, size_struct):
        return _IOC(_IOC_READ, type, nr, ctypes.sizeof(size_struct))

    def _IOW(type, nr, size_struct):
        return _IOC(_IOC_WRITE, type, nr, ctypes.sizeof(size_struct))

    TCGETS2 = _IOR(ord('T'), 0x2A, Termios2)
    TCSETS2 = _IOW(ord('T'), 0x2B, Termios2)

    termios2 = Termios2()
    # Get current settings
    fcntl.ioctl(fd, TCGETS2, termios2)

    # Set the custom baud rate
    termios2.c_cflag &= ~termios.CBAUD  # Clear standard baud rate bits
    termios2.c_cflag |= BOTHER         # Enable custom baud rate divisor
    termios2.c_ispeed = baudrate
    termios2.c_ospeed = baudrate

    # Apply the new settings
    fcntl.ioctl(fd, TCSETS2, termios2)


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
    # We open at a standard rate (9600) and then, if on Linux, use our
    # custom ioctl-based function to set the non-standard rate.
    with serial.Serial(serial_port, 9600, timeout=1) as s:
        if 'linux' in sys.platform:
            try:
                _set_custom_baud_rate(s.fileno(), BAUD_RATE)
            except IOError as e:
                print(f"\nError: Could not set custom baud rate via ioctl.")
                print(f"Details: {e}")
                print("This may happen on older kernels. Please check your system configuration.")
                sys.exit(1)
        else:
            # For non-Linux platforms, rely on pyserial's standard implementation
            s.baudrate = BAUD_RATE

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
