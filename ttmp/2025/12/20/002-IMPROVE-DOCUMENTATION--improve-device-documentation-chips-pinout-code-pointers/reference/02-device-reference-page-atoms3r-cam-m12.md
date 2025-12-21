---
Title: Device reference page (ATOMS3R-CAM-M12)
Ticket: 002-IMPROVE-DOCUMENTATION
Status: active
Topics:
    - documentation
    - hardware
    - pinout
    - esp32s3
    - camera
    - sensors
DocType: reference
Intent: long-term
Owners: []
RelatedFiles: []
ExternalSources: []
Summary: ""
LastUpdated: 2025-12-20T10:56:34.488448606-05:00
WhatFor: ""
WhenToUse: ""
---

# Device reference page (ATOMS3R-CAM-M12)

## Goal

Track the creation of the canonical repo-local device reference page (chips, pinout, buses, and code pointers) and provide a short index to the most important places to look.

## Context

The **canonical reference page** for the device lives at:

- `doc/atoms3r-cam-m12-device-reference.md`

This docmgr document exists so the ticket has a stable, searchable entrypoint and can relate files + capture diary/changelog for future work.

## Quick Reference

### Where to start in code

- **Bring-up sequence:** `main/usb_webcam_main.cpp`
- **Pin constants:** `main/hal_config.h`
- **Camera pin map (selected via sdkconfig):** `main/utils/camera/camera_pin.h`
- **Camera init wrapper:** `main/utils/camera/camera_init.c`
- **IMU + mag drivers:** `main/utils/bmi270/src/bmi270.{h,cpp}` (+ vendored Bosch Sensor APIs under `main/utils/bmi270/src/utilities/`)
- **IR transmitter (NEC over RMT):** `main/utils/ir_nec_transceiver/*`
- **Web/USB services that exercise the hardware:**
  - `main/service/service_uvc.cpp` (UVC)
  - `main/service/service_web_server.cpp` + `main/service/apis/api_*.cpp` (HTTP/websocket APIs)

## Usage Examples

### Find the exact pin mapping this firmware uses

- Internal/external I2C + IR: open `main/hal_config.h`
- Camera pins (DVP/SCCB): open `main/utils/camera/camera_pin.h` and confirm `CONFIG_CAMERA_MODULE_M5STACK_ATOMS3R_CAM=y` in `sdkconfig`

## Related

- Diary: `reference/01-diary.md`
- Ticket index: `index.md`
- Canonical device reference page: `doc/atoms3r-cam-m12-device-reference.md`
