# LED Controller for T9 Plus Mini PC

A command-line utility to control the LED lights on a T9 Plus mini PC. This tool allows you to set different lighting modes, adjust brightness, and control the speed of the effects.

It is written in C and is compilable on both Windows and Linux. A Python version with identical functionality is also included.

## Features

  * Multiple lighting modes: `off`, `auto`, `rainbow`, `breathing`, and `cycle`.
  * 5 levels of brightness control.
  * 5 levels of speed control.
  * Cross-platform C source for Windows and Linux.
  * A standalone Python script (`LED.py`) that doesn't require compilation.

## Building the C Version

### On Windows

Open the **Developer PowerShell for VS 2022** and run this command:

```powershell
cl /O2 /W4 /Fe:LED.exe LED.c
```

### On Linux

Open your terminal and run this command. The `-Wall` flag is added to enable all common compiler warnings, which is good practice.

```bash
gcc -O2 -Wall -o LED LED.c
```

## Usage

The program is controlled via command-line arguments.

**Synopsis**

```bash
# On Windows
.\LED.exe <mode> [--brightness <value>] [--speed <value>] [--serial-port <port>]

# On Linux
./LED <mode> [--brightness <value>] [--speed <value>] [--serial-port <port>]
```

**Arguments**

  * **`mode`**: (Required) The lighting effect you want to set.
      * Available modes: `off`, `auto`, `rainbow`, `breathing`, `cycle`.
  * **`--brightness <value>`**: Sets the brightness level from 1 to 5. (Default: 3).
  * **`--speed <value>`**: Sets the effect speed from 1 to 5. (Default: 3).
  * **`--serial-port <port>`**: Specifies the serial port the device is connected to.
      * Default on Windows: `COM3`.
      * Default on Linux: `/dev/ttyUSB0`.

**Examples**

  * (Windows) Set a rainbow effect at maximum brightness and slowest speed on port `COM4`:
    ```powershell
    .\LED.exe rainbow --brightness 5 --speed 1 --serial-port COM4
    ```
  * (Linux) Turn off the LED on port `/dev/ttyUSB1`:
    ```bash
    ./LED off --serial-port /dev/ttyUSB1
    ```

## Using the Python Version

If you have Python, you can use the `LED.py` script without compiling anything.

**1. Install Prerequisites**
The script requires the `pyserial` library.

```bash
pip install pyserial
```

**2. Run the Script**
The arguments are identical to the C version.

```bash
python LED.py rainbow --brightness 5 --speed 1 --serial-port /dev/ttyUSB0
```

## License

This project is licensed under the MIT License.
