---
Title: Diary
Ticket: 001-UNDERSTAND-BOOTLOADER
Status: active
Topics:
    - esp32s3
    - bootloader
    - usb
    - serial-jtag
    - uvc
    - flashing
DocType: reference
Intent: long-term
Owners: []
RelatedFiles:
    - Path: bootloader_components/boot_hooks/boot_hooks.c
      Note: Evidence USB Serial/JTAG enumeration is intentionally suppressed in bootloader
    - Path: flash.sh
      Note: Reproduces symptom path (flash+monitor on /dev/ttyACM0)
    - Path: main/usb_webcam_main.cpp
      Note: Evidence app does not wait for button
    - Path: sdkconfig
      Note: Console is UART1 and UVC is TinyUSB
ExternalSources: []
Summary: ""
LastUpdated: 2025-12-20T10:33:36.207672647-05:00
WhatFor: ""
WhenToUse: ""
---


# Diary

## Goal

Capture the investigation into why an ATOM S3R M12 appears to “stay in bootloader mode” after `flash.sh` and only “boots into UVC” after pressing a button, including repo findings, web references, and the inferences connecting them.

## Context

Observed behavior (Linux host, ESP-IDF project):

- Running `flash.sh` (which calls `idf.py ... flash ... monitor` on `/dev/ttyACM0`) appears to leave the board in a **USB Serial/JTAG**-like state where “nothing runs”.
- Pressing a physical button on the device then results in the device enumerating/working in **UVC webcam mode**.

Key framing:

- The firmware itself can be correct, while the **flash/boot/USB-Serial-JTAG path** makes it *look* like nothing is running (e.g., no logs on that port, device enumerates as UVC instead of a serial console, or the chip remains in ROM download mode).

## Quick Reference

## Step 1: Validate whether the app waits for a button (repo inspection)

We first checked if the firmware intentionally blocks startup until a button press. The top-level `app_main()` starts UVC + web server unconditionally; no “wait for button” gating was found.

**Repo evidence**

- `main/usb_webcam_main.cpp`: calls `start_service_uvc()` and `start_service_web_server()` directly in `app_main()`.
- `main/service/service_uvc.cpp`: initializes UVC immediately in `start_service_uvc()`.
- `main/hal_config.h`: defines `HAL_PIN_BUTTON_A`, but we did not find logic that uses it to gate boot.

**Inference**

- The “button makes it boot” symptom is likely not an app-level feature switch; it’s more likely a **reset / boot strap / USB-Serial-JTAG download-mode** interaction.

## Step 2: Identify the flashing path and why “monitor shows nothing”

`flash.sh` uses the USB Serial/JTAG ACM device:

- `SERIAL_PORT=/dev/ttyACM0`
- Runs `idf.py -p ${SERIAL_PORT} flash ... monitor`

**Repo evidence**

- `flash.sh`
- `sdkconfig`: `CONFIG_ESPTOOLPY_BEFORE="default_reset"`, `CONFIG_ESPTOOLPY_AFTER="hard_reset"`

**Additional repo evidence that affects “monitor”: console is not USB**

The project’s ESP-IDF console is configured to UART1 (custom TX/RX GPIOs), not USB Serial/JTAG.

- `sdkconfig`: `CONFIG_ESP_CONSOLE_UART_CUSTOM=y`, `CONFIG_ESP_CONSOLE_UART_NUM=1`, TX=GPIO5, RX=GPIO44
- `sdkconfig`: `# CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG is not set`

**Inference**

- Even when the app is running, you may see *no logs* on `/dev/ttyACM0` because that’s not where the console is.
- When the app boots into UVC, it may enumerate as a **USB webcam**, which can also disrupt the assumptions `idf.py monitor` makes about a stable serial port.

## Step 3: Bootloader hook that modifies USB Serial/JTAG behavior

This repo includes a bootloader hook that explicitly disables USB Serial/JTAG D+ pullup during bootloader init:

- `bootloader_components/boot_hooks/boot_hooks.c` implements `bootloader_before_init()`
- `bootloader_components/boot_hooks/CMakeLists.txt` forces inclusion so the weak hook is not discarded

**Observed intent (from comment)**

- “Disable D+ pullup, to prevent the USB host from retrieving USB-Serial-JTAG's descriptor.”

**Inference**

- The project is intentionally trying to prevent enumeration as USB Serial/JTAG (likely to avoid conflicts with USB-OTG/UVC).
- This can make “serial jtag but nothing runs” extra confusing: the system may be transitioning between USB roles/devices during boot.

## Step 4: Confirm UVC is TinyUSB-based (repo inspection)

Evidence indicates the firmware uses TinyUSB for UVC:

- `sdkconfig` contains `CONFIG_TUSB_PRODUCT="ESP UVC Device"` and “USB Device UVC” settings.
- `main/service/service_uvc.cpp` includes and uses `usb_device_uvc.h` (the project’s `components/usb_device_uvc` integration).

**Inference**

- It is expected that, in the “happy path”, the board enumerates as a webcam, not as a serial console.

## Step 5: Online triangulation — ESP32-S3 USB Serial/JTAG “stuck in DOWNLOAD_MODE”

We searched for ESP32-S3 + USB Serial/JTAG cases where devices appear stuck in bootloader after flashing and only recover with a physical reset. The most directly relevant reference found:

- Esptool issue: [“Can't reboot device using USB Serial JTAG when in DOWNLOAD_MODE” (espressif/esptool #970)](https://github.com/espressif/esptool/issues/970)
  - Key takeaway from the issue description/update: if the chip initially booted into **DOWNLOAD_MODE**, rebooting may not clear strapping pins; the “stuck in download mode” behavior is observed with **USB Serial/JTAG**, not UART.

We also saw (more general) vendor docs describing manual reset / boot flows for ATOM S3R M12:

- M5Stack programming page (mentions button/reset interactions): [docs.m5stack.com — ATOM S3R M12 program](https://docs.m5stack.com/en/arduino/m5atoms3r-m12/program)

**Inference**

- Your symptoms fit a common pattern:
  - flash tool puts the chip into download mode via USB Serial/JTAG,
  - after flashing, the attempted “hard reset” is not sufficient to exit DOWNLOAD_MODE in some cases,
  - pressing the button performs a “real” reset/power-cycle/strap-clearing event, and the app then boots and enumerates as UVC.

## Notes / hypotheses to validate next (if we continue)

- Verify which physical button you’re pressing (RESET/EN vs BOOT/IO0) for ATOM S3R M12; the observed “button press fixes it” strongly suggests a reset/strap event, not app logic.
- Try flashing without immediately attaching monitor:
  - e.g., run `idf.py -p /dev/ttyACM0 flash` (no `monitor`) and then power-cycle / reset once.
- If you want logs: connect to UART1 (TX GPIO5 / RX GPIO44) rather than relying on USB Serial/JTAG.

## Step 6: What I did during follow-up research (docs + DOWNLOAD_MODE explainer + bootloader hook validation)

This step captures the doc + research work done after the initial hypothesis, so we don’t lose the trail. The goal was to (a) preserve findings in docmgr, (b) write a grounded explanation of DOWNLOAD_MODE, and (c) validate that the bootloader USB enumeration tweak is truly a project-local override (not “standard ESP-IDF behavior”).

### What I did

- Created a new docmgr ticket `001-UNDERSTAND-BOOTLOADER`, added this diary document, and related key repo files (`flash.sh`, `sdkconfig`, bootloader hook, UVC entrypoints).
- Wrote an analysis document explaining ESP32-S3 DOWNLOAD_MODE and connected it back to our observed symptoms and repo configuration.
  - Espressif sources used:
    - Esptool “Boot Mode Selection (ESP32-S3)” (GPIO0/GPIO46 strapping): `https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/boot-mode-selection.html`
    - ESP-IDF “USB Serial/JTAG Controller Console” (auto-download mode, limitations): `https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/usb-serial-jtag-console.html`
  - Symptom-matching issue used:
    - Esptool #970: `https://github.com/espressif/esptool/issues/970`
- Fixed a doc frontmatter error (duplicate `ExternalSources` key) that prevented `docmgr doc relate` from working for one analysis doc, then re-ran relate + changelog update.
- Validated that `bootloader_before_init()` is **not** “standard behavior” but a supported **weak hook override**:
  - In ESP-IDF source:
    - `bootloader_hooks.h` declares `bootloader_before_init()` as `__attribute__((weak))` and explicitly says these hooks are meant to be defined by user projects and references the `custom_bootloader` example.
    - `bootloader_start.c` calls `bootloader_before_init()` before `bootloader_init()`.
  - In this repo’s build output:
    - `build/bootloader/bootloader.map` shows `bootloader_before_init` coming from `esp-idf/boot_hooks/libboot_hooks.a(boot_hooks.c.obj)`, which corresponds to this project’s `bootloader_components/boot_hooks/boot_hooks.c`.
    - `build/bootloader/build.ninja` link line includes `-u bootloader_hooks_include`, matching this repo’s approach to force the hook library into the bootloader link.

### What I learned

- ESP-IDF has an explicit, documented mechanism for project-local bootloader customization (weak hooks + bootloader components). This repo uses it to change USB Serial/JTAG enumeration behavior before bootloader init.
- The “why is it weird?” question is fair: it’s an aggressive workaround to keep the host from “seeing” USB Serial/JTAG early, likely to reduce conflicts when the application later wants to own USB for UVC (TinyUSB).

## Usage Examples

When you hit “stuck in bootloader” symptoms after flashing:

- Use this diary to quickly check:
  - whether the firmware has an intentional “wait for button” gate (it doesn’t),
  - whether your flashing/monitor path is using USB Serial/JTAG and expecting console output on that port,
  - whether the bootloader hook that disables USB Serial/JTAG enumeration applies to your build,
  - whether the known USB Serial/JTAG DOWNLOAD_MODE behavior could explain it.

## Related

- Ticket index: `../index.md`
- Esptool issue: [espressif/esptool #970](https://github.com/espressif/esptool/issues/970)
- M5Stack docs: [ATOM S3R M12 program](https://docs.m5stack.com/en/arduino/m5atoms3r-m12/program)
