# ATOMS3R-CAM-M12 — Device Reference

**Complete hardware and firmware reference for the M5Stack AtomS3R-CAM (M12) device**

This document provides everything you need to write your own firmware for this device: what chips are on-board, how they're physically connected, the complete pinout mapping, and where to find the initialization code and APIs in this repository.

---

## Table of Contents

- [Overview](#overview)
- [Hardware Components](#hardware-components)
- [Bus Topology](#bus-topology)
- [Complete Pinout](#complete-pinout)
- [Initialization Sequence](#initialization-sequence)
- [API Reference](#api-reference)
- [Datasheets and Schematics](#datasheets-and-schematics)

---

## Overview

The **M5Stack AtomS3R-CAM (M12)** is a compact development board built around an ESP32-S3 microcontroller with an integrated camera module. This device combines:

- **ESP32-S3-PICO-1-N8R8** — A complete SoC module with dual-core Xtensa LX7 processors, WiFi/Bluetooth, 8MB flash, and 8MB PSRAM
- **OV3660 camera sensor** — A 3MP CMOS image sensor with M12 lens mount
- **BMI270 6-axis IMU** — Accelerometer and gyroscope for motion sensing
- **BMM150 magnetometer** — 3-axis magnetic field sensor (connected via BMI270's sensor hub)
- **IR transmitter** — NEC protocol infrared LED driver
- **External I2C port** — HY2.0-4P connector for additional peripherals

The firmware in this repository demonstrates a USB webcam (UVC) implementation plus a WiFi web server that exposes camera, IMU, and IR control APIs. This reference document explains the hardware architecture so you can build your own applications.

---

## Hardware Components

### ESP32-S3-PICO-1-N8R8 (Main SoC Module)

The ESP32-S3-PICO-1-N8R8 is Espressif's compact system-in-package module that includes:

- **Dual-core Xtensa LX7 processors** (up to 240 MHz)
- **8MB SPI flash** (for program storage)
- **8MB SPI PSRAM** (for frame buffers and runtime data)
- **WiFi 802.11 b/g/n** and **Bluetooth 5.0**
- **USB Serial/JTAG** interface for programming and debugging
- **Rich GPIO peripheral set** (45+ GPIOs, multiple I2C/SPI/UART interfaces)

This firmware uses a **hybrid approach**: core hardware initialization uses **ESP-IDF** APIs (the native Espressif framework), while the web server layer uses **Arduino** libraries (`ESPAsyncWebServer`, `WiFi`, etc.) for rapid development. The camera subsystem uses Espressif's **esp32-camera** component, which provides a unified API for various camera sensors.

**Key characteristics:**
- The ESP32-S3 has dedicated hardware for camera interfaces (DVP/I2S)
- PSRAM is essential for camera frame buffers (frames are typically 50-200KB)
- The USB interface can operate as a UVC (USB Video Class) device, allowing the board to appear as a standard webcam

### BMI270 — 6-Axis Inertial Measurement Unit

The **BMI270** is Bosch Sensortec's low-power IMU combining a 3-axis accelerometer and 3-axis gyroscope. It's designed for motion tracking, gesture recognition, and orientation detection in mobile devices and wearables.

**Key features:**
- **Accelerometer**: ±2g, ±4g, ±8g, ±16g ranges
- **Gyroscope**: ±125°/s, ±250°/s, ±500°/s, ±1000°/s, ±2000°/s ranges
- **Sensor Hub**: Built-in auxiliary I2C master for connecting additional sensors
- **FIFO**: 1024-byte buffer for batch data collection
- **Low power**: Optimized for battery-powered applications

**How it's connected:**
The BMI270 is connected to the ESP32's **internal I2C bus** (`I2C_NUM_0`) using GPIO0 (SCL) and GPIO45 (SDA). The device uses I2C address `0x69` (7-bit). The firmware configures the sensor for 50Hz output data rate with ±4g accelerometer range and ±2000°/s gyroscope range.

**Why it matters:**
The BMI270 serves as both a motion sensor and a **sensor hub gateway**. The BMM150 magnetometer is not directly connected to the ESP32—instead, it's connected to the BMI270's auxiliary I2C interface. This allows the ESP32 to read all 9-axis sensor data (accel + gyro + mag) through a single I2C transaction to the BMI270, which then fetches magnetometer data from the BMM150 automatically.

### BMM150 — 3-Axis Magnetometer

The **BMM150** is Bosch Sensortec's digital geomagnetic sensor, providing magnetic field measurements for compass applications and orientation sensing.

**Key features:**
- **Measurement range**: ±1300 µT (microtesla)
- **Resolution**: 0.3 µT
- **Data rate**: Configurable (2-30 Hz)
- **I2C interface**: Standard I2C slave device

**How it's connected:**
The BMM150 is **not directly connected to the ESP32**. Instead, it's mounted on the BMI270 module and connected to the BMI270's **auxiliary I2C interface** (sensor hub). This creates a two-level bus hierarchy:

```
ESP32 (I2C master)
  └─> BMI270 (I2C slave + AUX I2C master)
       └─> BMM150 (I2C slave on AUX bus)
```

**Why this architecture:**
- **Unified data collection**: The ESP32 can read all 9-axis data (accel/gyro/mag) in a single burst read from BMI270 registers
- **Reduced bus traffic**: The BMI270 handles the BMM150 communication internally
- **Synchronized sampling**: The BMI270 can coordinate sampling times between its own sensors and the auxiliary sensor
- **Lower power**: The BMI270 can manage the BMM150's power state automatically

**Initialization sequence:**
1. Initialize BMI270 on main I2C bus
2. Configure BMI270's auxiliary I2C interface (set BMM150's I2C address: `0x10`)
3. Use BMI270's register-based API to read/write BMM150 registers indirectly
4. Enable automatic data fetching: BMI270 reads BMM150 data and stores it in its own registers

### OV3660 Camera Sensor (M12 Module)

The **OV3660** is OmniVision's 3-megapixel CMOS image sensor, commonly used in embedded camera applications. The "M12" designation refers to the lens mount standard (M12 × 0.5 thread), which allows interchangeable lenses.

**Key features:**
- **Resolution**: Up to 2048×1536 (3MP), supports common formats like 1920×1080 (FHD), 1280×720 (HD), 640×480 (VGA)
- **Output format**: YUV422, RGB565, JPEG compression
- **Frame rate**: Up to 30 fps (depends on resolution and JPEG quality)
- **Control interface**: SCCB (Serial Camera Control Bus — I2C-compatible)
- **Data interface**: Parallel DVP (Digital Video Port) — 8-bit data bus

**How it's connected:**

The camera uses **two separate interfaces**:

1. **SCCB (Control Bus)** — I2C-like protocol for register configuration
   - `CAM_SDA` (GPIO12) — Serial data
   - `CAM_SCL` (GPIO9) — Serial clock
   - Used to configure exposure, gain, white balance, image size, etc.

2. **DVP (Data Bus)** — Parallel interface for pixel data
   - `Y2` through `Y9` (8 data lines) — Pixel data bits
   - `VSYNC` (GPIO10) — Vertical sync (frame start)
   - `HREF` (GPIO14) — Horizontal reference (line valid)
   - `PCLK` (GPIO40) — Pixel clock (data valid strobe)
   - `XCLK` (GPIO21) — External clock input (20 MHz, generated by ESP32)

3. **Power Control**
   - `POWER_N` (GPIO18) — Active-low power enable signal

**Data flow:**
When capturing a frame, the ESP32:
1. Configures the camera via SCCB (sets resolution, JPEG quality, etc.)
2. Enables the camera power via GPIO18
3. Waits for VSYNC to go high (start of frame)
4. Reads pixel data on Y2-Y9 synchronized to PCLK
5. HREF indicates when each line is valid
6. The ESP32's DVP hardware captures the data into PSRAM buffers
7. JPEG compression happens in hardware (if enabled) or software

**Firmware configuration:**
- XCLK frequency: 20 MHz (set via `CONFIG_CAMERA_XCLK_FREQ`)
- Default format: JPEG (reduces memory bandwidth)
- Frame buffer location: PSRAM (required for high-resolution frames)
- Frame buffer count: 1 (for UVC) or 2 (for web streaming)

### IR Transmitter (NEC Protocol)

The device includes an **infrared LED** driven by GPIO47, used for sending remote control commands using the NEC protocol (commonly used by TV remotes, air conditioners, etc.).

**How it works:**
- The ESP32's **RMT (Remote Control)** peripheral generates precise timing signals
- A **38 kHz carrier frequency** is modulated onto the GPIO signal
- The **NEC encoder** converts address/command bytes into pulse-width modulated signals
- The IR LED emits these signals, which can be received by standard IR receivers

**Protocol details:**
- **NEC protocol**: 8-bit address + 8-bit command (with inverted copies for error checking)
- **Carrier frequency**: 38 kHz (standard for consumer IR)
- **Duty cycle**: 33% (1/3 on, 2/3 off)
- **Timing resolution**: 1 µs (RMT configured for 1 MHz resolution)

**Use cases:**
- Control TVs, air conditioners, projectors, and other IR-controlled devices
- Home automation integration
- Universal remote functionality

### HY2.0-4P Connector (External I2C Port)

The **PORT.CUSTOM** connector is a 4-pin HY2.0 connector that exposes an external I2C bus for connecting additional peripherals (sensors, displays, etc.).

**Pinout:**
- **Black**: Ground (GND)
- **Red**: 5V power supply
- **Yellow**: I2C SDA (GPIO2)
- **White**: I2C SCL (GPIO1)

**Notes:**
- This is a **separate I2C bus** from the internal bus (which connects to BMI270)
- The ESP32-S3 has multiple I2C controllers, so you can use both buses simultaneously
- 5V power is available for peripherals that require it (most I2C devices use 3.3V, so check datasheets)
- Pull-up resistors may be needed on SDA/SCL depending on your connected devices

---

## Bus Topology

Understanding the bus architecture helps you debug communication issues and add new peripherals. Here's how everything connects:

```
┌─────────────────────────────────────────────────────────────┐
│                    ESP32-S3-PICO-1-N8R8                      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  I2C_NUM_0   │  │  I2C_NUM_1   │  │    RMT       │      │
│  │ (Internal)   │  │  (External)  │  │  (IR TX)     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│    GPIO0 (SCL)       GPIO1 (SCL)        GPIO47 (TX)         │
│    GPIO45 (SDA)      GPIO2 (SDA)                             │
└─────────┼─────────────────┼──────────────────┼──────────────┘
          │                 │                  │
          │                 │                  │
    ┌─────▼─────┐    ┌──────▼──────┐    ┌────▼─────┐
    │  BMI270   │    │  PORT.CUSTOM │    │ IR LED   │
    │  (IMU)    │    │  (External)  │    │          │
    └─────┬─────┘    │   I2C Bus    │    └──────────┘
          │          └──────────────┘
          │
    ┌─────▼─────┐
    │  BMM150   │
    │ (Mag)     │
    │ (via AUX) │
    └───────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Camera Interface                         │
│                                                               │
│  ┌──────────────┐  ┌──────────────────────────────────┐    │
│  │   SCCB/I2C   │  │         DVP (Parallel)            │    │
│  │  (Control)  │  │      (Pixel Data)                 │    │
│  └──────┬───────┘  └──────┬───────────────────────────┘    │
│         │                  │                                 │
│    GPIO12 (SDA)      GPIO10 (VSYNC)                          │
│    GPIO9 (SCL)       GPIO14 (HREF)                           │
│                      GPIO40 (PCLK)                           │
│                      GPIO21 (XCLK)                           │
│                      GPIO3,4,11,13,17,42,46,48 (Y2-Y9)      │
│                      GPIO18 (POWER_N)                        │
└─────────┼──────────────────┼─────────────────────────────────┘
          │                  │
          │                  │
    ┌─────▼─────┐      ┌─────▼─────┐
    │  OV3660   │      │  OV3660   │
    │  (SCCB)   │      │   (DVP)   │
    └───────────┘      └───────────┘
```

**Key points:**
- **Two independent I2C buses**: Internal (BMI270) and External (PORT.CUSTOM)
- **Camera uses dedicated interfaces**: SCCB for control, DVP for data (not standard I2C/SPI)
- **BMM150 is behind BMI270**: Not directly accessible from ESP32
- **IR uses RMT peripheral**: Hardware timing generation, not just GPIO toggling

---

## Complete Pinout

### Internal I2C Bus (BMI270)

| Signal Name | ESP32 GPIO | Direction | Notes |
|------------|-----------|-----------|-------|
| `SYS_SCL` (BMI270) | **GPIO0** | Output (ESP32) | I2C clock for internal bus |
| `SYS_SDA` (BMI270) | **GPIO45** | Bidirectional | I2C data for internal bus |

**Constants in code:**
- `HAL_PIN_I2C_INTER_SCL = 0`
- `HAL_PIN_I2C_INTER_SDA = 45`

**Usage:**
- Initialized in `main/usb_webcam_main.cpp` → `i2c_init()`
- Used by `m5::In_I2C` (M5Unified I2C wrapper)
- Bus speed: 400 kHz (standard fast-mode I2C)

### External I2C Bus (PORT.CUSTOM)

| Connector Pin | Function | ESP32 GPIO | Direction | Notes |
|--------------|----------|-----------|-----------|-------|
| **Black** | GND | — | — | Ground reference |
| **Red** | 5V | — | — | Power supply (for peripherals) |
| **Yellow** | I2C SDA | **GPIO2** | Bidirectional | External I2C data |
| **White** | I2C SCL | **GPIO1** | Output (ESP32) | External I2C clock |

**Constants in code:**
- `HAL_PIN_I2C_EXTER_SDA = 2`
- `HAL_PIN_I2C_EXTER_SCL = 1`

**Usage:**
- Available for connecting additional I2C devices
- Not used by default firmware (internal bus handles BMI270)
- Can be initialized separately if needed

### IR Transmitter

| Signal Name | ESP32 GPIO | Direction | Notes |
|------------|-----------|-----------|-------|
| `IR_LED_DRV` | **GPIO47** | Output | RMT peripheral output, 38 kHz carrier |

**Constants in code:**
- `HAL_PIN_IR_TX = 47`

**Usage:**
- Initialized in `main/usb_webcam_main.cpp` → `ir_init()`
- Uses ESP-IDF RMT peripheral with NEC encoder
- Carrier: 38 kHz, 33% duty cycle

### Camera Interface — SCCB Control Bus

| OV3660 Signal | ESP32 GPIO | Direction | Notes |
|--------------|-----------|-----------|-------|
| `CAM_SDA` | **GPIO12** | Bidirectional | SCCB data (I2C-compatible) |
| `CAM_SCL` | **GPIO9** | Output (ESP32) | SCCB clock |

**Constants in code:**
- `CAMERA_PIN_SIOD = 12` (defined in `main/utils/camera/camera_pin.h`)
- `CAMERA_PIN_SIOC = 9`

**Usage:**
- Configured automatically by `esp_camera_init()`
- Used for sensor register access (exposure, gain, resolution, etc.)
- SCCB is I2C-compatible but uses different addressing (see OV3660 datasheet)

### Camera Interface — DVP Data Bus

| OV3660 Signal | ESP32 GPIO | Direction | Notes |
|--------------|-----------|-----------|-------|
| `VSYNC` | **GPIO10** | Input (ESP32) | Vertical sync (frame start) |
| `HREF` | **GPIO14** | Input (ESP32) | Horizontal reference (line valid) |
| `PCLK` | **GPIO40** | Input (ESP32) | Pixel clock (data strobe) |
| `XCLK` | **GPIO21** | Output (ESP32) | External clock input to camera (20 MHz) |
| `Y2` | **GPIO3** | Input (ESP32) | Data bit 2 |
| `Y3` | **GPIO42** | Input (ESP32) | Data bit 3 |
| `Y4` | **GPIO46** | Input (ESP32) | Data bit 4 |
| `Y5` | **GPIO48** | Input (ESP32) | Data bit 5 |
| `Y6` | **GPIO4** | Input (ESP32) | Data bit 6 |
| `Y7` | **GPIO17** | Input (ESP32) | Data bit 7 |
| `Y8` | **GPIO11** | Input (ESP32) | Data bit 8 |
| `Y9` | **GPIO13** | Input (ESP32) | Data bit 9 (MSB) |

**Constants in code:**
- Defined in `main/utils/camera/camera_pin.h` when `CONFIG_CAMERA_MODULE_M5STACK_ATOMS3R_CAM=y`
- `CAMERA_PIN_VSYNC = 10`
- `CAMERA_PIN_HREF = 14`
- `CAMERA_PIN_PCLK = 40`
- `CAMERA_PIN_XCLK = 21`
- `CAMERA_PIN_D0 = 3` (Y2), `CAMERA_PIN_D1 = 42` (Y3), etc.

**Usage:**
- Configured automatically by `esp_camera_init()`
- ESP32-S3 has dedicated DVP hardware that captures data synchronized to PCLK
- Data is stored in PSRAM frame buffers
- XCLK is generated by ESP32's LEDC (LED Controller) peripheral

### Camera Power Control

| Signal Name | ESP32 GPIO | Direction | Notes |
|------------|-----------|-----------|-------|
| `POWER_N` | **GPIO18** | Output (ESP32) | Active-low power enable |

**Usage:**
- Controlled in `main/usb_webcam_main.cpp` → `enable_camera_power()`
- Configured as output with pulldown
- **Note**: The function configures the pin but doesn't explicitly set the level—verify active-low semantics in your implementation

---

## Initialization Sequence

Understanding the startup sequence helps you debug initialization issues and modify the firmware. Here's the complete flow:

### 1. Entry Point: `app_main()`

**Location:** `main/usb_webcam_main.cpp`

This is the ESP-IDF application entry point (equivalent to `main()` in standard C). The firmware performs initialization in this order:

```cpp
app_main() {
    // 1. Dependency injection (shared data, asset pool)
    shared_data_injection();
    asset_pool_injection();
    
    // 2. Hardware initialization
    enable_camera_power();  // GPIO18 setup
    i2c_init();             // Internal I2C bus
    imu_init();             // BMI270 + BMM150
    ir_init();              // RMT + NEC encoder
    camera_init();          // OV3660 via esp-camera
    
    // 3. Start services
    start_service_uvc();        // USB webcam
    start_service_web_server(); // WiFi + HTTP APIs
    
    // 4. Main loop (cleanup tasks)
    while (1) {
        vTaskDelay(...);
        cleanup_imu_ws_client();
    }
}
```

### 2. Camera Power Enable

**Function:** `enable_camera_power()`

**What it does:**
- Configures GPIO18 as output
- Sets pulldown mode
- **Important**: The function doesn't explicitly set the GPIO level—verify if `POWER_N` is active-low and needs to be driven low to enable power

**Code location:** `main/usb_webcam_main.cpp:24-32`

### 3. I2C Bus Initialization

**Function:** `i2c_init()`

**What it does:**
- Initializes `I2C_NUM_0` (internal bus)
- Uses M5Unified's `I2C_Class` wrapper: `m5::In_I2C.begin(I2C_NUM_0, HAL_PIN_I2C_INTER_SDA, HAL_PIN_I2C_INTER_SCL)`
- Performs I2C bus scan to detect connected devices
- **Expected device**: BMI270 at address `0x69`

**Code location:** `main/usb_webcam_main.cpp:49-57`

### 4. IMU Initialization (BMI270 + BMM150)

**Function:** `imu_init()`

**What it does:**
1. Creates `BMI270_Class` instance (wraps Bosch Sensor API)
2. Calls `BMI270_Class::init()`:
   - Initializes BMI270 via I2C
   - Uploads BMI270 configuration file (sensor-specific calibration data)
   - Configures accelerometer: ±4g range, 50 Hz ODR
   - Configures gyroscope: ±2000°/s range, 50 Hz ODR
3. Calls `BMI270_Class::initAuxBmm150()`:
   - Configures BMI270's auxiliary I2C interface
   - Sets BMM150 I2C address (`0x10`)
   - Initializes BMM150 via BMI270's register-based proxy
   - Configures BMM150 for normal mode, 30 Hz data rate

**Code location:**
- Initialization: `main/usb_webcam_main.cpp:59-80`
- BMI270 driver: `main/utils/bmi270/src/bmi270.cpp`
- Bosch Sensor API: `main/utils/bmi270/src/utilities/BMI270-Sensor-API/`

**Key APIs:**
- `BMI270_Class::readAcceleration(float& x, float& y, float& z)` — Returns values in G (gravity units)
- `BMI270_Class::readGyroscope(float& x, float& y, float& z)` — Returns values in degrees/second
- `BMI270_Class::readMagneticField(float& x, float& y, float& z)` — Returns values in microtesla (µT)

### 5. IR Transmitter Initialization

**Function:** `ir_init()`

**What it does:**
1. Creates RMT TX channel on GPIO47
2. Configures 38 kHz carrier frequency (33% duty cycle)
3. Installs NEC encoder (converts address/command to pulse patterns)
4. Enables RMT channel

**Code location:** `main/utils/ir_nec_transceiver/ir_nec_transceiver.c:118-149`

**Key APIs:**
- `ir_nec_transceiver_send(uint16_t addr, uint16_t cmd)` — Sends NEC command

### 6. Camera Initialization

**Function:** `camera_init()` → `my_camera_init()`

**What it does:**
1. Builds `camera_config_t` structure with pin assignments from `camera_pin.h`
2. Configures frame buffer location: PSRAM (required for large frames)
3. Sets pixel format: JPEG (reduces memory bandwidth)
4. Sets frame size: FHD (1920×1080) initially
5. Calls `esp_camera_init(&camera_config)` — ESP-IDF camera driver
6. Applies sensor-specific tuning:
   - Detects sensor PID (checks for `OV3660_PID`)
   - Adjusts brightness, saturation, vertical flip

**Code location:**
- Wrapper: `main/utils/camera/camera_init.c:31-117`
- ESP-IDF driver: `components/esp32-camera/` (managed component)

**Key APIs:**
- `esp_camera_fb_get()` — Capture single frame (returns `camera_fb_t*`)
- `esp_camera_fb_return(camera_fb_t*)` — Release frame buffer
- `esp_camera_sensor_get()` — Get sensor control interface

---

## API Reference

### IMU Data Access

**Shared data pattern:**
The firmware uses a `SharedData` singleton to coordinate access to IMU data between different services (web server, UVC, etc.).

**Reading IMU data:**
```cpp
// Update sensor readings (reads from BMI270/BMM150)
SharedData::UpdateImuData();

// Get latest values
const IMU::ImuData_t& data = SharedData::GetImuData();
float ax = data.accelX;  // Acceleration X (G)
float ay = data.accelY;  // Acceleration Y (G)
float az = data.accelZ;  // Acceleration Z (G)
float gx = data.gyroX;  // Gyroscope X (deg/s)
float gy = data.gyroY;  // Gyroscope Y (deg/s)
float gz = data.gyroZ;  // Gyroscope Z (deg/s)
float mx = data.magX;   // Magnetometer X (µT)
float my = data.magY;   // Magnetometer Y (µT)
float mz = data.magZ;   // Magnetometer Z (µT)
```

**Code locations:**
- Shared data: `main/utils/shared/shared.h` / `shared.cpp`
- IMU update: `main/utils/shared/shared.cpp:59-78`

### Camera Frame Capture

**Basic capture:**
```cpp
camera_fb_t* fb = esp_camera_fb_get();
if (fb != NULL) {
    // Use frame data
    uint8_t* jpeg_data = fb->buf;
    size_t jpeg_len = fb->len;
    int width = fb->width;
    int height = fb->height;
    
    // Release when done
    esp_camera_fb_return(fb);
}
```

**Changing resolution:**
```cpp
sensor_t* s = esp_camera_sensor_get();
s->set_framesize(s, FRAMESIZE_VGA);  // 640×480
s->set_framesize(s, FRAMESIZE_HD);   // 1280×720
s->set_framesize(s, FRAMESIZE_FHD);  // 1920×1080
```

**Adjusting image quality:**
```cpp
sensor_t* s = esp_camera_sensor_get();
s->set_quality(s, 10);        // JPEG quality (0-63, lower = higher quality)
s->set_brightness(s, 1);     // Brightness (-2 to +2)
s->set_saturation(s, -2);     // Saturation (-2 to +2)
s->set_contrast(s, 0);        // Contrast (-2 to +2)
```

**Code locations:**
- Camera init: `main/utils/camera/camera_init.c`
- Frame capture examples: `main/service/service_uvc.cpp`, `main/service/apis/api_camera.cpp`

### IR Command Transmission

**Sending NEC command:**
```cpp
// Direct API
ir_nec_transceiver_send(0x00, 0x45);  // Address, Command

// Via shared data (thread-safe)
SharedData::IrSendNecMsg(0x00, 0x45);
```

**NEC protocol notes:**
- Address and command are 8-bit values (0-255)
- The encoder automatically adds inverted copies for error checking
- Typical TV remote addresses are 0x00-0xFF, commands vary by manufacturer

**Code locations:**
- IR driver: `main/utils/ir_nec_transceiver/ir_nec_transceiver.c`
- Shared wrapper: `main/utils/shared/shared.cpp:80-83`

### Web Server APIs

The firmware exposes HTTP endpoints for camera, IMU, and IR control:

**Camera endpoints:**
- `GET /api/v1/capture` — Single JPEG snapshot
- `GET /api/v1/stream` — MJPEG stream (multipart/x-mixed-replace)

**IMU endpoint:**
- `WebSocket /api/v1/ws/imu_data` — Real-time IMU data (JSON)
  ```json
  {
    "ax": 0.12, "ay": -0.98, "az": 0.05,
    "gx": 1.2, "gy": -0.5, "gz": 0.1,
    "mx": 25.3, "my": -12.1, "mz": 45.8
  }
  ```

**IR endpoint:**
- `POST /api/v1/ir_send` — Send NEC command (JSON body)
  ```json
  {
    "addr": 0,
    "cmd": 69
  }
  ```

**Code locations:**
- API handlers: `main/service/apis/api_*.cpp`
- Web server setup: `main/service/service_web_server.cpp`

---

## Datasheets and Schematics

All datasheets and board documentation are stored in the `datasheets/` directory:

### Component Datasheets

- **ESP32-S3-PICO-1-N8R8**: [`datasheets/esp32-s3-pico-1_datasheet_en.pdf`](../datasheets/esp32-s3-pico-1_datasheet_en.pdf)
  - Complete module specifications, pinout, electrical characteristics
  - Flash/PSRAM interface details
  - Power consumption and thermal specifications

- **BMI270 IMU**: [`datasheets/BMI270.PDF`](../datasheets/BMI270.PDF)
  - Register map, sensor characteristics, calibration procedures
  - Sensor hub (auxiliary I2C) documentation
  - FIFO usage and interrupt configuration

- **BMM150 Magnetometer**: [`datasheets/BMM150.PDF`](../datasheets/BMM150.PDF)
  - Measurement ranges, calibration, data formats
  - I2C interface specification
  - Compass application notes

- **OV3660 Camera Sensor**: [`datasheets/OV3660_datasheet.pdf`](../datasheets/OV3660_datasheet.pdf)
  - Image sensor specifications, register map
  - SCCB protocol details
  - DVP timing diagrams and signal descriptions

### Board Documentation

- **Main Board Schematic**: [`datasheets/main_board_schematic.pdf`](../datasheets/main_board_schematic.pdf)
- **Extension Board Schematic**: [`datasheets/ext_board_schematic.pdf`](../datasheets/ext_board_schematic.pdf)
- **Pin Map Diagram**: [`datasheets/C126-M12_PinMap_01.jpg`](../datasheets/C126-M12_PinMap_01.jpg)
- **Model Size Reference**: [`datasheets/C126_M12_Model_Size_sch_01.png`](../datasheets/C126_M12_Model_Size_sch_01.png)

---

## Quick Reference: Code Locations

### Pin Definitions
- **Internal/External I2C + IR**: `main/hal_config.h`
- **Camera pins**: `main/utils/camera/camera_pin.h` (selected via `CONFIG_CAMERA_MODULE_M5STACK_ATOMS3R_CAM`)

### Initialization Entry Points
- **Main entry**: `main/usb_webcam_main.cpp` → `app_main()`
- **Camera init**: `main/utils/camera/camera_init.c` → `my_camera_init()`
- **IMU init**: `main/utils/bmi270/src/bmi270.cpp` → `BMI270_Class::init()` / `initAuxBmm150()`
- **IR init**: `main/utils/ir_nec_transceiver/ir_nec_transceiver.c` → `ir_nec_transceiver_init()`

### Driver Implementations
- **BMI270 wrapper**: `main/utils/bmi270/src/bmi270.{h,cpp}`
- **Bosch Sensor APIs**: `main/utils/bmi270/src/utilities/BMI270-Sensor-API/` and `BMM150-Sensor-API/`
- **IR RMT driver**: `main/utils/ir_nec_transceiver/ir_nec_transceiver.c`
- **Camera wrapper**: `main/utils/camera/camera_init.{h,c}`

### Service Layer
- **UVC (USB webcam)**: `main/service/service_uvc.cpp`
- **Web server**: `main/service/service_web_server.cpp`
- **HTTP APIs**: `main/service/apis/api_*.cpp`

### Configuration
- **Build config**: `sdkconfig` (ESP-IDF menuconfig output)
- **Camera module selection**: `CONFIG_CAMERA_MODULE_M5STACK_ATOMS3R_CAM=y`
- **XCLK frequency**: `CONFIG_CAMERA_XCLK_FREQ=20000000`

---

## Troubleshooting Tips

### Camera Not Initializing
- **Check power**: Verify GPIO18 (`POWER_N`) is configured correctly (may be active-low)
- **Check XCLK**: Ensure 20 MHz clock is being generated on GPIO21
- **Check I2C**: Verify SCCB bus (GPIO9/12) can communicate with sensor
- **Check PSRAM**: Camera requires PSRAM for frame buffers—verify PSRAM is detected at boot

### IMU Not Responding
- **Check I2C bus**: Verify internal I2C (GPIO0/45) is initialized before IMU init
- **Check address**: BMI270 uses address `0x69` (7-bit)
- **Check BMM150**: If magnetometer fails, check BMI270's auxiliary I2C configuration

### IR Not Working
- **Check GPIO**: Verify GPIO47 is configured as RMT output
- **Check carrier**: Ensure 38 kHz carrier is enabled (check RMT carrier config)
- **Check LED**: Verify IR LED is physically connected and not damaged

### Frame Capture Issues
- **PSRAM**: Ensure PSRAM is enabled and detected (check boot logs)
- **Frame size**: Large resolutions require more memory—reduce resolution or JPEG quality
- **Buffer count**: UVC uses 1 buffer, web streaming may need 2

---

**Last updated:** 2025-12-20  
**Firmware version:** See `main/usb_webcam_main.cpp` for version info
