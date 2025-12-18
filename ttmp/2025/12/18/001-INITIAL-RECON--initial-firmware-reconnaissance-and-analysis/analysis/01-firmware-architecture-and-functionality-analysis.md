---
Title: Firmware Architecture and Functionality Analysis
Ticket: 001-INITIAL-RECON
Status: active
Topics:
    - firmware
    - esp32
    - analysis
DocType: analysis
Intent: long-term
Owners: []
RelatedFiles: []
ExternalSources: []
Summary: Comprehensive analysis of AtomS3R-M12 USB webcam firmware architecture, components, and usage
LastUpdated: 2025-12-18T07:43:08.078321505-05:00
---

# Firmware Architecture and Functionality Analysis

## Executive Summary

The AtomS3R-M12 User Demo firmware is an ESP32-S3 based USB webcam implementation that provides dual-mode operation: USB Video Class (UVC) device and WiFi-based web server. The firmware supports multiple camera modules, includes IMU/magnetometer sensors, IR transmitter, and provides a web-based control interface. It uses ESP-IDF v5.1.4, Arduino compatibility layer, and M5Stack libraries for hardware abstraction.

## Project Overview

### Purpose
Transform an ESP32-S3 development board into a USB webcam device that can:
- Function as a standard UVC camera (plug-and-play USB webcam)
- Provide WiFi-based web interface for camera control and streaming
- Expose IMU/magnetometer data via WebSocket
- Control IR devices via NEC protocol

### Target Hardware

The firmware targets the **M5Stack AtomS3R-M12** development board, which is built around the ESP32-S3 system-on-chip. Understanding the hardware capabilities is crucial for developers working with this firmware.

**ESP32-S3 System-on-Chip**:
The ESP32-S3 is Espressif's dual-core Xtensa LX7 processor running at 240 MHz. It features:
- **Dual-core architecture**: Two 32-bit LX7 cores that can be used for symmetric multiprocessing or asymmetric task distribution
- **USB-OTG support**: Native USB On-The-Go functionality that enables the device to act as a USB device (like a webcam) without external USB-to-serial chips
- **PSRAM support**: The AtomS3R-M12 includes 8MB of PSRAM (Pseudo Static RAM), which is essential for storing camera frame buffers. PSRAM is slower than internal SRAM but provides much larger capacity for image data
- **WiFi capabilities**: Integrated 2.4 GHz WiFi with support for both Access Point (AP) and Station (STA) modes, though this firmware only uses AP mode
- **Flash memory**: 8MB of on-chip flash for storing firmware and data
- **GPIO and peripherals**: Rich set of GPIO pins, I2C, SPI, UART interfaces, and ADC channels

**Camera Module**:
The default camera module is the **M5Stack AtomS3R-CAM**, which features:
- **OV3660 sensor**: A 3-megapixel (2048x1536) CMOS image sensor with wide-angle F2.4 aperture lens and 120° field of view
- **Frame rate**: Capable of up to 30 FPS at lower resolutions
- **Interface**: Uses parallel DVP (Digital Video Port) interface with 8-bit data bus, plus SCCB (Serial Camera Control Bus, compatible with I2C) for configuration
- **Power requirements**: Requires external power control via GPIO (GPIO 18 in this firmware) with a 200ms stabilization delay after power-on

**Sensor Suite**:
The board includes two integrated sensors:
- **BMI270**: A 6-axis inertial measurement unit (IMU) providing 3-axis accelerometer and 3-axis gyroscope data. This sensor is used for motion detection, orientation tracking, and gesture recognition applications
- **BMM150**: A 3-axis geomagnetic sensor (magnetometer) that provides compass functionality. When combined with the BMI270, it forms a 9-axis sensor fusion system capable of determining absolute orientation

**Connectivity**:
- **USB Type-C**: Used for both power supply and USB communication. The USB-OTG capability allows the device to function as a USB device (UVC webcam) when connected to a host computer
- **WiFi**: Operates in Access Point mode, creating a network named "AtomS3R-M12-WiFi" that clients can connect to for web-based camera access

**Infrared Transmitter**:
- **IR LED**: Capable of transmitting NEC protocol infrared commands with 38kHz carrier frequency
- **Range**: Up to 12.46 meters without obstruction
- **Emission angle**: 180° coverage
- **Use cases**: Remote control of TVs, air conditioners, and other IR-controlled devices

### Build System

The firmware uses a hybrid build system that combines ESP-IDF's native build tools with Arduino compatibility libraries. This approach provides access to ESP-IDF's powerful features while maintaining compatibility with Arduino ecosystem libraries.

**ESP-IDF Framework (v5.1.4)**:
ESP-IDF (Espressif IoT Development Framework) is the official development framework for ESP32 series chips. Version 5.1.4 provides:
- **Native ESP32-S3 support**: Full feature set including USB-OTG, PSRAM management, and advanced power management
- **Component system**: Modular architecture where functionality is organized into components (camera driver, USB stack, WiFi, etc.)
- **Kconfig system**: Menu-based configuration system (`idf.py menuconfig`) that allows developers to enable/disable features and configure parameters without editing source code
- **FreeRTOS integration**: Built-in FreeRTOS real-time operating system for task scheduling and resource management
- **Hardware abstraction**: Low-level drivers for GPIO, I2C, SPI, UART, and other peripherals

**CMake Build System**:
ESP-IDF uses CMake for build configuration:
- **Component discovery**: Automatically discovers components in `components/` and `managed_components/` directories
- **Dependency resolution**: Handles component dependencies and build order automatically
- **Cross-compilation**: Configured for Xtensa architecture with GCC toolchain
- **Ninja backend**: Uses Ninja build system for fast incremental builds

**Arduino Compatibility Layer (v3.0.2)**:
The Arduino-ESP32 layer provides Arduino API compatibility:
- **Why it's used**: The web server implementation uses `ESPAsyncWebServer` library, which is built on Arduino APIs. The Arduino layer provides WiFi, TCP/IP stack, and HTTP server functionality
- **Integration**: The Arduino layer runs on top of ESP-IDF, using ESP-IDF's WiFi and networking stack but providing Arduino-style APIs
- **Limitations**: Not all Arduino libraries work seamlessly; some require ESP-IDF-specific modifications
- **Initialization**: Must call `initArduino()` before using Arduino APIs (done in `service_web_server.cpp`)

**Language Mix**:
- **C++**: Used for main application code, object-oriented abstractions (SharedData, AssetPool), and Arduino compatibility
- **C**: Used for low-level utilities, camera initialization, and IR transceiver code. This is common in embedded systems where C provides better control over memory and performance

**Where to learn more**:
- ESP-IDF Programming Guide: https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/
- Arduino-ESP32 Documentation: https://docs.espressif.com/projects/arduino-esp32/en/latest/
- CMake Documentation: https://cmake.org/documentation/

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    app_main()                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Dependency Injection                             │  │
│  │  - SharedData (singleton)                         │  │
│  │  - AssetPool (memory-mapped)                       │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Hardware Initialization                          │  │
│  │  - Camera power (GPIO 18)                         │  │
│  │  - I2C bus (internal)                             │  │
│  │  - IMU (BMI270 + BMM150)                          │  │
│  │  - IR transceiver                                 │  │
│  │  - Camera module                                  │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Service Layer                                    │  │
│  │  ┌──────────────┐  ┌──────────────────────────┐  │  │
│  │  │  UVC Service │  │  Web Server Service     │  │  │
│  │  │  (USB)       │  │  (WiFi AP)              │  │  │
│  │  └──────────────┘  └──────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Main Loop                                        │  │
│  │  - Cleanup tasks                                 │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Component Interaction

```
┌─────────────┐
│   Host PC   │
│  (USB/UVC)  │
└──────┬──────┘
       │ USB
       ▼
┌─────────────────┐     ┌──────────────┐
│  UVC Service    │◄────│  SharedData  │
│  (TinyUSB)      │     │  (Singleton) │
└────────┬────────┘     └──────┬───────┘
         │                     │
         │ Camera Frames       │ State
         │                     │
         ▼                     ▼
┌─────────────────┐     ┌──────────────┐
│  Camera Driver  │     │  Web Server  │
│  (esp32-camera) │     │  (WiFi AP)   │
└─────────────────┘     └──────────────┘
                                │
                                │ HTTP/WS
                                ▼
                         ┌──────────────┐
                         │  Web Client  │
                         └──────────────┘
```

## Core Components

### 1. Main Application (`main/usb_webcam_main.cpp`)

**Entry Point**: `app_main()`

**Initialization Sequence**:
1. **Dependency Injection**
   - `SharedData::Inject(new SharedData_StdMutex)` - Thread-safe singleton
   - `AssetPool::InjectStaticAsset()` - Load assets from flash partition

2. **Hardware Initialization**
   - Camera power enable (GPIO 18, 200ms delay)
   - I2C bus initialization (internal bus: SDA=45, SCL=0)
   - IMU initialization (BMI270 + BMM150)
   - IR transceiver initialization (GPIO 47)
   - Camera module initialization (JPEG, FHD, quality 6)

3. **Service Startup**
   - `start_service_uvc()` - USB UVC device
   - `start_service_web_server()` - WiFi AP + HTTP server

4. **Main Loop**
   - Periodic cleanup tasks (IMU WebSocket clients)

**Key Functions**:
- `enable_camera_power()` - Controls camera power via GPIO
- `i2c_init()` - Initializes I2C bus and scans devices
- `imu_init()` - Initializes BMI270 IMU and BMM150 magnetometer
- `ir_init()` - Initializes IR NEC transceiver
- `camera_init()` - Initializes camera module
- `asset_pool_injection()` - Memory-maps asset pool partition
- `shared_data_injection()` - Sets up SharedData singleton

### 2. UVC Service (`main/service/service_uvc.cpp`)

**Purpose**: Implements USB Video Class device functionality

The UVC (USB Video Class) service enables the device to function as a standard USB webcam that works with any operating system without requiring custom drivers. UVC is a USB device class specification that defines a standard protocol for video streaming over USB. When you plug the device into a computer, the host operating system recognizes it as a standard webcam and can use it with any application that supports webcams (video conferencing software, image capture tools, etc.).

**Understanding USB Video Class (UVC)**:
UVC is part of the USB specification maintained by the USB Implementers Forum. It defines:
- **Standard descriptors**: The device reports its capabilities (supported resolutions, frame rates, formats) through USB descriptors that the host reads during enumeration
- **Control requests**: The host can query and set camera parameters (brightness, contrast, resolution, etc.) using standard USB control requests
- **Streaming protocol**: Video data is transmitted over USB using either isochronous transfers (guaranteed bandwidth, may drop frames) or bulk transfers (reliable but variable timing)
- **Format negotiation**: The host selects a video format (MJPEG in this case) and resolution from the device's advertised capabilities
- **Driver-free operation**: Because UVC is standardized, operating systems include built-in drivers, eliminating the need for custom driver installation

**Architecture**: Callback-based
The UVC service uses a callback-driven architecture where the TinyUSB stack calls application-provided functions at key points in the streaming lifecycle:

- **`camera_start_cb()`**: Called when the host initiates video streaming. This callback receives the requested format (MJPEG), resolution (width/height), and frame rate. The firmware uses this information to reconfigure the camera hardware to match the host's requirements. This is where dynamic resolution switching happens - if the host requests 640x480, the camera is reinitialized with VGA settings.

- **`camera_fb_get_cb()`**: Called repeatedly by the TinyUSB stack when it needs a new frame to send to the host. This is the most critical callback as it's called at the frame rate (e.g., 30 times per second for 30 FPS). The function must:
  1. Check if web server is streaming (service mode check)
  2. Acquire a frame buffer from the camera driver
  3. Convert the frame buffer to UVC format structure
  4. Validate frame size doesn't exceed USB buffer limits
  5. Return the frame buffer pointer

- **`camera_fb_return_cb()`**: Called after the TinyUSB stack has finished transmitting the frame to the host. This is where the firmware returns the frame buffer to the camera driver's free pool so it can be reused for the next frame. Proper buffer management here is critical to prevent memory leaks and frame drops.

- **`camera_stop_cb()`**: Called when the host stops streaming (user closes the application, unplugs USB, etc.). This allows the firmware to clean up resources, stop camera capture, and reset service mode.

**Key Features**:

**Dynamic Camera Reconfiguration**: Unlike many webcams that have fixed resolutions, this firmware can dynamically reconfigure the camera hardware when the host requests a different resolution. When `camera_start_cb()` is called with new parameters, the firmware:
1. Checks if camera is already configured with the requested settings
2. If different, deinitializes the current camera configuration
3. Reinitializes with new resolution, JPEG quality, and frame buffer settings
4. This allows a single device to support multiple resolutions without rebooting

**Service Mode Coordination**: The firmware implements a service mode system to prevent conflicts between UVC streaming and web server streaming. Both services need exclusive access to camera frames, so:
- When UVC is active, web server requests return NULL frames
- When web server is streaming, UVC's `camera_fb_get_cb()` checks service mode and returns NULL if web server mode is detected
- This prevents frame corruption and ensures consistent streaming

**Frame Buffer Management**: 
- Frame buffers are allocated in PSRAM (8MB available on AtomS3R-M12) rather than internal SRAM (limited to ~500KB)
- Maximum frame buffer size is 1MB for ESP32-S3, which accommodates high-resolution JPEG frames
- The firmware uses a single frame buffer (reduced from 2) to save memory, which means frames must be processed and returned quickly to avoid drops

**Supported Resolutions**:
| Resolution | Width x Height | JPEG Quality | Frame Size Enum | Typical Use Case |
|------------|----------------|--------------|-----------------|------------------|
| QVGA       | 320 x 240      | 10           | FRAMESIZE_QVGA  | Low bandwidth, preview |
| HVGA       | 480 x 320      | 10           | FRAMESIZE_HVGA  | Mobile preview |
| VGA        | 640 x 480      | 12           | FRAMESIZE_VGA   | Standard webcam |
| SVGA       | 800 x 600      | 14           | FRAMESIZE_SVGA  | Higher quality |
| HD         | 1280 x 720     | 16           | FRAMESIZE_HD    | HD video calls |
| FHD        | 1920 x 1080    | 16           | FRAMESIZE_FHD   | Full HD recording |

**JPEG Quality Settings**: The firmware uses different JPEG quality values for different resolutions. Lower resolutions use lower quality (10) because the smaller image size means compression artifacts are less noticeable, while higher resolutions use higher quality (16) to preserve detail. JPEG quality ranges from 0-63, where higher values mean better quality but larger file sizes.

**Implementation Details**:

**TinyUSB Stack**: The firmware uses TinyUSB, an open-source USB device/host stack for embedded systems. TinyUSB handles:
- USB enumeration (device identification to host)
- Descriptor generation (telling host about device capabilities)
- Endpoint management (data transfer channels)
- Control request handling (host queries and commands)
- Isochronous/bulk transfer scheduling

The UVC implementation in this firmware uses TinyUSB's video class support, which provides the UVC protocol layer while the application provides the camera-specific callbacks.

**PSRAM Frame Buffers**: Camera frames are stored in PSRAM rather than internal SRAM because:
- High-resolution JPEG frames can be 100KB-1MB in size
- Internal SRAM is limited (~500KB total, shared with code and stack)
- PSRAM provides 8MB of additional memory
- Trade-off: PSRAM is slower than SRAM but still fast enough for camera frame rates

**Camera Reinitialization Logic**: The camera initialization function (`my_camera_init()`) is designed to be idempotent - calling it multiple times with the same parameters has no effect. It tracks current configuration and only reinitializes when parameters change. This prevents unnecessary camera resets that could cause frame drops.

**ESP-S3-EYE Special Support**: The ESP-S3-EYE development board includes an LCD display that shows animated "eyes" that open when camera streaming starts and close when it stops. This is implemented using FreeRTOS event groups to coordinate between the UVC service and the display driver.

**Where to learn more**:
- USB Video Class Specification: https://www.usb.org/document-library/video-class-v15-document-set
- TinyUSB Documentation: https://docs.tinyusb.org/
- ESP32-S3 USB-OTG Guide: https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/api-guides/usb-serial-jtag-console.html

### 3. Web Server Service (`main/service/service_web_server.cpp`)

**Purpose**: Provides WiFi-based web interface for camera control

**Features**:
- WiFi Access Point: "AtomS3R-M12-WiFi" (channel 1, max 1 client)
- HTTP server on port 80
- Serves compressed HTML from asset pool
- REST APIs for camera control
- WebSocket for real-time IMU data

**WiFi Configuration**:
- SSID: "AtomS3R-M12-WiFi"
- Channel: 1
- Max connections: 1
- Hidden: false

**Web Interface**:
- Root (`/`): Serves `index.html.gz` (234,419 bytes compressed)
- Content-Encoding: gzip

### 4. API Layer (`main/service/apis/`)

#### Camera API (`api_camera.cpp`)

**Endpoints**:
- `GET /api/v1/capture` - Single JPEG capture
  - Returns: JPEG image
  - Content-Type: `image/jpeg`
  - CORS: Enabled

- `GET /api/v1/stream` - MJPEG stream
  - Returns: Multipart MJPEG stream
  - Content-Type: `multipart/x-mixed-replace;boundary=123456789000000000000987654321`
  - Sets service mode to `mode_web_server` (blocks UVC)
  - CORS: Enabled

**Understanding MJPEG Streaming**:

MJPEG (Motion JPEG) is a video compression format where each frame is independently compressed as a JPEG image. Unlike modern video codecs (H.264, VP8) that use inter-frame compression (comparing frames to reduce data), MJPEG compresses each frame independently. This makes it:
- **Simple to implement**: No complex encoding algorithms needed
- **Low latency**: Each frame can be decoded immediately without waiting for other frames
- **CPU-friendly**: JPEG compression is well-optimized and can use hardware acceleration
- **Browser-compatible**: Most web browsers can display MJPEG streams natively

**Multipart/x-mixed-replace Protocol**:

The web server uses HTTP's `multipart/x-mixed-replace` content type to stream continuous video. This is an older but widely-supported streaming method:

- **Multipart**: The response contains multiple parts (each JPEG frame is a separate part)
- **x-mixed-replace**: A non-standard but widely-implemented extension that tells the browser to replace the previous content with new content (rather than appending)
- **Boundary**: A unique string (`123456789000000000000987654321`) that separates each frame in the stream
- **Continuous stream**: The connection stays open and frames are sent continuously

**Stream Format**:
```
HTTP/1.1 200 OK
Content-Type: multipart/x-mixed-replace;boundary=123456789000000000000987654321
Transfer-Encoding: chunked

--123456789000000000000987654321
Content-Type: image/jpeg
Content-Length: <frame_size>

<JPEG frame 1 data>
--123456789000000000000987654321
Content-Type: image/jpeg
Content-Length: <frame_size>

<JPEG frame 2 data>
--123456789000000000000987654321
...
```

**How It Works**:
1. Client requests `/api/v1/stream`
2. Server creates `AsyncJpegStreamResponse` object
3. Server sets service mode to `mode_web_server` (prevents UVC access)
4. Server enters loop:
   - Captures frame from camera
   - Converts to JPEG if needed (camera may output raw format)
   - Sends boundary marker
   - Sends Content-Type and Content-Length headers
   - Sends JPEG frame data
   - Repeats for next frame
5. When client disconnects, service mode resets to `mode_none`

**Frame Rate and Performance**:
- **Frame rate**: Limited by camera capture speed and network bandwidth
- **Typical performance**: 5-15 FPS depending on resolution and network conditions
- **Bandwidth**: Each frame is 10-100KB depending on resolution and JPEG quality
- **Latency**: Low latency since frames are sent immediately after capture

**Browser Compatibility**:
- **Chrome/Edge**: Full support
- **Firefox**: Full support
- **Safari**: Full support
- **Mobile browsers**: Generally supported

**Advantages over WebRTC/HLS**:
- **Simplicity**: No complex streaming protocols
- **Compatibility**: Works with simple HTTP GET requests
- **Low overhead**: Minimal protocol overhead
- **Easy debugging**: Can view stream in browser or save frames

**Disadvantages**:
- **Bandwidth**: Less efficient than modern codecs (larger file sizes)
- **No audio**: MJPEG is video-only
- **No adaptive bitrate**: Fixed quality per frame

**Camera Control** (referenced but not loaded in current code):
- `GET /api/v1/status` - Get camera sensor status (JSON)
- `GET /api/v1/control?var=<param>&val=<value>` - Set camera parameter

**Supported Camera Parameters**:
- `framesize` - Resolution (0-13)
- `quality` - JPEG quality (0-63)
- `brightness` - Brightness (-2 to 2)
- `contrast` - Contrast (-2 to 2)
- `saturation` - Saturation (-2 to 2)
- `sharpness` - Sharpness (-2 to 2)
- `awb` - Auto white balance (0/1)
- `agc` - Auto gain control (0/1)
- `aec` - Auto exposure control (0/1)
- `hmirror` - Horizontal mirror (0/1)
- `vflip` - Vertical flip (0/1)
- And many more...

#### IMU API (`api_imu.cpp`)

**WebSocket Endpoint**:
- `WS /api/v1/ws/imu_data` - Real-time IMU data stream

The IMU API provides real-time sensor data via WebSocket, allowing web applications to receive continuous updates about the device's motion and orientation. WebSocket is used instead of HTTP polling because it provides lower latency and reduces overhead for high-frequency data updates.

**Understanding the Sensor Suite**:

**BMI270 Inertial Measurement Unit (IMU)**:
The BMI270 is a 6-axis IMU combining:
- **3-axis Accelerometer**: Measures linear acceleration in X, Y, and Z axes. Units are in g-force (1g = 9.8 m/s²). Can detect:
  - Device orientation (which way is "down" due to gravity)
  - Motion and vibration
  - Tilt and shake gestures
- **3-axis Gyroscope**: Measures angular velocity (rotation rate) around X, Y, and Z axes. Units are degrees per second (°/s). Can detect:
  - Rotation speed and direction
  - Angular motion
  - Gesture recognition (twist, rotate)

**BMM150 Magnetometer**:
The BMM150 is a 3-axis geomagnetic sensor that measures:
- **Magnetic field strength**: In microteslas (µT) along X, Y, and Z axes
- **Earth's magnetic field**: Can determine compass heading (north, south, etc.)
- **Magnetic interference**: Detects nearby magnets or ferrous materials

**9-Axis Sensor Fusion**:
When combined, the BMI270 (6-axis) and BMM150 (3-axis) form a 9-axis sensor system capable of:
- **Absolute orientation**: Determining device orientation relative to Earth (not just relative motion)
- **Compass functionality**: Knowing which direction is north
- **Motion tracking**: Tracking device movement in 3D space
- **Gesture recognition**: Detecting complex gestures like rotation, shake, flip

**Data Format** (JSON):
```json
{
  "ax": 0.0,  // Accelerometer X (g) - linear acceleration
  "ay": 0.0,  // Accelerometer Y (g)
  "az": 0.0,  // Accelerometer Z (g) - typically ~1.0 when stationary (gravity)
  "gx": 0.0,  // Gyroscope X (deg/s) - angular velocity around X axis
  "gy": 0.0,  // Gyroscope Y (deg/s)
  "gz": 0.0,  // Gyroscope Z (deg/s)
  "mx": 0.0,  // Magnetometer X (uT) - magnetic field strength
  "my": 0.0,  // Magnetometer Y (uT)
  "mz": 0.0   // Magnetometer Z (uT) - note: X and Z are negated in firmware
}
```

**Coordinate System**: The firmware uses a right-handed coordinate system. The exact orientation depends on how the sensors are mounted on the board. The magnetometer data has X and Z axes negated (`magX = -magX, magZ = -magZ`) to correct for sensor mounting orientation.

**Update Rate**: 10Hz (100ms interval)

The 10Hz update rate is a balance between:
- **Responsiveness**: Fast enough for real-time applications like motion tracking
- **CPU load**: Higher rates consume more CPU for sensor reading and JSON encoding
- **Network bandwidth**: Each update is ~100 bytes, so 10Hz = ~1KB/s per client
- **Battery life**: Lower rates save power (though this device is USB-powered)

For applications requiring higher rates (e.g., gesture recognition), the update rate could be increased, but 10Hz is sufficient for most orientation and motion tracking applications.

**Implementation**:

**FreeRTOS Task**: The IMU data daemon runs as a separate FreeRTOS task (`imu_data_ws_daemon`), which:
- Runs independently of the main application loop
- Has its own stack space (4000 bytes)
- Runs at priority 5 (moderate priority)
- Continuously loops, sleeping 100ms between updates

**Data Reading**: The task calls `SharedData::UpdateImuData()`, which:
1. Checks if BMI270 sensor is initialized
2. Reads accelerometer data (3 axes) from BMI270
3. Reads gyroscope data (3 axes) from BMI270
4. Checks if BMM150 magnetometer is available
5. If available, reads magnetometer data (3 axes) from BMM150 via BMI270's auxiliary I2C interface
6. Applies coordinate system corrections (negates magX and magZ)

**WebSocket Broadcasting**: When clients are connected:
- JSON data is serialized using ArduinoJson library
- Data is sent to all connected WebSocket clients using `imu_data_ws->textAll()`
- If no clients are connected, sensor reading still occurs but no network transmission

**Client Management**: The WebSocket implementation includes:
- Connection tracking via mutex-protected flag (`is_imu_data_ws_connected`)
- Automatic client cleanup via `cleanup_imu_ws_client()` called from main loop
- Ping/pong support for connection health monitoring

**Use Cases**:
- **Motion-controlled camera**: Tilt device to pan camera view
- **Gesture recognition**: Detect shake, flip, or rotation gestures
- **Orientation tracking**: Determine device orientation for image rotation
- **Compass application**: Display compass heading
- **Motion logging**: Record motion data for analysis
- **Gaming**: Use device as motion controller

**Where to learn more**:
- BMI270 Datasheet: Available from Bosch Sensortec
- BMM150 Datasheet: Available from Bosch Sensortec
- Sensor Fusion Algorithms: https://en.wikipedia.org/wiki/Sensor_fusion
- WebSocket Protocol: https://tools.ietf.org/html/rfc6455

#### IR API (`api_ir.cpp`)

**Endpoint**:
- `POST /api/v1/ir_send` - Send NEC IR command

The IR API allows the device to function as a universal remote control, capable of sending commands to TVs, air conditioners, and other IR-controlled devices. This is useful for home automation, smart home integration, and remote control applications.

**Understanding Infrared Remote Control**:

Infrared (IR) remote controls work by:
1. **Modulating data**: Encoding command data onto a carrier frequency (38kHz for NEC protocol)
2. **Transmitting pulses**: Using an IR LED to transmit light pulses
3. **Receiving**: The target device has an IR receiver that demodulates the signal

**NEC Protocol**:
NEC is one of the most common IR protocols, used by many consumer electronics manufacturers. The protocol defines:

- **Carrier frequency**: 38kHz (38,000 pulses per second). This is the "carrier wave" that the data is modulated onto. The 38kHz frequency is chosen because:
  - It's high enough to avoid interference from ambient light
  - It's low enough for simple receivers to demodulate
  - It's a standard frequency supported by most IR receivers

- **Data encoding**: Uses pulse distance encoding:
  - **Logical 0**: 562.5µs pulse + 562.5µs space = 1125µs total
  - **Logical 1**: 562.5µs pulse + 1687.5µs space = 2250µs total
  - The longer space for "1" makes it distinguishable from "0"

- **Message structure**:
  - **Leader pulse**: 9ms pulse + 4.5ms space (marks start of message)
  - **Address**: 16 bits (device identifier, e.g., TV brand/model)
  - **Address complement**: 16 bits (inverted address for error checking)
  - **Command**: 16 bits (actual command, e.g., "power on", "volume up")
  - **Command complement**: 16 bits (inverted command for error checking)
  - **Stop bit**: 562.5µs pulse

- **Repeat codes**: If a button is held down, the device sends repeat codes (simpler message) instead of full messages to save bandwidth

**Request Format** (JSON):
```json
{
  "addr": 0x0000,  // NEC address (16-bit) - identifies target device
  "cmd": 0x0000     // NEC command (16-bit) - command to execute
}
```

**Address Field**: The 16-bit address identifies the target device. Different manufacturers and device types use different address ranges:
- **TV manufacturers**: Each brand typically uses a specific address range
- **Device type**: TVs, air conditioners, audio systems may use different addresses
- **Example**: A Samsung TV might use address `0x707`, while a Sony TV uses `0x1CE`

**Command Field**: The 16-bit command specifies the action:
- **Power**: Often `0x00` or `0x01` for power on/off
- **Volume**: `0x10` for volume up, `0x11` for volume down
- **Channel**: `0x20` for channel up, `0x21` for channel down
- **Numbers**: `0x00-0x09` for digits 0-9
- **Other**: Manufacturer-specific commands vary

**Finding IR Codes**: To control a specific device, you need to know its NEC address and command codes. These can be:
- **Learned**: Use an IR receiver to capture codes from the original remote
- **Databases**: Online databases like LIRC (Linux Infrared Remote Control) project
- **Trial and error**: Some devices use standard codes that can be discovered

**Response**: `{"msg":"ok"}`

The API returns a simple success message. Note that there's no way to verify if the IR command was actually received by the target device - IR is a one-way protocol with no acknowledgment.

**Implementation Details**:

**Hardware**: The IR transmitter uses:
- **GPIO 47**: Connected to IR LED driver circuit
- **LEDC (LED Controller)**: ESP32's hardware PWM peripheral generates the 38kHz carrier frequency
- **Timing**: Precise timing is critical for NEC protocol - FreeRTOS tasks provide sufficient timing accuracy

**IR Transmission Process**:
1. API receives JSON request with address and command
2. Validates JSON structure
3. Calls `SharedData::IrSendNecMsg(addr, cmd)`
4. Which calls `ir_nec_transceiver_send()` in the IR utility
5. IR encoder generates NEC protocol waveform
6. LEDC hardware modulates 38kHz carrier
7. IR LED transmits the signal

**Range and Limitations**:
- **Range**: Up to 12.46 meters without obstruction (per AtomS3R-M12 specifications)
- **Obstructions**: IR is line-of-sight - walls, furniture, etc. block the signal
- **Interference**: Bright sunlight or other IR sources can interfere
- **Angle**: 180° emission angle provides wide coverage

**Use Cases**:
- **Smart home control**: Integrate camera device with home automation
- **Universal remote**: Control multiple devices from web interface
- **Automation**: Schedule IR commands (e.g., turn on TV at specific time)
- **Accessibility**: Web-based remote control for users who can't use physical remotes

**Where to learn more**:
- NEC IR Protocol Specification: Available from NEC Corporation
- LIRC Project: http://www.lirc.org/ (IR code database)
- IR Remote Control Theory: https://www.sbprojects.net/knowledge/ir/nec.php
- ESP32 LEDC Documentation: https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/api-reference/peripherals/ledc.html

### 5. Shared Data Management (`main/utils/shared/`)

**Purpose**: Thread-safe singleton for sharing data between components

The SharedData system provides a centralized, thread-safe way for different components (UVC service, web server, main application) to share state and coordinate access to hardware resources. This is essential in a multi-threaded embedded system where multiple tasks need to access the same data structures.

**Pattern**: Dependency Injection + Singleton

The firmware uses two design patterns:

**Singleton Pattern**: Ensures only one instance of SharedData exists throughout the application lifetime. This provides:
- **Global access**: Any component can access shared data via `SharedData::GetData()`
- **Consistency**: All components see the same data
- **Resource efficiency**: Single instance reduces memory usage

**Dependency Injection**: The actual SharedData implementation is injected at startup rather than being hardcoded. This provides:
- **Testability**: Can inject mock implementations for testing
- **Flexibility**: Can use different implementations (with/without mutex, different locking strategies)
- **Loose coupling**: Components depend on the SharedData interface, not specific implementations

**Implementation Details**:

The firmware uses `SharedData_StdMutex` implementation, which provides:
- **std::mutex**: C++ standard library mutex for thread synchronization
- **RAII pattern**: Mutex is automatically locked/unlocked via `BorrowData()`/`ReturnData()`
- **Exception safety**: If code throws exception, mutex is still properly unlocked

**Key Features**:
- Mutex-based locking (`BorrowData()` / `ReturnData()`)
- Service mode management
- IMU data access
- IR command interface

**Thread Safety Model**:

The SharedData system uses a "borrow-return" pattern for thread-safe access:

```cpp
// Correct usage:
SharedData::BorrowData();  // Acquires mutex lock
// ... access or modify data ...
SharedData::ReturnData();  // Releases mutex lock

// Incorrect usage (will cause deadlock):
SharedData::BorrowData();
SharedData::BorrowData();  // Deadlock! Mutex already locked
```

**Why This Pattern**:
- **Explicit locking**: Makes it clear when data is being accessed
- **Prevents deadlocks**: Single mutex prevents complex deadlock scenarios
- **Performance**: Mutex is only held during actual data access
- **Error prevention**: RAII ensures mutex is always released

**Common Pitfalls**:
1. **Forgetting ReturnData()**: Causes deadlock - other threads wait forever
2. **Nested borrowing**: Calling BorrowData() twice causes deadlock
3. **Long-held locks**: Holding lock during slow operations (network I/O) blocks other threads
4. **Exception safety**: If code throws exception between BorrowData() and ReturnData(), mutex stays locked

**Data Structure** (`types.h`):
```cpp
struct SharedData_t {
    ServiceMode::ServiceMode_t service_mode;
    BMI270_Class* imu;
    bool is_bmm150_ok;
    IMU::ImuData_t imu_data;
};
```

**Service Modes**:
- `mode_none` - No active service
- `mode_uvc` - UVC streaming active
- `mode_web_server` - Web server streaming active

**Thread Safety**:
- `BorrowData()` - Acquires lock, returns reference
- `ReturnData()` - Releases lock
- Implementation: `SharedData_StdMutex` (from mooncake library)

**Helper Methods**:
- `GetServiceMode()` - Get current service mode
- `SetServiceMode()` - Set service mode
- `UpdateImuData()` - Read and update IMU data
- `GetImuData()` - Get IMU data (const reference)
- `IrSendNecMsg()` - Send IR NEC command

### 6. Camera Initialization (`main/utils/camera/`)

**Function**: `my_camera_init(xclk_freq_hz, pixel_format, frame_size, jpeg_quality, fb_count)`

**Features**:
- Idempotent initialization (skips if already configured)
- Dynamic reinitialization when parameters change
- Sensor-specific configuration
- PSRAM frame buffer allocation

**Camera Configuration**:
- Pixel format: JPEG (hardcoded)
- Frame size: Configurable (QVGA to FHD)
- JPEG quality: 6-16 (resolution-dependent)
- Frame buffer count: 1
- Grab mode: `CAMERA_GRAB_WHEN_EMPTY`
- Frame buffer location: PSRAM

**Supported Camera Modules**:
1. **ESP-S2-Kaluga-1 V1.3**
2. **ESP-S3-EYE DevKit** (with LCD animation support)
3. **ESP-S3-Korvo-2**
4. **M5Stack-AtomS3R-CAM** (default for ESP32-S3)
5. **Custom** (user-defined pins)

**Supported Camera Sensors** (from sdkconfig):
The ESP32-Camera driver supports a wide variety of camera sensors, each with different capabilities:

- **OV7670/OV7725**: Lower resolution VGA sensors (640x480), commonly used in older camera modules. These are basic sensors suitable for simple applications.
- **NT99141**: A 1.3-megapixel sensor capable of 1280x720 resolution, provides good quality for mid-range applications.
- **OV2640**: A popular 2-megapixel sensor (1600x1200) with built-in JPEG compression. Widely used in ESP32 camera projects due to good balance of quality and cost.
- **OV3660**: The 3-megapixel sensor used in AtomS3R-M12 (2048x1536). Features wide-angle lens (120° FOV) and good low-light performance. This is the primary sensor for this firmware.
- **OV5640**: A high-resolution 5-megapixel sensor (2592x1944), provides excellent image quality but requires more processing power.
- **GC2145/GC032A/GC0308**: GalaxyCore sensors offering good price/performance ratios. GC032A and GC0308 are lower resolution sensors suitable for cost-sensitive applications.
- **BF3005/BF20A6**: BYD Microelectronics sensors, less common but supported by the driver.
- **SC030IOT**: A sensor designed for IoT applications, optimized for low power consumption.

**Sensor-Specific Configuration**:
Each camera sensor has unique characteristics that require specific initialization settings:

- **OV3660** (AtomS3R-M12 default): 
  - Brightness set to +1 to compensate for slightly dim default output
  - Saturation reduced by -2 to prevent oversaturated colors
  - Vertical flip enabled to correct image orientation (sensor is mounted upside-down)
  - This sensor supports hardware JPEG compression, reducing CPU load

- **OV2640**: 
  - Only vertical flip is applied (no brightness/saturation adjustments needed)
  - Also supports hardware JPEG compression
  - Commonly used in ESP32-CAM modules

- **GC0308**: 
  - Horizontal mirror disabled (sensor outputs correct orientation)
  - Lower resolution sensor, suitable for basic applications

- **GC032A**: 
  - Vertical flip enabled for correct orientation
  - Similar to GC0308 but with different pinout

**Why Sensor-Specific Configuration Matters**:
Camera sensors have different:
- **Default orientations**: Some sensors are mounted rotated or flipped, requiring software correction
- **Color characteristics**: Different sensors have different color response curves, requiring brightness/saturation adjustments
- **Noise characteristics**: Some sensors produce more noise, requiring different processing
- **Capabilities**: Not all sensors support hardware JPEG compression; some require software encoding

The firmware detects the sensor type by reading the sensor's Product ID (PID) register and applies appropriate settings automatically.

**Pin Configuration** (M5Stack AtomS3R-CAM):
- XCLK: GPIO 15
- PCLK: GPIO 13
- VSYNC: GPIO 6
- HREF: GPIO 7
- SIOD (SCCB SDA): GPIO 4
- SIOC (SCCB SCL): GPIO 5
- D0-D7: GPIO 11, 9, 8, 10, 12, 18, 17, 16

### 7. Asset Pool System (`main/utils/assets/`)

**Purpose**: Store static assets (HTML, images) in flash memory

**Implementation**:
- Custom partition type: 233 (0x23)
- Partition size: 2MB
- Memory-mapped for zero-copy access
- Singleton pattern (`AssetPool`)

**Asset Structure**:
```cpp
struct StaticAsset_t {
    ImagePool_t Image;  // Contains HTML, images, etc.
};
```

**Assets Included**:
- `index_html_gz` - Compressed HTML (234,419 bytes)
- `m5.jpg` - Image asset
- Other image assets

**Partition Layout**:
- Partition name: `assetpool`
- Type: 233 (custom)
- Subtype: 0x23
- Size: 2MB
- Flash command: `parttool.py --port <port> write_partition --partition-name=assetpool --input asset_pool_gen/output/AssetPool.bin`

**Usage**:
- Injected at startup via `asset_pool_injection()`
- Web server serves HTML directly from memory-mapped partition
- No filesystem required

### 8. Hardware Abstraction Layer (`main/hal_config.h`)

**Pin Definitions**:

**Display** (SPI):
- MOSI: GPIO 21
- SCLK: GPIO 15
- DC: GPIO 42
- CS: GPIO 14
- RST: GPIO 48
- MISO: -1 (not used)
- BUSY: -1 (not used)
- Backlight: -1 (not used)

**I2C**:
- Internal bus: SDA=45, SCL=0
- External bus: SDA=2, SCL=1 (defined but not used)

**Buttons**:
- Button A: GPIO 8

**IMU**:
- Interrupt: GPIO 16 (hardware pulled up)

**IR**:
- Transmitter: GPIO 47

**Camera**:
- Power control: GPIO 18 (active high, pulled down)
- Other pins: Module-dependent (see `camera_pin.h`)

## Memory Layout

### Partition Table (`partitions.csv`)

```
# Name,     Type, SubType, Offset,   Size, Flags
nvs,           data, nvs,      0x9000,  0x6000,
factory,       0,    0,        0x10000, 2M
assetpool, 233, 0x23,    ,        2M,
```

**Partitions**:
1. **NVS** (Non-Volatile Storage)
   - Offset: 0x9000 (36KB)
   - Size: 24KB
   - Purpose: Configuration storage

2. **Factory** (Application)
   - Offset: 0x10000 (64KB)
   - Size: 2MB
   - Purpose: Main firmware

3. **Asset Pool** (Custom)
   - Type: 233 (custom)
   - Subtype: 0x23
   - Size: 2MB
   - Purpose: Static assets (HTML, images)

### Memory Usage

Understanding memory usage is critical for embedded systems development, as memory is limited and must be managed carefully.

**ESP32-S3 Memory Architecture**:

The ESP32-S3 has multiple memory types with different characteristics:

1. **Internal SRAM**: ~512KB total, divided into:
   - **IRAM (Instruction RAM)**: Stores executable code, must be in IRAM for code that runs during flash operations
   - **DRAM (Data RAM)**: Stores variables, stack, heap. Very fast access but limited capacity
   - **RTC Fast Memory**: Small amount of memory that persists during deep sleep

2. **PSRAM (Pseudo Static RAM)**: External memory chip on AtomS3R-M12:
   - **Size**: 8MB on AtomS3R-M12
   - **Speed**: Slower than internal SRAM but much larger capacity
   - **Use case**: Perfect for large buffers like camera frames
   - **Access**: Accessed via ESP32's SPI interface, cached for performance

3. **Flash Memory**: 8MB on AtomS3R-M12:
   - **Purpose**: Stores firmware code and data
   - **Partitions**: Divided into bootloader, application, NVS, asset pool
   - **Memory-mapped**: Can be accessed directly via memory mapping

**Frame Buffers**:
- **Location**: PSRAM (not internal SRAM)
- **Why PSRAM**: Camera frames are large (10KB-1MB per frame). Internal SRAM (~500KB total) cannot hold even a single high-resolution frame. PSRAM provides 8MB of space for multiple frames.
- **Count**: 1 (reduced from 2 to save memory)
- **Size**: Variable depending on resolution:
  - QVGA (320x240): ~10-20KB JPEG
  - VGA (640x480): ~30-60KB JPEG
  - HD (1280x720): ~80-150KB JPEG
  - FHD (1920x1080): ~150-300KB JPEG
- **Max size**: 1MB (ESP32-S3 limit for single allocation)
- **Allocation**: Done by ESP32-Camera driver using `CAMERA_FB_IN_PSRAM` flag
- **Performance**: PSRAM access is slower than SRAM but still fast enough for 30 FPS capture

**UVC Buffer**:
- **Size**: 1MB (ESP32-S3), 60KB (other targets like ESP32)
- **Location**: Heap (allocated via `malloc()`)
- **Purpose**: Temporary buffer for USB transmission. TinyUSB copies frame data from camera buffer to UVC buffer before sending over USB.
- **Why separate**: USB stack needs its own buffer for DMA transfers and protocol handling
- **Memory type**: Allocated from heap, which can be in PSRAM if configured

**Asset Pool**:
- **Size**: 2MB
- **Location**: Flash memory (memory-mapped)
- **Access method**: `esp_partition_mmap()` creates a memory-mapped view of flash partition
- **Advantages**:
  - Zero-copy access: Web server can serve files directly from flash without copying to RAM
  - Persistent: Data survives power cycles
  - Large capacity: 2MB for HTML, images, and other assets
- **Trade-off**: Flash is slower than RAM but acceptable for serving static files

**Memory Management Best Practices**:

1. **Use PSRAM for large buffers**: Camera frames, image processing buffers
2. **Use internal SRAM for small, frequently-accessed data**: Variables, small buffers, stack
3. **Avoid large stack allocations**: Use heap allocation for large local variables
4. **Monitor heap fragmentation**: Repeated allocation/deallocation can fragment heap
5. **Use memory-mapped flash for read-only data**: Reduces RAM usage

**Memory Constraints**:

- **Single frame buffer**: With only 1 frame buffer, the firmware must process and return frames quickly to avoid drops. If UVC or web server doesn't return the buffer fast enough, the next frame capture will fail.
- **PSRAM bandwidth**: PSRAM has limited bandwidth. If multiple components access PSRAM simultaneously, performance can degrade.
- **Heap fragmentation**: Over time, heap can become fragmented, making it difficult to allocate large contiguous blocks.

**Where to learn more**:
- ESP32-S3 Memory Layout: https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/api-guides/memory-types.html
- PSRAM Usage: https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/api-guides/external-ram.html
- Memory Mapping: https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/api-reference/storage/spi_flash.html

## Dependencies

### External Git Repositories (`repos.json`)

1. **mooncake** (v1.2)
   - M5Stack framework utilities
   - Provides SharedData mutex implementation

2. **arduino-esp32** (v3.0.2)
   - Arduino compatibility layer
   - Used for WiFi and web server

3. **ArduinoJson** (v7.0.4)
   - JSON parsing library
   - Used in API handlers

4. **esp32-camera** (v2.0.10)
   - Camera driver from Espressif
   - Core camera functionality

5. **M5GFX** (0.1.16)
   - Graphics library
   - Display support

6. **M5Unified** (0.1.16)
   - M5Stack unified API
   - Hardware abstraction

### ESP-IDF Managed Components

**Key Components**:
- **tinyusb** - USB stack (used by usb_device_uvc)
- **littlefs** - Filesystem (not actively used)
- **esp-dsp** - Signal processing
- **esp-sr** - Speech recognition (not used)
- **esp-rainmaker** - Cloud services (not used)
- **esp-modem** - Cellular modem (not used)

**Note**: Many managed components are included but not actively used in the firmware.

## Build and Flash Process

### Prerequisites

1. **ESP-IDF v5.1.4**
   - Install and set up ESP-IDF environment
   - Source `export.sh` or `export.bat`

2. **Python 3**
   - Required for ESP-IDF tools

3. **Git**
   - Required for fetching dependencies

### Build Steps

1. **Fetch Dependencies**:
   ```bash
   python ./fetch_repos.py
   ```
   - Clones external repositories into `components/`

2. **Configure** (optional):
   ```bash
   idf.py menuconfig
   ```
   - Configure camera module, UVC settings, etc.

3. **Build**:
   ```bash
   idf.py build
   ```
   - Compiles firmware
   - Generates binaries in `build/`

### Flash Process

1. **Flash Firmware**:
   ```bash
   idf.py -p <YourPort> flash -b 1500000
   ```
   - Flashes bootloader, partition table, and application
   - Baud rate: 1,500,000

2. **Flash Asset Pool** (separate step):
   ```bash
   parttool.py --port <YourPort> write_partition \
     --partition-name=assetpool \
     --input "asset_pool_gen/output/AssetPool.bin"
   ```
   - Flashes static assets to custom partition
   - Must be done after firmware flash

### Build Outputs

**Key Files**:
- `build/bootloader/bootloader.bin` - Bootloader
- `build/partition_table/partition-table.bin` - Partition table
- `build/usb_webcam.bin` - Application firmware
- `asset_pool_gen/output/AssetPool.bin` - Asset pool binary

## Usage Guide

### As USB Webcam

1. **Connect via USB**
   - Device appears as "ESP UVC Device" (VID: 0x303A, PID: 0x8000)

2. **Host Recognition**
   - Standard UVC drivers should recognize device
   - Available resolutions depend on UVC configuration

3. **Streaming**
   - Host requests resolution via UVC control
   - Firmware reconfigures camera dynamically
   - Frames sent via USB bulk/isochronous transfer

### As WiFi Webcam

1. **Connect to WiFi AP**
   - SSID: "AtomS3R-M12-WiFi"
   - No password (open network)
   - Channel: 1

2. **Access Web Interface**
   - Open browser to `http://192.168.4.1`
   - Web interface loads from asset pool

3. **Use APIs**:
   - **Capture**: `GET http://192.168.4.1/api/v1/capture`
   - **Stream**: `GET http://192.168.4.1/api/v1/stream`
   - **IMU Data**: `WS ws://192.168.4.1/api/v1/ws/imu_data`
   - **IR Control**: `POST http://192.168.4.1/api/v1/ir_send`

### Service Mode Behavior

**Important**: UVC and web server streaming cannot run simultaneously.

- **UVC Active**: Web server streaming returns `NULL` frames
- **Web Server Active**: UVC `fb_get_cb` returns `NULL` if web server mode detected
- **Mode Switching**: Automatic based on which service requests frames

## Configuration

### Kconfig Options (`main/Kconfig.projbuild`)

**Camera Configuration**:
- `CAMERA_XCLK_FREQ` - XCLK frequency (1-40MHz, default 20MHz)
- `CAMERA_MODULE` - Camera module selection
  - ESP-S2-Kaluga-1 V1.3
  - ESP-S3-EYE DevKit
  - ESP-S3-Korvo-2
  - M5Stack-AtomS3R-CAM (default)
  - Custom

**UVC Configuration** (via `sdkconfig`):
- `CONFIG_UVC_CAM1_FRAMESIZE_WIDTH/HEIGHT` - Default resolution
- `CONFIG_UVC_CAM1_FRAMERATE` - Frame rate
- `CONFIG_CAMERA_MULTI_FRAMESIZE` - Enable multi-resolution support
- `CONFIG_TUSB_VID/PID` - USB vendor/product IDs

### Runtime Configuration

**Camera Parameters** (via web API):
- Resolution, quality, brightness, contrast, saturation, etc.
- Auto white balance, auto gain control, auto exposure
- Mirror/flip options

**Service Mode** (automatic):
- Set by active service (UVC or web server)
- Prevents resource conflicts

## Troubleshooting

### Common Issues

**1. Camera Not Detected**

Symptoms: Camera initialization fails, no frames captured, I2C errors in logs.

**Diagnosis Steps**:
- **Check camera power**: Verify GPIO 18 is configured correctly and camera power LED is on
  - Look for log message: `"enable camera power"`
  - Measure GPIO 18 voltage (should be 3.3V when enabled)
  - Check if 200ms delay is sufficient for your camera module
- **Verify camera module selection**: Ensure `CONFIG_CAMERA_MODULE` matches your hardware
  - Check `sdkconfig` for `CONFIG_CAMERA_MODULE_M5STACK_ATOMS3R_CAM=y` (or your module)
  - Verify pin definitions in `main/utils/camera/camera_pin.h` match your hardware
- **Check I2C bus**: Camera uses SCCB (compatible with I2C) for configuration
  - Verify I2C pins: SDA=45, SCL=0 (for M5Stack AtomS3R-CAM)
  - Check I2C scan results in logs: `"start scan:"` should show camera device address
  - Common camera I2C addresses: 0x30 (OV3660), 0x60 (OV2640)
- **Check sensor support**: Verify your camera sensor is enabled in `sdkconfig`
  - Look for `CONFIG_OV3660_SUPPORT=y` (or your sensor)
  - Some sensors require specific configuration options

**Where to look**: `main/usb_webcam_main.cpp` (camera_init function), `main/utils/camera/camera_init.c`, serial monitor logs

**2. UVC Not Working**

Symptoms: Device not recognized by host, no video stream, USB enumeration fails.

**Diagnosis Steps**:
- **Verify USB connection**: Check physical USB cable and port
  - Try different USB cable (some cables are power-only)
  - Try different USB port on host computer
  - Check if device appears in system USB device list (`lsusb` on Linux)
- **Check USB VID/PID**: Verify device appears with correct identifiers
  - Expected: VID=0x303A, PID=0x8000
  - Check `sdkconfig` for `CONFIG_TUSB_VID` and `CONFIG_TUSB_PID`
- **Host driver support**: Verify host OS has UVC driver
  - Windows: Should work automatically (built-in driver)
  - Linux: Requires `uvcvideo` kernel module (`modprobe uvcvideo`)
  - macOS: Should work automatically
- **Review UVC frame configuration**: Check if requested resolution is supported
  - Look at UVC descriptor in `components/usb_device_uvc/tusb/uvc_frame_config.h`
  - Verify `UVC_FRAMES_INFO` array includes requested resolution
  - Check logs for: `"Format: X, width: Y, height: Z, rate: W"`
- **Check service mode**: Ensure web server is not streaming (service mode conflict)
  - Look for log: `"web server is streaming"` in UVC callback
  - Stop any web browser connections to `/api/v1/stream`

**Where to look**: `main/service/service_uvc.cpp`, `components/usb_device_uvc/`, host system USB logs, serial monitor

**3. Web Server Not Accessible**

Symptoms: Cannot connect to WiFi AP, cannot access web interface, connection timeout.

**Diagnosis Steps**:
- **Verify WiFi AP creation**: Check if Access Point is started
  - Look for log: `"ap ip: 192.168.4.1"` (or similar)
  - Check WiFi AP appears in device's WiFi scan
- **Check SSID**: Verify SSID matches expected value
  - Expected: "AtomS3R-M12-WiFi"
  - Check `main/service/service_web_server.cpp` for SSID definition
- **Client connection**: Ensure client device is connected to AP
  - Check WiFi connection status on client device
  - Verify client received IP address (should be 192.168.4.x)
  - Check if client can ping 192.168.4.1
- **Max connections**: AP is configured for 1 client maximum
  - Disconnect other devices before connecting
  - Check `WiFi.softAP()` call in `service_web_server.cpp`
- **Port and firewall**: Verify HTTP port 80 is accessible
  - Check firewall settings on client device
  - Try accessing `http://192.168.4.1` (not https)
- **Asset pool**: Verify asset pool is loaded (web interface won't load without it)
  - Look for log: `"asset pool maped at: <address>"`
  - If missing, flash asset pool partition

**Where to look**: `main/service/service_web_server.cpp`, client device WiFi settings, serial monitor logs

**4. Asset Pool Missing**

Symptoms: Web interface doesn't load, 404 errors, blank page.

**Diagnosis Steps**:
- **Check partition table**: Verify assetpool partition exists
  - Review `partitions.csv` for `assetpool` entry
  - Verify partition type 233, subtype 0x23
  - Check partition size (should be 2MB)
- **Flash asset pool**: Asset pool must be flashed separately from firmware
  - Run: `parttool.py --port <port> write_partition --partition-name=assetpool --input asset_pool_gen/output/AssetPool.bin`
  - Verify binary file exists: `asset_pool_gen/output/AssetPool.bin`
  - Check file size matches partition size
- **Verify mapping**: Check if asset pool is memory-mapped at startup
  - Look for log: `"asset pool maped at: <address>"`
  - If error: `"asset pool partition not found!"` - partition not flashed
  - If error: `"map asset pool failed!"` - flash corruption or wrong partition
- **Rebuild asset pool**: If binary is missing or corrupted
  - Check `asset_pool_gen/` directory for build scripts
  - Rebuild asset pool binary if needed

**Where to look**: `main/usb_webcam_main.cpp` (asset_pool_injection function), `partitions.csv`, serial monitor logs

**5. Service Mode Conflicts**

Symptoms: One service works but not both, frames return NULL, streaming stops unexpectedly.

**Diagnosis Steps**:
- **Understand limitation**: Only one service can stream at a time by design
  - UVC and web server both need exclusive camera access
  - Service mode prevents simultaneous access
- **Check active service**: Determine which service is currently active
  - UVC active: Web server `/api/v1/stream` returns NULL frames
  - Web server active: UVC `camera_fb_get_cb()` returns NULL
  - Look for log: `"web server is streaming"` in UVC callback
- **Stop conflicting service**: Before using other service
  - Stop web browser stream (close tab with `/api/v1/stream`)
  - Disconnect USB (stops UVC stream)
  - Wait for service mode to reset to `mode_none`
- **Verify service mode reset**: Check mode returns to `mode_none` after stream stops
  - UVC: `camera_stop_cb()` should reset mode
  - Web server: `~AsyncJpegStreamResponse()` destructor resets mode
  - Look for mode changes in logs

**Where to look**: `main/service/service_uvc.cpp`, `main/service/apis/api_camera.cpp`, `main/utils/shared/shared.h`

**6. IMU Not Working**

Symptoms: No IMU data, WebSocket disconnects, sensor initialization fails.

**Diagnosis Steps**:
- **Check sensor initialization**: Verify BMI270 and BMM150 are detected
  - Look for logs: `"bmi270 init ok"` and `"bmm150 init ok"`
  - If `"bmi270 init failed"` - check I2C connection (SDA=45, SCL=0)
  - If `"bmm150 init failed"` - sensor may not be present or I2C issue
- **I2C bus**: Verify I2C communication
  - Check I2C scan results in logs
  - BMI270 typically at address 0x68 or 0x69
  - BMM150 accessed via BMI270's auxiliary I2C interface
- **WebSocket connection**: Verify client can connect
  - Check WebSocket URL: `ws://192.168.4.1/api/v1/ws/imu_data`
  - Verify client JavaScript code is correct
  - Check browser console for WebSocket errors
- **Data update rate**: Verify daemon task is running
  - Check FreeRTOS task list (if debugger available)
  - Verify task is sending data (check network traffic)
  - Default update rate is 10Hz (100ms interval)

**Where to look**: `main/usb_webcam_main.cpp` (imu_init function), `main/service/apis/api_imu.cpp`, serial monitor logs

### Debugging

**Logging System**:

The firmware uses a dual logging system:

**Application Logging (spdlog)**:
- **Library**: spdlog - Fast C++ logging library
- **Pattern**: `[HH:MM:SS] [L] message` where L is log level (I=info, E=error, W=warn)
- **Usage**: Application-level messages, service status, initialization results
- **Example**: `[12:34:56] [I] camera init ok`

**ESP-IDF Logging**:
- **System**: ESP-IDF's built-in logging (`ESP_LOGI`, `ESP_LOGE`, etc.)
- **Usage**: Low-level driver messages, hardware initialization, system events
- **Tag**: Each component has a tag (e.g., "usb_webcam", "cam_init")
- **Example**: `I (12345) usb_webcam: Camera Start`

**Enabling Debug Logs**:
- Set log level in `sdkconfig`: `CONFIG_LOG_DEFAULT_LEVEL_DEBUG`
- Or use `idf.py menuconfig` → Component config → Log output → Default log verbosity

**Key Log Messages to Monitor**:

**Startup Sequence**:
- `"SharedData injected"` - Dependency injection successful
- `"asset pool maped at: <address>"` - Asset pool loaded
- `"enable camera power"` - Camera power enabled
- `"bmi270 init ok"` / `"bmm150 init ok"` - Sensors initialized
- `"camera init ok"` - Camera ready
- `"Service uvc started"` / `"Service web server started"` - Services running

**Runtime Monitoring**:
- `"Camera Start"` / `"Camera Stop"` - UVC streaming state
- `"web server is streaming"` - Service mode conflict warning
- `"Capture failed"` - Camera frame capture error
- `"Frame size X is larger than max frame size Y"` - Frame too large for buffer

**Where to Find Logs**:
- **Serial monitor**: `idf.py monitor` or `screen /dev/ttyUSB0 115200`
- **Log files**: Check `build/log/` directory for build-time logs
- **Host system**: USB device logs (Linux: `dmesg`, Windows: Device Manager)

**Debugging Tools**:

**Serial Monitor**:
- **Command**: `idf.py monitor` or `idf.py -p <port> monitor`
- **Baud rate**: Usually 115200 (check `sdkconfig`)
- **Features**: Log viewing, GDB debugging, reset device

**GDB Debugger**:
- **Setup**: Requires OpenOCD and GDB
- **Usage**: `idf.py openocd` (separate terminal) then `idf.py gdb`
- **Benefits**: Breakpoints, variable inspection, stack traces

**Heap Monitoring**:
- **Command**: Call `heap_caps_get_free_size()` to check free memory
- **Useful for**: Detecting memory leaks, fragmentation issues

**Task Monitoring**:
- **FreeRTOS**: Use `vTaskList()` to see all running tasks and their stack usage
- **Helpful for**: Identifying task starvation, stack overflow

**Where to learn more**:
- ESP-IDF Logging: https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/api-reference/system/log.html
- GDB Debugging: https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/api-guides/tools/idf-monitor.html
- FreeRTOS Debugging: https://www.freertos.org/a00017.html

## Limitations and Constraints

1. **Single Stream**: UVC and web server cannot stream simultaneously
2. **WiFi AP Only**: No station mode (cannot join existing network)
3. **Single Client**: WiFi AP supports only 1 client
4. **Frame Buffer**: Limited to 1 buffer (may cause frame drops)
5. **Asset Pool**: Must be flashed separately from firmware
6. **Camera Module**: Must match hardware (compile-time selection)

## Future Enhancements

**Potential Improvements**:
1. Dual streaming support (UVC + web server)
2. WiFi station mode support
3. Multiple WiFi clients
4. Increased frame buffer count
5. Integrated asset pool flashing
6. Runtime camera module detection
7. OTA update support
8. Cloud connectivity (ESP RainMaker)

## References

### Key Files

**Main Application**:
- `main/usb_webcam_main.cpp` - Entry point
- `main/hal_config.h` - Pin definitions

**Services**:
- `main/service/service_uvc.cpp` - UVC implementation
- `main/service/service_web_server.cpp` - Web server

**APIs**:
- `main/service/apis/api_camera.cpp` - Camera API
- `main/service/apis/api_imu.cpp` - IMU API
- `main/service/apis/api_ir.cpp` - IR API

**Core Utilities**:
- `main/utils/shared/shared.h` - SharedData class
- `main/utils/camera/camera_init.c` - Camera initialization
- `main/utils/assets/assets.h` - Asset pool

**Configuration**:
- `partitions.csv` - Partition table
- `sdkconfig` - ESP-IDF configuration
- `main/Kconfig.projbuild` - Project Kconfig

### External Documentation

- [ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/)
- [ESP32-Camera Documentation](https://github.com/espressif/esp32-camera)
- [USB Video Class Specification](https://www.usb.org/document-library/video-class-v15-document-set)
- [TinyUSB Documentation](https://docs.tinyusb.org/)

## Conclusion

The AtomS3R-M12 firmware is a well-structured ESP32-S3 based USB webcam implementation with dual-mode operation (UVC and WiFi web server). It demonstrates effective use of ESP-IDF, Arduino compatibility layer, and M5Stack libraries. The architecture uses dependency injection, singleton patterns, and service mode management to coordinate resources. The firmware supports multiple camera modules, provides comprehensive APIs, and includes sensor integration (IMU, magnetometer, IR).

Key strengths:
- Clean separation of concerns
- Thread-safe state management
- Flexible camera module support
- Comprehensive web API

Areas for improvement:
- Simultaneous streaming support
- WiFi station mode
- Multiple client support
- Integrated asset flashing

## Getting Started for New Developers

If you're new to this firmware project, this section provides a roadmap for understanding the codebase and getting started with development.

### Prerequisites

Before diving into the code, ensure you have:

1. **ESP-IDF v5.1.4 installed and configured**
   - Follow official installation guide: https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/get-started/
   - Verify installation: `idf.py --version`
   - Set up environment: Source `export.sh` (Linux/Mac) or `export.bat` (Windows)

2. **Hardware understanding**
   - Familiarize yourself with ESP32-S3 architecture and capabilities
   - Understand embedded systems concepts (GPIO, I2C, SPI, interrupts)
   - Basic knowledge of USB protocols (helpful but not required)

3. **Development tools**
   - Serial monitor: `idf.py monitor` or `screen`/`minicom`
   - Text editor or IDE with C/C++ support
   - Git for version control
   - Python 3 for build scripts

### Recommended Reading Order

**1. Start with the Main Entry Point** (`main/usb_webcam_main.cpp`)

This file shows the complete initialization sequence and gives you an overview of all components:
- Read `app_main()` function to understand startup flow
- Follow each initialization function to see what hardware is set up
- Note the dependency injection pattern for SharedData and AssetPool
- **Time investment**: 30-60 minutes
- **Key concepts**: Initialization order, dependency injection, hardware setup

**2. Understand Shared Data Management** (`main/utils/shared/`)

The SharedData system is central to how components communicate:
- Read `shared.h` to understand the interface
- Study `shared.cpp` to see the implementation
- Understand the BorrowData/ReturnData pattern for thread safety
- **Time investment**: 1-2 hours
- **Key concepts**: Singleton pattern, mutex locking, thread safety

**3. Explore Camera Initialization** (`main/utils/camera/`)

Camera is the core functionality:
- Read `camera_init.c` to understand camera setup
- Study `camera_pin.h` to see pin configurations for different modules
- Understand how camera reinitialization works
- **Time investment**: 1-2 hours
- **Key concepts**: Hardware initialization, dynamic reconfiguration, sensor-specific settings

**4. Study Service Implementations** (`main/service/`)

Services provide the main functionality:
- **UVC Service** (`service_uvc.cpp`): Understand callback architecture, frame buffer management
- **Web Server** (`service_web_server.cpp`): See how WiFi AP and HTTP server are set up
- **APIs** (`apis/`): Review REST API and WebSocket implementations
- **Time investment**: 2-3 hours
- **Key concepts**: USB Video Class, HTTP/WebSocket protocols, service coordination

**5. Review Configuration Files**

Understanding configuration is crucial:
- `partitions.csv`: Memory layout and partition structure
- `sdkconfig`: ESP-IDF configuration (camera support, USB settings, etc.)
- `main/Kconfig.projbuild`: Project-specific configuration options
- **Time investment**: 30-60 minutes
- **Key concepts**: Partition tables, Kconfig system, build configuration

### Key Files to Understand

**Critical Files** (must understand):
1. `main/usb_webcam_main.cpp` - Entry point and initialization
2. `main/utils/shared/shared.h` - Shared data interface
3. `main/service/service_uvc.cpp` - UVC implementation
4. `main/utils/camera/camera_init.c` - Camera initialization

**Important Files** (should understand):
1. `main/service/service_web_server.cpp` - Web server
2. `main/service/apis/api_camera.cpp` - Camera API
3. `main/utils/camera/camera_pin.h` - Pin configurations
4. `partitions.csv` - Memory layout

**Reference Files** (consult when needed):
1. `main/hal_config.h` - Pin definitions
2. `main/service/apis/api_imu.cpp` - IMU API
3. `main/service/apis/api_ir.cpp` - IR API
4. `components/usb_device_uvc/` - UVC component implementation

### Common Development Tasks

**Adding a New API Endpoint**:
1. Add handler function in appropriate `api_*.cpp` file
2. Register handler in `load_*_apis()` function
3. Test via web browser or `curl`
4. **See**: `main/service/apis/api_camera.cpp` for examples

**Modifying Camera Behavior**:
1. Edit `main/utils/camera/camera_init.c` for initialization changes
2. Modify `main/service/service_uvc.cpp` for UVC-specific behavior
3. Check `main/utils/camera/camera_pin.h` for pin changes
4. **See**: Camera initialization section in this document

**Adding Sensor Support**:
1. Initialize sensor in `main/usb_webcam_main.cpp`
2. Add data structure to `main/utils/shared/types.h`
3. Add access methods to `main/utils/shared/shared.h`
4. Create API endpoint if needed
5. **See**: IMU initialization in `main/usb_webcam_main.cpp` for example

**Debugging Issues**:
1. Enable debug logging in `sdkconfig`
2. Use `idf.py monitor` to view serial output
3. Check relevant service file for error handling
4. Review troubleshooting section in this document
5. **See**: Debugging section above

### Development Workflow

**1. Set Up Development Environment**:
```bash
# Install ESP-IDF v5.1.4
# Clone repository
git clone <repo-url>
cd ATOMS3R-CAM-M12-UserDemo

# Fetch dependencies
python ./fetch_repos.py

# Configure (optional)
idf.py menuconfig

# Build
idf.py build

# Flash
idf.py -p /dev/ttyUSB0 flash

# Monitor
idf.py monitor
```

**2. Make Changes**:
- Edit source files
- Rebuild: `idf.py build`
- Flash: `idf.py -p <port> flash`
- Test and verify

**3. Debug**:
- Use serial monitor: `idf.py monitor`
- Add log statements: `spdlog::info("debug message")`
- Use GDB if needed: `idf.py gdb`

### Where to Get Help

**Official Documentation**:
- ESP-IDF Programming Guide: https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/
- ESP32-Camera: https://github.com/espressif/esp32-camera
- TinyUSB: https://docs.tinyusb.org/

**Community Resources**:
- ESP32 Forum: https://www.esp32.com/
- M5Stack Community: https://community.m5stack.com/
- GitHub Issues: Check repository issues for known problems

**Code References**:
- This analysis document: Comprehensive overview
- Diary document: Step-by-step research notes
- Source code comments: Inline documentation
- ESP-IDF examples: `/path/to/esp-idf/examples/`

### Next Steps

After understanding the basics:

1. **Experiment**: Try modifying camera settings, adding log statements, changing update rates
2. **Extend**: Add new features (e.g., new API endpoints, sensor support)
3. **Optimize**: Improve performance (e.g., increase frame rate, reduce latency)
4. **Debug**: Fix issues you encounter, contribute fixes back

Remember: Embedded development requires patience. Take time to understand each component before moving to the next. Use the serial monitor extensively - it's your best friend for debugging.
