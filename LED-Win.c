#include <stdio.h>
#include <string.h>
#include <windows.h>

// Define the BEGIN byte for communication
#define BEGIN 0xfa

// Enum for different LED modes
enum Mode {
    MODE_OFF,
    MODE_AUTO,
    MODE_RAINBOW,
    MODE_BREATHING,
    MODE_CYCLE
};

// Enum for different brightness levels
enum Brightness {
    BRIGHTNESS_1,
    BRIGHTNESS_2,
    BRIGHTNESS_3,
    BRIGHTNESS_4,
    BRIGHTNESS_5
};

// Enum for different speed levels
enum Speed {
    SPEED_1,
    SPEED_2,
    SPEED_3,
    SPEED_4,
    SPEED_5
};

// Constant arrays to store the byte values for modes, brightness, and speed
static const unsigned char MODE_VALUES[] = {0x04, 0x05, 0x01, 0x02, 0x03};
static const unsigned char BRIGHTNESS_VALUES[] = {0x05, 0x04, 0x03, 0x02, 0x01};
static const unsigned char SPEED_VALUES[] = {0x05, 0x04, 0x03, 0x02, 0x01};

// Function to calculate the checksum for the command
static unsigned char checksum(unsigned char mode, unsigned char brightness, unsigned char speed) {
    return (BEGIN + mode + brightness + speed) & 0xff;
}

// Function to control the LED device via the serial port
static void control(const char* serial_port, unsigned char mode, unsigned char brightness, unsigned char speed) {
    // Open the serial port
    HANDLE hSerial = CreateFileA(serial_port, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hSerial == INVALID_HANDLE_VALUE) {
        printf("Failed to open serial port %s\n", serial_port);
        return;
    }

    // Configure the serial port settings
    DCB dcb = {0};  // Device Control Block
    dcb.DCBlength = sizeof(dcb);
    GetCommState(hSerial, &dcb);
    dcb.BaudRate = 10000;
    dcb.ByteSize = 8;
    dcb.StopBits = ONESTOPBIT;
    dcb.Parity = NOPARITY;
    SetCommState(hSerial, &dcb);

    // Configure the serial port timeouts
    COMMTIMEOUTS timeouts = {0};
    timeouts.ReadIntervalTimeout = 50;
    timeouts.ReadTotalTimeoutConstant = 50;
    timeouts.ReadTotalTimeoutMultiplier = 10;
    timeouts.WriteTotalTimeoutConstant = 50;
    timeouts.WriteTotalTimeoutMultiplier = 10;
    SetCommTimeouts(hSerial, &timeouts);

    DWORD bytesWritten;

    // Send the BEGIN byte
    unsigned char data[] = {BEGIN};
    WriteFile(hSerial, data, sizeof(data), &bytesWritten, NULL);
    Sleep(5); // Wait for 5 milliseconds

    // Send the mode byte
    data[0] = mode;
    WriteFile(hSerial, data, sizeof(data), &bytesWritten, NULL);
    Sleep(5); // Wait for 5 milliseconds

    // Send the brightness byte
    data[0] = brightness;
    WriteFile(hSerial, data, sizeof(data), &bytesWritten, NULL);
    Sleep(5); // Wait for 5 milliseconds

    // Send the speed byte
    data[0] = speed;
    WriteFile(hSerial, data, sizeof(data), &bytesWritten, NULL);
    Sleep(5); // Wait for 5 milliseconds

    // Send the checksum byte
    data[0] = checksum(mode, brightness, speed);
    WriteFile(hSerial, data, sizeof(data), &bytesWritten, NULL);

    // Close the serial port
    CloseHandle(hSerial);
}

// Function to print the usage information
static void printUsage(const char* programName) {
    printf("Usage: %s <mode> [--brightness <value>] [--speed <value>] [--serial-port <port>]\n", programName);
    printf("Modes: off, auto, rainbow, breathing, cycle\n");
    printf("Brightness values: 1, 2, 3, 4, 5 (default: 3)\n");
    printf("Speed values: 1, 2, 3, 4, 5 (default: 3)\n");
    printf("Serial port: (default: COM3)\n");
}

int main(int argc, char* argv[]) {
    // Check if the help flag is provided
    if (argc == 2 && (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0)) {
        printUsage(argv[0]);
        return 0;
    }

    // Check if the required arguments are provided
    if (argc < 2) {
        printUsage(argv[0]);
        return 1;
    }

    // Initialize the mode, brightness, speed, and serial port with default values
    unsigned char mode = MODE_VALUES[MODE_OFF];
    unsigned char brightness = BRIGHTNESS_VALUES[BRIGHTNESS_3 - 1];
    unsigned char speed = SPEED_VALUES[SPEED_3 - 1];
    const char* serial_port = "COM3";

    // Parse the mode argument
    if (strcmp(argv[1], "off") == 0) {
        mode = MODE_VALUES[MODE_OFF];
    } else if (strcmp(argv[1], "auto") == 0) {
        mode = MODE_VALUES[MODE_AUTO];
    } else if (strcmp(argv[1], "rainbow") == 0) {
        mode = MODE_VALUES[MODE_RAINBOW];
    } else if (strcmp(argv[1], "breathing") == 0) {
        mode = MODE_VALUES[MODE_BREATHING];
    } else if (strcmp(argv[1], "cycle") == 0) {
        mode = MODE_VALUES[MODE_CYCLE];
    } else {
        printf("Invalid mode: %s\n", argv[1]);
        printUsage(argv[0]);
        return 1;
    }

    // Parse the optional arguments
    for (int i = 2; i < argc; i++) {
        if (strcmp(argv[i], "--brightness") == 0) {
            i++;
            if (i >= argc) {
                printf("Missing brightness value\n");
                return 1;
            }
            int value = atoi(argv[i]);
            if (value >= 1 && value <= 5) {
                brightness = BRIGHTNESS_VALUES[value - 1];
            } else {
                printf("Invalid brightness value: %s\n", argv[i]);
                return 1;
            }
        } else if (strcmp(argv[i], "--speed") == 0) {
            i++;
            if (i >= argc) {
                printf("Missing speed value\n");
                return 1;
            }
            int value = atoi(argv[i]);
            if (value >= 1 && value <= 5) {
                speed = SPEED_VALUES[value - 1];
            } else {
                printf("Invalid speed value: %s\n", argv[i]);
                return 1;
            }
        } else if (strcmp(argv[i], "--serial-port") == 0) {
            i++;
            if (i >= argc) {
                printf("Missing serial port\n");
                return 1;
            }
            serial_port = argv[i];
        }
    }

    // Control the LED device with the parsed arguments
    control(serial_port, mode, brightness, speed);

    return 0;
}

