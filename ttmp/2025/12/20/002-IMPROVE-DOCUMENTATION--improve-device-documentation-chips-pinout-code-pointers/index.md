---
Title: Improve device documentation (chips, pinout, code pointers)
Ticket: 002-IMPROVE-DOCUMENTATION
Status: active
Topics:
    - documentation
    - hardware
    - pinout
    - esp32s3
    - camera
    - sensors
DocType: index
Intent: long-term
Owners: []
RelatedFiles:
    - Path: doc/atoms3r-cam-m12-device-reference.md
      Note: Canonical device reference document (hardware
    - Path: main/hal_config.h
      Note: Pin constants for I2C
    - Path: main/usb_webcam_main.cpp
      Note: Main entry point and hardware initialization sequence
    - Path: main/utils/bmi270/src/bmi270.cpp
      Note: BMI270 and BMM150 initialization and driver implementation
    - Path: main/utils/camera/camera_init.c
      Note: Camera initialization wrapper (esp32-camera integration)
    - Path: main/utils/camera/camera_pin.h
      Note: Camera pin mapping (selected via sdkconfig)
ExternalSources: []
Summary: ""
LastUpdated: 2025-12-20T10:56:34.270631649-05:00
WhatFor: ""
WhenToUse: ""
---


# Improve device documentation (chips, pinout, code pointers)

## Overview

Create a **single, repo-local device reference page** for the AtomS3R-CAM-M12 hardware that covers:
- Chips + links to local datasheets/schematics
- Pinout + bus mapping (I2C, camera DVP/SCCB, IR, PORT.CUSTOM)
- Code pointers (where each device is initialized and which APIs/components are used)

## Key Links

- **Canonical device reference page**: `doc/atoms3r-cam-m12-device-reference.md`
- **Diary**: `reference/01-diary.md`
- **Device-reference (docmgr index doc)**: `reference/02-device-reference-page-atoms3r-cam-m12.md`

## Status

Current status: **active**

## Topics

- documentation
- hardware
- pinout
- esp32s3
- camera
- sensors

## Tasks

See [tasks.md](./tasks.md) for the current task list.

## Changelog

See [changelog.md](./changelog.md) for recent changes and decisions.

## Structure

- design/ - Architecture and design documents
- reference/ - Prompt packs, API contracts, context summaries
- playbooks/ - Command sequences and test procedures
- scripts/ - Temporary code and tooling
- various/ - Working notes and research
- archive/ - Deprecated or reference-only artifacts
