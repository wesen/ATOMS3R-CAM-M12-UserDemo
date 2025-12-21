---
Title: Diary
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
LastUpdated: 2025-12-20T10:56:34.375638372-05:00
WhatFor: ""
WhenToUse: ""
---

# Diary

## Goal

Keep a step-by-step diary while creating a complete “device reference” documentation page for the ATOMS3R-CAM-M12 firmware repo (chips, pinout, buses, and code pointers).

## Step 1: Create the ticket workspace + seed docs

This step set up the `docmgr` ticket workspace so the work is tracked, searchable, and linked to code. I also created the top-level `doc/` directory since the request wants the final device reference page to live there.

### What I did
- Created `doc/` at the repo root.
- Created ticket `002-IMPROVE-DOCUMENTATION`.
- Added two reference docs: `Diary` and `Device reference page (ATOMS3R-CAM-M12)`.

### Why
- We want a long-lived, discoverable documentation artifact (device reference) plus a diary of the implementation journey.

### What worked
- `docmgr` is installed and the repo already has `.ttmp.yaml` + vocabulary, so the workflow is ready to use.

### What didn't work
- N/A

### What I learned
- This repo already has an existing docmgr knowledge base (`ttmp/`) so we can link the new reference doc cleanly without inventing structure.

### What was tricky to build
- N/A

### What warrants a second pair of eyes
- N/A

### What should be done in the future
- N/A

### Code review instructions
- N/A (doc scaffolding only)

---

## Step 2: Identify hardware initialization entrypoints in firmware

This step focused on finding where the firmware configures the major peripherals (camera, IMU, magnetometer, IR) so the reference page can link directly to the authoritative initialization code.

### What I did
- Read `main/usb_webcam_main.cpp` and noted the startup sequence and helper init functions.

### Why
- The device reference page needs “code pointers” that answer: “where is this chip configured?” and “which API/component is used?”.

### What worked
- Found a single, clear bring-up sequence:
  - I2C bus init via `m5::In_I2C.begin(...)`
  - IMU init via `BMI270_Class::init()` and `BMI270_Class::initAuxBmm150()`
  - IR init via `ir_nec_transceiver_init(...)`
  - Camera init via `my_camera_init(...)`

### What didn't work
- N/A

### What I learned
- **Great**: this repo has consolidated initialization in `app_main()` so our documentation can link to one place for “where does the hardware come up?”

### What was tricky to build
- Pin numbers are abstracted behind `hal_config.h` constants, so we need to follow those definitions to map to the physical pinout table.

### What warrants a second pair of eyes
- Confirm `enable_camera_power()`’s GPIO18 logic matches the schematic expectation (`POWER_N` is typically active-low); the function currently configures the pin but does not explicitly set its level.

### What should be done in the future
- Once we map all pins, consider adding a small comment or assert in code to document active-low semantics for camera power (documentation-only follow-up; no functional change required).

### Code review instructions
- Start at `main/usb_webcam_main.cpp` `app_main()` and follow calls to `i2c_init()`, `imu_init()`, `ir_init()`, and `camera_init()`.

---

## Step 3: Map firmware pin constants to the published pinout tables

This step turned “mystery constants” into an explicit, copy/paste-able pinout mapping. The key idea is that the firmware has *two* authoritative sources for pins: `main/hal_config.h` for general board pins (I2C, IR, etc.) and `main/utils/camera/camera_pin.h` for camera pins selected by `sdkconfig`.

### What I did
- Extracted the I2C/IR pin constants from `main/hal_config.h`.
- Verified the camera DVP/SCCB mapping for `CONFIG_CAMERA_MODULE_M5STACK_ATOMS3R_CAM` in `main/utils/camera/camera_pin.h`.
- Confirmed the camera module selection and XCLK frequency in `sdkconfig`.

### Why
- The requested device reference page needs to state the pinout unambiguously, plus show where those pins come from in code.

### What worked
- Pins match the provided tables cleanly:
  - Internal I2C: SDA=GPIO45, SCL=GPIO0
  - IR TX: GPIO47
  - HY2.0-4P PORT.CUSTOM exposes external I2C: SDA=GPIO2, SCL=GPIO1
  - Camera pins are defined exactly for the AtomS3R-CAM module selection.

### What didn't work
- N/A

### What I learned
- Camera pin selection is **compile-time** via `sdkconfig` (`CONFIG_CAMERA_MODULE_M5STACK_ATOMS3R_CAM=y`) rather than hard-coded in the app.

### What was tricky to build
- The camera power pin (`POWER_N`) is not part of the `camera_pin.h` mapping; it’s controlled separately in `enable_camera_power()` (GPIO18).

### What warrants a second pair of eyes
- Confirm whether `enable_camera_power()` needs an explicit `gpio_set_level(GPIO18, 0/1)` for clarity (it currently configures direction/pull but doesn’t set level).

### What should be done in the future
- If future boards differ, document the exact `sdkconfig` deltas (camera module selection + pins) in the reference page.

### Code review instructions
- Compare:
  - `main/hal_config.h` (I2C + IR + PORT.CUSTOM)
  - `main/utils/camera/camera_pin.h` (camera DVP/SCCB pins)
  - `sdkconfig` (camera module selection + XCLK freq)

---

## Step 4: Flesh out the reference document with comprehensive explanations

This step transformed the reference from a "quick lookup table" into a comprehensive, human-friendly guide with full paragraphs explaining concepts, detailed API usage, bus topology diagrams, and troubleshooting tips.

### What I did
- Rewrote the entire document with expanded sections:
  - **Overview**: Context about what the device is and its purpose
  - **Hardware Components**: Detailed explanations of each chip (ESP32-S3, BMI270, BMM150, OV3660, IR, PORT.CUSTOM) with features, connection methods, and why they matter
  - **Bus Topology**: ASCII diagram showing how all buses connect
  - **Complete Pinout**: Expanded tables with direction, notes, and code constants
  - **Initialization Sequence**: Step-by-step walkthrough of the startup sequence with code locations
  - **API Reference**: Practical code examples for IMU, camera, and IR APIs
  - **Troubleshooting Tips**: Common issues and debugging guidance
- Added prose explanations throughout (not just bullet points)
- Included ASCII diagrams for bus topology
- Added code examples showing actual usage patterns
- Expanded pinout tables with direction, constants, and usage notes

### Why
- The user requested a more "human-friendly" document with full paragraphs, bullet lists, and diagrams
- A comprehensive reference helps developers understand *why* things are connected the way they are, not just *what* pins are used
- Detailed explanations reduce the learning curve for new developers

### What worked
- The expanded format makes the document much more approachable—readers can understand the architecture before diving into pin numbers
- Bus topology diagram clarifies the two-level I2C hierarchy (BMM150 behind BMI270)
- Code examples provide copy-paste starting points for common tasks
- Troubleshooting section addresses real-world debugging scenarios

### What didn't work
- N/A

### What I learned
- Good documentation balances quick reference (tables) with conceptual explanations (prose)
- Diagrams (even ASCII) help visualize complex bus architectures
- Code examples are essential—showing "how" is as important as explaining "what"

### What was tricky to build
- Balancing detail vs. length—wanted comprehensive but not overwhelming
- Ensuring code examples match actual API signatures (verified against source files)
- Creating clear ASCII diagrams that show relationships without being cluttered

### What warrants a second pair of eyes
- Verify all code examples compile/work as written (they're based on actual source but not tested)
- Check that bus topology diagram accurately represents the connections
- Confirm troubleshooting tips are accurate based on real debugging experience

### What should be done in the future
- Add more code examples for advanced use cases (custom I2C devices on PORT.CUSTOM, camera frame processing, etc.)
- Consider adding performance notes (frame rates, I2C speeds, power consumption)
- Add links to external resources (ESP-IDF docs, Bosch Sensor API docs, etc.)

### Code review instructions
- Read through `doc/atoms3r-cam-m12-device-reference.md` and verify:
  - All pin numbers match `hal_config.h` and `camera_pin.h`
  - Code examples match actual API signatures in source files
  - Bus topology diagram accurately represents connections
  - Troubleshooting tips are reasonable
