# AtomS3R-M12 User Demo

ESP32-S3 based USB webcam firmware for the M5Stack AtomS3R-M12 development board. Provides dual-mode operation as a standard USB Video Class (UVC) device and a WiFi-based web server for camera control and streaming.

## Features

- **USB Webcam Mode**: Plug-and-play UVC device compatible with Windows, Linux, and macOS
- **WiFi Web Server**: Access camera via web interface at `http://192.168.4.1`
- **Camera Support**: OV3660 sensor (3MP, 2048x1536) with dynamic resolution switching
- **IMU Integration**: BMI270 accelerometer/gyroscope + BMM150 magnetometer with WebSocket API
- **IR Transmitter**: NEC protocol IR remote control support
- **Multiple Resolutions**: QVGA to FHD (320x240 to 1920x1080)

## Hardware Requirements

- **M5Stack AtomS3R-M12** development board
- **ESP32-S3** SoC (dual-core, 240MHz)
- **8MB PSRAM** (for camera frame buffers)
- **8MB Flash** (for firmware and assets)
- **M5Stack AtomS3R-CAM** camera module (OV3660 sensor)

## Quick Start

### Prerequisites

- **ESP-IDF v5.1.x**: Install ESP-IDF following the [official installation guide](https://docs.espressif.com/projects/esp-idf/en/v5.1.6/esp32/get-started/index.html)
  - After installation, source the ESP-IDF environment in each terminal session:
    ```bash
    source ~/esp/esp-idf/export.sh
    ```
    (Adjust the path if ESP-IDF is installed in a different location)
- Python 3
- Git

### Build

1. **Fetch Dependencies**:

   The project uses a mix of Git submodules and vendored components:
   - **Submodules**: `mooncake`, `arduino-esp32`, `ArduinoJson`, `esp32-camera`, `M5GFX`, `M5Unified`
   - **Vendored**: `AsyncTCP`, `ESPAsyncWebServer`, `usb_device_uvc` (included in repository)
   - **Managed**: ESP-IDF component manager handles `managed_components/` automatically
   
   Initialize and update Git submodules:
   ```bash
   git submodule update --init --recursive
   ```
   
   Or clone the repository with submodules:
   ```bash
   git clone --recursive <repository-url>
   ```
   
   Alternatively, use the fetch script:
   ```bash
   python ./fetch_repos.py
   ```

2. **Build Firmware**:
   ```bash
   idf.py build
   ```

3. **Flash Firmware**:
   ```bash
   idf.py -p <YourPort> flash -b 1500000
   ```

4. **Flash Asset Pool** (required for web interface):
   ```bash
   parttool.py --port <YourPort> write_partition \
     --partition-name=assetpool \
     --input "asset_pool_gen/output/AssetPool.bin"
   ```

### Usage

#### USB Webcam Mode

1. Connect device via USB Type-C
2. Device appears as "ESP UVC Device" (VID: 0x303A, PID: 0x8000)
3. Use with any application that supports webcams (video conferencing, image capture, etc.)
4. Resolution is dynamically configured based on host application requirements

#### WiFi Web Server Mode

1. Connect to WiFi Access Point:
   - SSID: `AtomS3R-M12-WiFi`
   - Password: None (open network)
   - Channel: 1

2. Open web browser: `http://192.168.4.1`

3. **Available APIs**:
   - `GET /api/v1/capture` - Single JPEG capture
   - `GET /api/v1/stream` - MJPEG video stream
   - `WS /api/v1/ws/imu_data` - Real-time IMU data (WebSocket)
   - `POST /api/v1/ir_send` - Send NEC IR command

**Note**: UVC and web server streaming cannot run simultaneously. Only one service can access the camera at a time.

## Development

### Cursor/IDE Setup

For Cursor C/C++ symbol resolution with ESP-IDF (clangd + ESP-clang), see:

- [clangd Setup for Cursor](ttmp/2025/12/18/001-INITIAL-RECON--initial-firmware-reconnaissance-and-analysis/playbooks/01-clangd-setup-for-cursor.md)

### Configuration

- Camera module selection: `idf.py menuconfig` → Component config → Camera Configuration
- UVC settings: Edit `sdkconfig` or use `menuconfig`
- Partition table: `partitions.csv`

**Note**: The `dependencies.lock` and `sdkconfig` files are important for reproducible builds. Do not ignore these files in version control - they ensure component versions match across different environments.

### Monitoring

View serial output:
```bash
idf.py monitor
```

## Architecture

The firmware uses ESP-IDF v5.1.x with Arduino compatibility layer for web server functionality. Key components:

- **UVC Service**: TinyUSB-based USB Video Class implementation
- **Web Server**: ESPAsyncWebServer with WiFi AP mode
- **Camera Driver**: ESP32-Camera library with PSRAM frame buffers
- **Shared Data**: Thread-safe singleton for inter-component communication
- **Asset Pool**: Memory-mapped flash partition for web assets

## Documentation

For detailed architecture analysis, component descriptions, and troubleshooting:

- [Firmware Architecture Analysis](ttmp/2025/12/18/001-INITIAL-RECON--initial-firmware-reconnaissance-and-analysis/analysis/01-firmware-architecture-and-functionality-analysis.md)

## License

See repository license file.
