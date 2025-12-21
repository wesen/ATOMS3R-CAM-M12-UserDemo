---
Title: Firmware Architecture Analysis
Ticket: 001-FIRMWARE-ARCHITECTURE-BOOK
Status: active
Topics:
    - firmware
    - architecture
    - analysis
    - esp32
    - uvc
    - webserver
DocType: analysis
Intent: long-term
Owners: []
RelatedFiles: []
ExternalSources: []
Summary: "Comprehensive analysis of the AtomS3R-M12 firmware architecture, components, APIs, dependencies, and data flow"
LastUpdated: 2025-12-19T22:12:28.330110686-05:00
WhatFor: "Understanding the complete firmware structure, component interactions, and third-party dependencies"
WhenToUse: "When working on firmware modifications, debugging, or adding new features"
---

# Firmware Architecture Analysis

## Executive Summary

The AtomS3R-M12 firmware is an ESP32-S3 based USB webcam implementation that provides dual-mode operation:
1. **USB Video Class (UVC) Device**: Standard USB webcam compatible with Windows, Linux, and macOS
2. **WiFi Web Server**: HTTP/WebSocket-based camera control and streaming interface

The firmware uses ESP-IDF v5.1.x with an Arduino compatibility layer, FreeRTOS for task management, and a thread-safe singleton pattern for inter-component communication.

## Architecture Overview

### High-Level Structure

```
┌─────────────────────────────────────────────────────────┐
│                    app_main()                           │
│  (Initialization & Service Startup)                    │
└────────────┬────────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌─────▼──────┐
│  UVC   │      │   Web      │
│Service │      │  Server    │
└───┬────┘      └─────┬──────┘
    │                 │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │   SharedData     │
    │  (Singleton +    │
    │   Mutex Lock)    │
    └────────┬────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌─────▼──────┐
│ Camera │      │    IMU     │
│ Driver │      │  (BMI270)  │
└────────┘      └────────────┘
```

### Entry Point

**File**: `main/usb_webcam_main.cpp`

The `app_main()` function performs initialization in this order:
1. **Dependency Injection**: SharedData and AssetPool initialization
2. **Hardware Initialization**: Camera power, I2C, IMU, IR, Camera
3. **Service Startup**: UVC service and Web Server service
4. **Main Loop**: Periodic cleanup tasks

## Core Components

### 1. Service Layer (`main/service/`)

#### 1.1 UVC Service (`service_uvc.cpp`)

**Purpose**: Implements USB Video Class device functionality

**Key Features**:
- Dynamic resolution switching based on host requirements
- JPEG format support (MJPEG)
- Frame buffer management with PSRAM
- Service mode coordination (prevents simultaneous UVC/web server access)

**APIs Used**:
- `usb_device_uvc.h` - TinyUSB-based UVC implementation
- `esp_camera.h` - Camera frame capture
- `uvc_frame_config.h` - UVC frame configuration

**Callbacks**:
- `camera_start_cb()`: Called when host requests camera start
  - Maps UVC resolution to ESP32-Camera framesize
  - Configures JPEG quality based on resolution
  - Reinitializes camera with new parameters
- `camera_fb_get_cb()`: Called to get next frame
  - Checks service mode (blocks if web server is active)
  - Captures frame from camera
  - Converts to UVC frame format
- `camera_fb_return_cb()`: Called when frame is consumed
  - Returns frame buffer to camera driver
- `camera_stop_cb()`: Called when host stops streaming

**Supported Resolutions**:
- QVGA (320x240) - JPEG quality 10
- HVGA (480x320) - JPEG quality 10
- VGA (640x480) - JPEG quality 12
- SVGA (800x600) - JPEG quality 14
- HD (1280x720) - JPEG quality 16
- FHD (1920x1080) - JPEG quality 16

**Frame Buffer Configuration**:
- Buffer size: 1MB (1024KB) for ESP32-S3
- Frame buffer count: 1 (CAMERA_FB_COUNT)
- Location: PSRAM (CAMERA_FB_IN_PSRAM)

#### 1.2 Web Server Service (`service_web_server.cpp`)

**Purpose**: HTTP/WebSocket server for camera control and streaming

**Key Features**:
- WiFi Access Point mode (SSID: "AtomS3R-M12-WiFi")
- Static asset serving (gzipped HTML)
- RESTful API endpoints
- WebSocket support for real-time IMU data

**APIs Used**:
- `ESPAsyncWebServer.h` - Async web server
- `AsyncTCP.h` - Async TCP stack
- `Arduino.h` - Arduino compatibility layer
- `mooncake.h` - M5Stack utilities (spdlog)

**Endpoints**:
- `GET /` - Serves gzipped HTML interface (234KB)
- `GET /api/v1/capture` - Single JPEG capture
- `GET /api/v1/stream` - MJPEG video stream
- `WS /api/v1/ws/imu_data` - WebSocket IMU data stream
- `POST /api/v1/ir_send` - Send NEC IR command

**WiFi Configuration**:
- Mode: Access Point (softAP)
- SSID: "AtomS3R-M12-WiFi"
- Password: None (open network)
- Channel: 1
- Max connections: 1
- Hidden: false

### 2. API Layer (`main/service/apis/`)

#### 2.1 Camera API (`api_camera.cpp`)

**Endpoints**:
- `GET /api/v1/capture` → `sendJpg()`
  - Captures single JPEG frame
  - Returns JPEG or converts from other formats
  - Uses `AsyncFrameResponse` for efficient streaming
  
- `GET /api/v1/stream` → `streamJpg()`
  - MJPEG stream (multipart/x-mixed-replace)
  - Uses `AsyncJpegStreamResponse` class
  - Sets service mode to `mode_web_server`
  - Converts non-JPEG formats on-the-fly
  - Boundary: "123456789000000000000987654321"

**Helper Classes**:
- `AsyncBufferResponse`: Serves buffer data (BMP conversion)
- `AsyncFrameResponse`: Serves camera frame directly
- `AsyncJpegStreamResponse`: MJPEG streaming with chunked transfer

**Camera Control**:
- `getCameraStatus()`: Returns JSON with all camera settings
- `setCameraVar()`: Sets camera parameters (framesize, quality, brightness, etc.)

**Supported Camera Settings**:
- framesize, quality, brightness, contrast, saturation, sharpness
- special_effect, wb_mode, awb, awb_gain, aec, aec2, denoise
- ae_level, aec_value, agc, agc_gain, gainceiling
- bpc, wpc, raw_gma, lenc, hmirror, vflip, dcw, colorbar

#### 2.2 IMU API (`api_imu.cpp`)

**WebSocket Endpoint**: `/api/v1/ws/imu_data`

**Features**:
- Real-time IMU data streaming (10Hz - 100ms interval)
- JSON format: `{"ax":float, "ay":float, "az":float, "gx":float, "gy":float, "gz":float, "mx":float, "my":float, "mz":float}`
- Thread-safe connection management with mutex
- Automatic cleanup of disconnected clients

**Data Source**:
- BMI270 accelerometer/gyroscope
- BMM150 magnetometer (optional, if available)

**Threading**:
- Daemon task: `imu_data_ws_daemon` (4000 bytes stack, priority 5)
- Updates IMU data via `SharedData::UpdateImuData()`
- Serializes to JSON using ArduinoJson

#### 2.3 IR API (`api_ir.cpp`)

**Endpoint**: `POST /api/v1/ir_send`

**Features**:
- JSON body: `{"addr":uint16, "cmd":uint16}`
- Sends NEC protocol IR command
- Uses RMT peripheral for precise timing

**Implementation**:
- Uses `AsyncCallbackJsonWebHandler` for JSON parsing
- Calls `SharedData::IrSendNecMsg()` which delegates to IR transceiver

### 3. Utilities Layer (`main/utils/`)

#### 3.1 Shared Data (`shared/`)

**Purpose**: Thread-safe singleton for inter-component communication

**Files**:
- `shared.h` - Interface definition
- `shared.cpp` - Implementation
- `types.h` - Data structures

**Key Classes**:
- `SharedData`: Base singleton class
- `SharedData_StdMutex`: Thread-safe implementation using `std::mutex`

**Data Structure** (`SHARED_DATA::SharedData_t`):
```cpp
struct SharedData_t {
    ServiceMode::ServiceMode_t service_mode;  // Current service mode
    BMI270_Class* imu;                        // IMU sensor instance
    bool is_bmm150_ok;                        // Magnetometer status
    IMU::ImuData_t imu_data;                  // Latest IMU readings
};
```

**Service Modes**:
- `mode_none`: No active service
- `mode_uvc`: UVC service active
- `mode_web_server`: Web server streaming active

**Thread Safety**:
- `BorrowData()`: Locks mutex, returns reference
- `ReturnData()`: Unlocks mutex
- Prevents simultaneous camera access from UVC and web server

**Helper Methods**:
- `UpdateImuData()`: Reads from BMI270/BMM150 sensors
- `IrSendNecMsg()`: Sends IR command via transceiver
- `GetServiceMode()` / `SetServiceMode()`: Thread-safe mode access

#### 3.2 Camera Utilities (`camera/`)

**Files**:
- `camera_init.c/h` - Camera initialization wrapper
- `camera_pin.h` - Pin configuration for different camera modules

**Function**: `my_camera_init()`

**Parameters**:
- `xclk_freq_hz`: XCLK frequency (from CONFIG_CAMERA_XCLK_FREQ)
- `pixel_format`: PIXFORMAT_JPEG
- `frame_size`: FRAMESIZE_* enum
- `jpeg_quality`: 0-63 (lower = higher quality)
- `fb_count`: Frame buffer count (typically 1)

**Features**:
- Caches initialization state
- Reinitializes only if parameters change
- Returns all frames before reinit
- Sensor-specific tuning:
  - OV3660: brightness +1, saturation -2, vflip
  - OV2640: vflip
  - GC0308: hmirror off
  - GC032A: vflip

**Supported Camera Modules** (via `camera_pin.h`):
- ESP-S2-KALUGA
- ESP-S3-EYE
- ESP-S3-KORVO2
- M5STACK AtomS3R-CAM (default)
- CUSTOM (via Kconfig)

#### 3.3 IR NEC Transceiver (`ir_nec_transceiver/`)

**Files**:
- `ir_nec_transceiver.c/h` - Main transceiver implementation
- `ir_nec_encoder.c/h` - NEC protocol encoder

**Purpose**: Send NEC protocol IR commands

**APIs Used**:
- `driver/rmt_tx.h` - RMT transmitter
- `driver/rmt_rx.h` - RMT receiver (not used for TX)
- `ir_nec_encoder.h` - NEC encoder

**Configuration**:
- Resolution: 1MHz (1 tick = 1μs)
- Carrier frequency: 38kHz
- Duty cycle: 33%
- GPIO: HAL_PIN_IR_TX (pin 47)

**NEC Protocol Timing**:
- Leading code: 9000μs / 4500μs
- Zero bit: 560μs / 560μs
- One bit: 560μs / 1690μs
- Repeat code: 9000μs / 2250μs

**Functions**:
- `ir_nec_transceiver_init()`: Initializes RMT channel and encoder
- `ir_nec_transceiver_send()`: Sends address + command

#### 3.4 IMU Driver (`bmi270/`)

**Files**:
- `src/bmi270.cpp/h` - BMI270 wrapper class
- `src/utilities/BMI270-Sensor-API/` - Bosch BMI270 driver
- `src/utilities/BMM150-Sensor-API/` - Bosch BMM150 driver

**Purpose**: Accelerometer, gyroscope, and magnetometer support

**Class**: `BMI270_Class` (extends `m5::I2C_Device`)

**Features**:
- I2C communication via M5Unified
- Accelerometer: ±2g to ±16g range
- Gyroscope: ±125°/s to ±2000°/s range
- Magnetometer: BMM150 auxiliary sensor
- FIFO support
- Interrupt support (motion, gesture)
- Step counter

**Methods**:
- `init()`: Initialize BMI270
- `initAuxBmm150()`: Initialize BMM150 magnetometer
- `readAcceleration()`: Read accelerometer (G units)
- `readGyroscope()`: Read gyroscope (deg/s)
- `readMagneticField()`: Read magnetometer (μT)

**I2C Configuration**:
- Primary address: 0x68 (BMI2_I2C_PRIM_ADDR)
- Frequency: 400kHz
- Bus: Internal I2C (m5::In_I2C)

#### 3.5 Asset Pool (`assets/`)

**Purpose**: Memory-mapped static assets (web interface)

**Files**:
- `assets.cpp/h` - Asset pool management
- `images/types.h` - Image pool structure
- `images/index.html.gz` - Gzipped web interface (234KB)

**Class**: `AssetPool` (singleton)

**Features**:
- Memory-mapped flash partition (type 233, subtype 0x23)
- Size: 2MB
- Contains: HTML, images, fonts (if used)

**Structure** (`StaticAsset_t`):
```cpp
struct StaticAsset_t {
    ImagePool_t Image;  // Contains index_html_gz, m5_logo, etc.
};
```

**Initialization**:
- Partition found via `esp_partition_find_first()`
- Memory-mapped via `esp_partition_mmap()`
- Injected via `AssetPool::InjectStaticAsset()`

**Generation**:
- Desktop build: `CreateStaticAsset()` creates from files
- Binary output: `CreateStaticAssetBin()` writes to `AssetPool.bin`
- Flash: Binary flashed to `assetpool` partition

## Third-Party Dependencies

### External Git Repositories (`repos.json`)

1. **mooncake** (v1.2)
   - Repository: `https://github.com/Forairaaaaa/mooncake.git`
   - Purpose: M5Stack framework utilities
   - Used for: spdlog logging, I2C abstraction
   - Location: `components/mooncake/`

2. **arduino-esp32** (v3.0.2)
   - Repository: `https://github.com/Forairaaaaa/arduino_lite.git`
   - Purpose: Arduino compatibility layer for ESP-IDF
   - Used for: WiFi, WebServer, Arduino APIs
   - Location: `components/arduino-esp32/`
   - Key libraries used:
     - WiFi (softAP mode)
     - WebServer (via ESPAsyncWebServer)

3. **ArduinoJson** (v7.0.4)
   - Repository: `https://github.com/bblanchon/ArduinoJson.git`
   - Purpose: JSON parsing and generation
   - Used for: API request/response parsing, WebSocket JSON
   - Location: `components/ArduinoJson/`
   - Usage: `JsonDocument`, `serializeJson()`, `AsyncCallbackJsonWebHandler`

4. **esp32-camera** (v2.0.10)
   - Repository: `https://github.com/espressif/esp32-camera.git`
   - Purpose: Camera driver for ESP32
   - Used for: Camera initialization, frame capture, JPEG conversion
   - Location: `components/esp32-camera/`
   - Key APIs:
     - `esp_camera_init()` - Camera initialization
     - `esp_camera_fb_get()` - Get frame buffer
     - `esp_camera_fb_return()` - Return frame buffer
     - `frame2jpg()` - Convert frame to JPEG
     - `frame2bmp()` - Convert frame to BMP

5. **M5GFX** (0.1.16)
   - Repository: `https://github.com/Forairaaaaa/M5GFX.git`
   - Purpose: Graphics library
   - Used for: Display support (if display is present)
   - Location: `components/M5GFX/`
   - Note: Not actively used in current firmware

6. **M5Unified** (0.1.16)
   - Repository: `https://github.com/m5stack/M5Unified.git`
   - Purpose: M5Stack unified hardware abstraction
   - Used for: I2C bus management (`m5::I2C_Class`, `m5::In_I2C`)
   - Location: `components/M5Unified/`
   - Key classes:
     - `m5::I2C_Class` - I2C bus abstraction
     - `m5::I2C_Device` - Base class for I2C devices

### Vendored Components (`components/`)

1. **AsyncTCP**
   - Purpose: Asynchronous TCP stack
   - Used by: ESPAsyncWebServer
   - Location: `components/AsyncTCP/`

2. **ESPAsyncWebServer**
   - Purpose: Asynchronous HTTP/WebSocket server
   - Used for: Web server, API endpoints, WebSocket
   - Location: `components/ESPAsyncWebServer/`
   - Key classes:
     - `AsyncWebServer` - HTTP server
     - `AsyncWebSocket` - WebSocket server
     - `AsyncWebServerRequest` - HTTP request handler
     - `AsyncAbstractResponse` - Response base class

3. **usb_device_uvc**
   - Purpose: USB Video Class device implementation
   - Based on: TinyUSB
   - Used for: UVC device functionality
   - Location: `components/usb_device_uvc/`
   - Key APIs:
     - `uvc_device_config()` - Configure UVC device
     - `uvc_device_init()` - Initialize UVC device
     - Callbacks: `start_cb`, `fb_get_cb`, `fb_return_cb`, `stop_cb`

### ESP-IDF Managed Components (`managed_components/`)

**Active Components**:
- **tinyusb** (0.15.0~10) - USB stack (used by usb_device_uvc)
- **mdns** (1.4.0) - mDNS service (via arduino-esp32)
- **esp-dsp** (1.5.2) - Signal processing (via arduino-esp32)
- **libsodium** (1.0.20~1) - Cryptography (via arduino-esp32)

**Included but Not Used**:
- esp-sr (speech recognition)
- esp-rainmaker (cloud services)
- esp-modem (cellular modem)
- esp-zboss-lib / esp-zigbee-lib (Zigbee)
- littlefs (filesystem)
- esp-libhelix-mp3 (MP3 decoder)

**Note**: Many components are pulled in as dependencies of `arduino-esp32` but are not actively used in the firmware.

## Hardware Interfaces

### GPIO Configuration (`hal_config.h`)

**Camera Power**:
- GPIO 18: Camera power enable (output, pulldown)

**I2C**:
- Internal I2C (I2C_NUM_0):
  - SDA: GPIO 45 (HAL_PIN_I2C_INTER_SDA)
  - SCL: GPIO 0 (HAL_PIN_I2C_INTER_SCL)
- External I2C:
  - SDA: GPIO 2 (HAL_PIN_I2C_EXTER_SDA)
  - SCL: GPIO 1 (HAL_PIN_I2C_EXTER_SCL)

**IR Transmitter**:
- GPIO 47: IR TX (HAL_PIN_IR_TX)

**IMU Interrupt**:
- GPIO 16: IMU interrupt (hardware pulled up)

**Button**:
- GPIO 8: Button A (HAL_PIN_BUTTON_A)

**Camera Pins** (M5STACK AtomS3R-CAM):
- VSYNC: GPIO 10
- HREF: GPIO 14
- PCLK: GPIO 40
- XCLK: GPIO 21
- SIOD: GPIO 12
- SIOC: GPIO 9
- D0-D7: GPIO 3, 42, 46, 48, 4, 17, 11, 13

### Peripherals Used

1. **RMT** (Remote Control)
   - Channel: TX channel for IR transmission
   - Resolution: 1MHz
   - Used for: NEC IR protocol encoding

2. **I2C**
   - Controller: I2C_NUM_0
   - Speed: 400kHz
   - Devices: BMI270 (0x68), BMM150 (via BMI270)

3. **PSRAM**
   - Purpose: Camera frame buffers
   - Size: 8MB (hardware)
   - Usage: Camera frame storage

4. **SPI Flash**
   - Purpose: Firmware storage, asset pool partition
   - Size: 8MB (hardware)
   - Partitions:
     - Bootloader
     - Partition table
     - App firmware
     - Asset pool (type 233, subtype 0x23, 2MB)

5. **USB**
   - Mode: Device mode
   - Class: Video Class (UVC)
   - VID: 0x303A (Espressif)
   - PID: 0x8000

## Data Flow

### UVC Streaming Flow

```
Host Application
    ↓ (USB Request)
TinyUSB Stack
    ↓ (UVC Callback)
service_uvc.cpp::camera_fb_get_cb()
    ↓ (Check Service Mode)
SharedData::BorrowData()
    ↓ (Lock Mutex)
esp_camera_fb_get()
    ↓ (Capture Frame)
Camera Driver (PSRAM)
    ↓ (Return Frame)
Convert to UVC Format
    ↓ (Return Frame)
TinyUSB Stack
    ↓ (USB Transfer)
Host Application
```

### Web Server Streaming Flow

```
HTTP Client
    ↓ (GET /api/v1/stream)
ESPAsyncWebServer
    ↓ (Route Handler)
api_camera.cpp::streamJpg()
    ↓ (Create Response)
AsyncJpegStreamResponse
    ↓ (Set Service Mode)
SharedData::SetServiceMode(mode_web_server)
    ↓ (Capture Loop)
esp_camera_fb_get()
    ↓ (Convert if needed)
frame2jpg() (if not JPEG)
    ↓ (Send Chunk)
HTTP Client (MJPEG Stream)
```

### IMU Data Flow

```
FreeRTOS Task (imu_data_ws_daemon)
    ↓ (100ms interval)
SharedData::UpdateImuData()
    ↓ (Read Sensors)
BMI270_Class::readAcceleration()
BMI270_Class::readGyroscope()
BMI270_Class::readMagneticField()
    ↓ (Update SharedData)
SharedData::GetImuData()
    ↓ (Serialize JSON)
ArduinoJson::serializeJson()
    ↓ (Send WebSocket)
AsyncWebSocket::textAll()
    ↓ (Broadcast)
WebSocket Clients
```

## Threading Model

### FreeRTOS Tasks

1. **Main Task** (`app_main`)
   - Priority: Default (1)
   - Stack: Default
   - Purpose: Initialization and main loop

2. **TinyUSB Task** (`tusb_device_task`)
   - Created by: `usb_device_uvc`
   - Priority: Default
   - Purpose: USB stack processing

3. **IMU WebSocket Daemon** (`imu_data_ws_daemon`)
   - Created by: `api_imu.cpp::load_imu_apis()`
   - Stack: 4000 bytes
   - Priority: 5
   - Purpose: Periodic IMU data updates and WebSocket broadcasting

4. **ESPAsyncWebServer Tasks**
   - Created internally by ESPAsyncWebServer
   - Purpose: HTTP request handling, WebSocket management

### Synchronization

**Mutexes**:
- `SharedData_StdMutex::_mutex` - Protects SharedData access
- `api_imu.cpp::mutex` - Protects IMU WebSocket connection state

**Service Mode Coordination**:
- UVC service checks `GetServiceMode()` before capturing
- Web server sets `mode_web_server` when streaming starts
- Prevents simultaneous camera access

## Memory Management

### Static Memory

- **UVC Buffer**: 1MB allocated via `malloc()` in `start_service_uvc()`
- **Frame Buffers**: Allocated in PSRAM by camera driver
- **Asset Pool**: Memory-mapped from flash partition

### Dynamic Memory

- **Web Server**: Created via `new AsyncWebServer(80)`
- **WebSocket**: Created via `new AsyncWebSocket()`
- **JSON Documents**: Stack-allocated `JsonDocument` in handlers
- **Response Objects**: Created via `new` in API handlers (auto-deleted)

### Memory Layout

- **Flash**: 8MB
  - Bootloader: ~32KB
  - Partition table: ~4KB
  - App firmware: ~1-2MB
  - Asset pool: 2MB
  - Free space: ~4-5MB

- **PSRAM**: 8MB
  - Camera frame buffers: ~1MB per frame (depending on resolution)
  - Other dynamic allocations

- **SRAM**: 512KB
  - Stack for tasks
  - Static variables
  - Heap for small allocations

## API Reference Summary

### Camera APIs

**ESP32-Camera** (`esp_camera.h`):
- `esp_camera_init()` - Initialize camera
- `esp_camera_fb_get()` - Get frame buffer
- `esp_camera_fb_return()` - Return frame buffer
- `esp_camera_sensor_get()` - Get sensor object
- `frame2jpg()` - Convert frame to JPEG
- `frame2bmp()` - Convert frame to BMP

**Camera Init Wrapper** (`camera_init.h`):
- `my_camera_init()` - Wrapper with caching

### UVC APIs

**USB Device UVC** (`usb_device_uvc.h`):
- `uvc_device_config()` - Configure UVC device
- `uvc_device_init()` - Initialize UVC device

**Callbacks**:
- `start_cb` - Camera start callback
- `fb_get_cb` - Frame buffer get callback
- `fb_return_cb` - Frame buffer return callback
- `stop_cb` - Camera stop callback

### Web Server APIs

**ESPAsyncWebServer** (`ESPAsyncWebServer.h`):
- `AsyncWebServer::on()` - Register route handler
- `AsyncWebServer::begin()` - Start server
- `AsyncWebServerRequest::send()` - Send response
- `AsyncWebSocket::onEvent()` - WebSocket event handler
- `AsyncWebSocket::textAll()` - Broadcast text message

### Shared Data APIs

**SharedData** (`shared.h`):
- `SharedData::BorrowData()` - Lock and get data reference
- `SharedData::ReturnData()` - Unlock mutex
- `SharedData::GetServiceMode()` - Get current service mode
- `SharedData::SetServiceMode()` - Set service mode
- `SharedData::UpdateImuData()` - Update IMU readings
- `SharedData::GetImuData()` - Get latest IMU data
- `SharedData::IrSendNecMsg()` - Send IR command

### IMU APIs

**BMI270_Class** (`bmi270.h`):
- `init()` - Initialize BMI270
- `initAuxBmm150()` - Initialize BMM150 magnetometer
- `readAcceleration()` - Read accelerometer
- `readGyroscope()` - Read gyroscope
- `readMagneticField()` - Read magnetometer

### IR APIs

**IR NEC Transceiver** (`ir_nec_transceiver.h`):
- `ir_nec_transceiver_init()` - Initialize IR transmitter
- `ir_nec_transceiver_send()` - Send NEC command

## Build System

### CMake Structure

- **Root** (`CMakeLists.txt`): ESP-IDF project definition
- **Main** (`main/CMakeLists.txt`): Application component
  - Glob all `.c` and `.cpp` files
  - Include current directory

### Component Management

- **Git Submodules**: External repositories (mooncake, arduino-esp32, etc.)
- **ESP-IDF Component Manager**: Managed components (tinyusb, mdns, etc.)
- **Vendored**: Components included in repository (AsyncTCP, ESPAsyncWebServer, usb_device_uvc)

### Build Process

1. Fetch dependencies: `python fetch_repos.py` or `git submodule update --init --recursive`
2. Configure: `idf.py menuconfig` (optional)
3. Build: `idf.py build`
4. Flash: `idf.py -p <port> flash -b 1500000`
5. Flash asset pool: `parttool.py --port <port> write_partition --partition-name=assetpool --input asset_pool_gen/output/AssetPool.bin`

## Configuration

### Kconfig Options

**Camera** (`main/Kconfig.projbuild`):
- `CONFIG_CAMERA_MODULE_*` - Camera module selection
- `CONFIG_CAMERA_XCLK_FREQ` - XCLK frequency
- `CONFIG_CAMERA_MULTI_FRAMESIZE` - Multiple frame sizes support

**UVC**:
- `CONFIG_UVC_SUPPORT_TWO_CAM` - Dual camera support
- `CONFIG_TINYUSB_RHPORT_HS` - High-speed USB port

### Partition Table (`partitions.csv`)

- Bootloader
- Partition table
- App firmware (type: app)
- Asset pool (type: 233, subtype: 0x23, size: 2MB)

## Error Handling

### Camera Errors

- Camera init failure: Logged, service continues without camera
- Frame capture failure: Returns NULL, logged
- Frame size too large: Frame discarded, logged

### Service Errors

- UVC init failure: Logged, device may not enumerate
- Web server init failure: Logged, WiFi AP may not start
- IMU init failure: Logged, IMU features disabled

### Thread Safety

- SharedData mutex protects against race conditions
- Service mode prevents simultaneous camera access
- WebSocket connection state protected by mutex

## Performance Characteristics

### Frame Rates

- **UVC**: Depends on host application requirements (typically 15-30 fps)
- **Web Server**: Limited by network and JPEG conversion (~5-15 fps)
- **IMU**: 10Hz (100ms interval)

### Latency

- **UVC**: Low latency (direct USB transfer)
- **Web Server**: Higher latency (network + JPEG conversion)
- **IMU**: 100ms update interval

### Memory Usage

- **Camera Frames**: ~1MB per frame (FHD JPEG)
- **UVC Buffer**: 1MB static allocation
- **Web Server**: Minimal (async, no buffering)
- **IMU**: Minimal (9 floats per update)

## Limitations and Constraints

1. **Single Camera Access**: UVC and web server cannot access camera simultaneously
2. **Frame Buffer Count**: Only 1 frame buffer (may cause frame drops)
3. **WiFi AP**: Single client connection, open network
4. **Asset Pool**: Fixed size (2MB), requires separate flash step
5. **Camera Module**: Hardcoded pin configuration per module type

## Future Enhancement Opportunities

1. **Dual Service Mode**: Allow simultaneous UVC and web server with frame duplication
2. **Multiple Frame Buffers**: Increase `CAMERA_FB_COUNT` for better performance
3. **WiFi Station Mode**: Support connecting to existing WiFi networks
4. **OTA Updates**: Implement over-the-air firmware updates
5. **Configuration Web UI**: Web-based camera and system configuration
6. **SD Card Support**: Optional SD card for asset storage or recording
7. **Video Recording**: Record video to flash or SD card

## Search Queries Performed

During this analysis, the following searches and explorations were performed:

1. **Component Structure**: Explored `main/` directory structure to understand organization
2. **Service Layer**: Analyzed `service_uvc.cpp` and `service_web_server.cpp` for service implementation
3. **API Layer**: Examined all API files (`api_camera.cpp`, `api_imu.cpp`, `api_ir.cpp`) for endpoint definitions
4. **Shared Data**: Reviewed `shared.h/cpp` and `types.h` for data structures and thread safety
5. **Camera Utilities**: Analyzed `camera_init.c` and `camera_pin.h` for camera configuration
6. **IR Transceiver**: Examined `ir_nec_transceiver.c` for IR implementation details
7. **IMU Driver**: Reviewed `bmi270.h` for sensor interface
8. **Asset Pool**: Analyzed `assets.cpp/h` for asset management
9. **Dependencies**: Checked `repos.json` and `dependencies.lock` for third-party components
10. **Hardware Config**: Reviewed `hal_config.h` for GPIO configuration
11. **Build System**: Examined CMakeLists.txt files for build configuration
12. **UVC Component**: Reviewed `usb_device_uvc` README and source for UVC implementation

## Key Findings

1. **Architecture**: Clean separation between services, APIs, and utilities
2. **Thread Safety**: Proper mutex usage for shared data access
3. **Service Coordination**: Service mode prevents camera conflicts
4. **Dependencies**: Mix of Git submodules, vendored components, and ESP-IDF managed components
5. **Memory**: Efficient use of PSRAM for camera frames, flash for assets
6. **APIs**: RESTful HTTP endpoints with WebSocket for real-time data
7. **Hardware Abstraction**: Good use of M5Unified for I2C abstraction
8. **Error Handling**: Basic error handling with logging, graceful degradation

## Related Documentation

- ESP-IDF Documentation: https://docs.espressif.com/projects/esp-idf/
- ESP32-Camera: https://github.com/espressif/esp32-camera
- TinyUSB: https://github.com/hathach/tinyusb
- ESPAsyncWebServer: https://github.com/me-no-dev/ESPAsyncWebServer
- ArduinoJson: https://arduinojson.org/
