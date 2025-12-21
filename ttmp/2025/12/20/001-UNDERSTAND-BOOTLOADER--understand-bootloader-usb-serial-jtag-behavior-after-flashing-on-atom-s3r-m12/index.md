---
Title: Understand bootloader/USB Serial-JTAG behavior after flashing on ATOM S3R M12
Ticket: 001-UNDERSTAND-BOOTLOADER
Status: active
Topics:
    - esp32s3
    - bootloader
    - usb
    - serial-jtag
    - uvc
    - flashing
DocType: index
Intent: long-term
Owners: []
RelatedFiles:
    - Path: README.md
      Note: Documents UVC mode/web server; helps set expectations
    - Path: bootloader_components/boot_hooks/CMakeLists.txt
      Note: Forces inclusion of bootloader hook symbols
    - Path: bootloader_components/boot_hooks/boot_hooks.c
      Note: Bootloader hook disabling USB Serial/JTAG pullup
    - Path: flash.sh
      Note: Flashing entrypoint; uses /dev/ttyACM0 and runs idf.py flash+monitor
    - Path: main/hal_config.h
      Note: Pin mapping; shows button pin definition (but unused for gating)
    - Path: main/service/service_uvc.cpp
      Note: UVC init path; uses usb_device_uvc
    - Path: main/usb_webcam_main.cpp
      Note: app_main shows UVC starts unconditionally (no button gate)
    - Path: sdkconfig
      Note: Reset/monitor config and console selection (UART vs USB Serial/JTAG)
ExternalSources: []
Summary: ""
LastUpdated: 2025-12-20T10:33:36.1276058-05:00
WhatFor: ""
WhenToUse: ""
---


# Understand bootloader/USB Serial-JTAG behavior after flashing on ATOM S3R M12

## Overview

<!-- Provide a brief overview of the ticket, its goals, and current status -->

## Key Links

- **Related Files**: See frontmatter RelatedFiles field
- **External Sources**: See frontmatter ExternalSources field

## Status

Current status: **active**

## Topics

- esp32s3
- bootloader
- usb
- serial-jtag
- uvc
- flashing

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
