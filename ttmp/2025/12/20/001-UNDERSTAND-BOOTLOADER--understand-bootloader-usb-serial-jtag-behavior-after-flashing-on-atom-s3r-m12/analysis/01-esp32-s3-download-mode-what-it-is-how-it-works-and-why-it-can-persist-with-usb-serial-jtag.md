---
Title: 'ESP32-S3 DOWNLOAD_MODE: what it is, how it works, and why it can persist with USB Serial/JTAG'
Ticket: 001-UNDERSTAND-BOOTLOADER
Status: active
Topics:
    - esp32s3
    - bootloader
    - usb
    - serial-jtag
    - uvc
    - flashing
DocType: analysis
Intent: long-term
Owners: []
RelatedFiles: []
ExternalSources:
    - https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/boot-mode-selection.html
    - https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/usb-serial-jtag-console.html
    - https://github.com/espressif/esptool/issues/970
    - https://docs.m5stack.com/en/arduino/m5atoms3r-m12/program
Summary: "Explains ESP32-S3 DOWNLOAD_MODE (ROM serial bootloader): what it is for, how GPIO strapping selects it, how USB Serial/JTAG can enter it automatically, and why it can appear to persist after flashing."
LastUpdated: 2025-12-20T10:38:40.738260747-05:00
WhatFor: "Troubleshooting and explaining ESP32-S3 boot behavior (normal boot vs ROM download mode), especially when flashing/monitoring over USB Serial/JTAG and when devices appear stuck until a manual reset."
WhenToUse: "Use when the board seems to remain in bootloader/download mode after flashing, when USB Serial/JTAG enumeration is confusing, or when you need a concise reference for how ESP32-S3 boot mode selection works."
---

# ESP32-S3 DOWNLOAD_MODE: what it is, how it works, and why it can persist with USB Serial/JTAG

## What “DOWNLOAD_MODE” is (definition)

When you power on or reset an ESP32-S3, the chip must decide whether to run your application code from flash memory or wait for you to upload new firmware. **DOWNLOAD_MODE** (also called **Download Boot**, **serial bootloader**, or **ROM download mode**) is the boot path where the chip runs a minimal bootloader program stored permanently in ROM. This ROM bootloader doesn't execute your application—instead, it waits patiently for a host computer to connect and send firmware images or flash commands.

This is fundamentally different from normal boot, where the chip loads and runs your application code from flash memory. Think of DOWNLOAD_MODE as a "recovery mode" that's always available, even if your application is corrupted or missing entirely.

## What it is for (why it exists)

DOWNLOAD_MODE serves as the chip's safety net and primary mechanism for firmware management. Without it, you'd have no way to program a blank chip or recover from a bad firmware update. The ROM bootloader provides a minimal, always-available interface that lets you write to flash memory, read back what you've written, and perform other low-level operations—all without requiring any working application code.

The mode enables three critical workflows:

- **Initial firmware flashing**: When you first receive a blank ESP32-S3, DOWNLOAD_MODE is the only way to get your code onto the chip.
- **Recovery from failures**: If your application crashes in a way that prevents normal boot, or if you accidentally flash corrupted firmware, DOWNLOAD_MODE lets you reflash without external hardware.
- **Manufacturing and field updates**: Production lines and field service tools rely on DOWNLOAD_MODE to program devices consistently and update firmware in deployed products.

In your daily development workflow, you intentionally enter DOWNLOAD_MODE whenever you run `idf.py flash`. The flashing tool communicates with the ROM bootloader using a simple serial protocol, sending commands like "erase this sector" or "write this data to that address."

## How ESP32-S3 selects DOWNLOAD_MODE (strap pins at reset)

The ESP32-S3 doesn't have a configuration menu or DIP switches to choose boot mode. Instead, it samples the voltage levels on specific GPIO pins at the exact moment of reset, using these "strapping pins" to make a binary decision: run the application from flash, or wait in DOWNLOAD_MODE. This hardware-level mechanism ensures the boot mode decision happens before any software runs, making it impossible for buggy firmware to prevent recovery.

The chip reads two strapping pins during reset:

- **GPIO0**: This is the primary boot mode selector. When GPIO0 is held low (grounded) during reset, the chip enters DOWNLOAD_MODE. When GPIO0 is high (or left floating), the chip attempts normal boot from flash. GPIO0 has an internal pull-up resistor, so leaving it unconnected defaults to "high" and normal boot.
- **GPIO46**: This pin acts as a secondary qualifier. To enter DOWNLOAD_MODE, GPIO46 must also be low or floating. However, if GPIO0 is already high (normal boot path), GPIO46's state is ignored entirely. This two-pin system provides some protection against accidental entry into download mode.

The strapping pin values are latched into hardware registers at reset time and remain stable throughout the boot process. This means you can't change boot mode by toggling GPIOs after reset—the decision is already made.

Source: `https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/boot-mode-selection.html`

### Manual entry (typical BOOT+RESET sequence)

Most development boards simplify the strapping pin manipulation by wiring physical buttons to the relevant pins. A "BOOT" or "FLASH" button typically connects to GPIO0, pulling it low when pressed. The "RESET" or "EN" button triggers a chip reset. To manually enter DOWNLOAD_MODE, you perform a specific sequence:

1. **Hold the BOOT button**: This pulls GPIO0 low, preparing the strapping pin for download mode.
2. **Press and release RESET**: This triggers a reset while GPIO0 is still held low, causing the chip to sample the strapping pins and enter DOWNLOAD_MODE.
3. **Release the BOOT button**: Once the chip has latched the boot mode decision, you can release the button.

The timing matters: GPIO0 must be low at the exact moment reset occurs. If you release BOOT before pressing RESET, or if you press RESET before holding BOOT, the chip will likely boot normally instead. This sequence ensures the strapping pins are sampled correctly at reset time.

## How USB Serial/JTAG relates (automatic entry into download mode)

The ESP32-S3 includes a built-in **USB Serial/JTAG Controller**—a dedicated hardware block that provides a USB CDC-ACM (serial port) interface and JTAG debugging capabilities without requiring an external USB-to-UART bridge chip. This controller is more than just a convenience feature; it can actively manage the boot process by automatically placing the chip into DOWNLOAD_MODE when needed.

According to ESP-IDF's programming guide, the USB Serial/JTAG Controller can automatically trigger DOWNLOAD_MODE during flashing operations. When you run `idf.py flash -p /dev/ttyACM0` (or the Windows equivalent COM port), the flashing tool communicates with the USB Serial/JTAG Controller, which then handles the reset sequence internally. This means you don't need to manually press the BOOT and RESET buttons—the controller coordinates everything.

**Practical consequence for your workflow:**

- If you flash using the USB Serial/JTAG port (typically `/dev/ttyACM0` on Linux or a COM port on Windows), the host tooling can enter DOWNLOAD_MODE automatically without manual button presses.
- This convenience comes with a trade-off: the automatic reset mechanism can sometimes leave the chip in DOWNLOAD_MODE longer than expected, especially if the reset sequence doesn't fully clear the strapping pin state.

Source: `https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/usb-serial-jtag-console.html`

## Why "stuck in DOWNLOAD_MODE" can happen (esp. with USB Serial/JTAG)

When you flash firmware and then try to run your application, you might observe that the device seems to remain in DOWNLOAD_MODE even after the flashing completes. This frustrating behavior can stem from two fundamentally different causes, and understanding which one applies helps you choose the right fix.

### 1) You're in DOWNLOAD_MODE and a reset doesn't actually exit it

The ESP32-S3 has a documented quirk when using the USB Serial/JTAG interface: if the chip originally booted into DOWNLOAD_MODE (either manually or automatically via the USB Serial/JTAG Controller), a software-triggered reset may not properly clear the strapping pin state. The chip appears to remain stuck in DOWNLOAD_MODE, waiting for flash commands that will never come.

This issue was reported in `espressif/esptool` issue #970, where a developer noted: "if originally booted in DOWNLOAD_MODE, device stays stuck in DOWNLOAD_MODE. rebooting does not clear strapping pins. This only occurs with USJ, not UART." The "USJ" refers to USB Serial/JTAG, distinguishing it from traditional UART-based flashing where this problem doesn't occur.

**Why this happens**: The USB Serial/JTAG Controller manages reset sequences differently than external UART adapters. When it triggers a reset, the strapping pins may not be sampled correctly, or the controller's internal state may influence the boot mode decision in unexpected ways.

**Implication for workflows**: After flashing over USB Serial/JTAG, you may need a **true hardware reset** (physical reset button press) or **power cycle** (unplugging and replugging USB) to reliably return to normal boot. A software reset via `idf.py monitor` or `esp_restart()` may not be sufficient.

Source: `https://github.com/espressif/esptool/issues/970`

### 2) The app is running, but you can't "see it" over the port you're watching

Sometimes the application boots perfectly fine, but you can't tell because you're watching the wrong interface or the device has changed its USB identity. This creates the illusion that nothing is running, when in reality your code is executing normally.

Common scenarios where this happens:

- **Console routing mismatch**: Your `sdkconfig` may route console output to UART1 (GPIO5/GPIO44) instead of USB Serial/JTAG. Watching `/dev/ttyACM0` shows nothing because logs are going to a different physical interface.
- **USB re-enumeration**: The device may enumerate as a different USB device class (like a UVC webcam) after boot, causing the serial port to disappear from the system. Your application is running, but the host sees it as a camera, not a serial device.
- **Early USB reconfiguration**: The firmware may disable or reconfigure the USB Serial/JTAG Controller during early boot, causing it to disappear from the host system before you can attach a monitor.

## How this relates to *this* repo (ATOM S3R M12 UVC project)

The symptoms observed in this repository—where the device appears to "stay in bootloader mode" after flashing and only "boots into UVC" after pressing a button—are actually a combination of both problem classes described above. Understanding the specific configuration of this project explains why the behavior is particularly confusing.

**The flashing workflow**: The `flash.sh` script uses `/dev/ttyACM0` (the USB Serial/JTAG port) and runs `idf.py flash monitor` in one command. This means the chip enters DOWNLOAD_MODE automatically via USB Serial/JTAG, which can trigger the "stuck in DOWNLOAD_MODE" issue where a software reset doesn't properly exit download mode.

**The console configuration**: This project's `sdkconfig` routes console output to **UART1** (TX=GPIO5, RX=GPIO44), not to USB Serial/JTAG. Even if the application boots successfully, you won't see any logs on `/dev/ttyACM0` because they're going to a different physical interface entirely.

**The USB device identity**: The firmware is designed to enumerate as a **TinyUSB UVC device** ("ESP UVC Device"), not as a serial console. After boot, the device should appear as a webcam in your operating system, not as a serial port. This means `/dev/ttyACM0` may disappear entirely once the application starts, replaced by a video device.

**The bootloader hook**: The bootloader contains a custom hook (`bootloader_before_init`) that disables the USB Serial/JTAG D+ pull-up resistor early in the boot process. This prevents the host from enumerating the USB Serial/JTAG device during bootloader execution, likely to avoid USB role conflicts when the application later enumerates as UVC. This hook contributes to the "invisible boot" effect, making it harder to observe what's happening during early boot.

Together, these factors create a perfect storm: the device may genuinely be stuck in DOWNLOAD_MODE due to the USB Serial/JTAG reset quirk, but even if it boots successfully, you can't easily verify this because logs aren't on the port you're watching and the device changes its USB identity.

## Practical troubleshooting checklist

When a board “only boots after pressing a button” after flashing:

- Confirm whether the button is **RESET/EN** vs **BOOT/IO0**.
- Try flashing **without** immediately attaching `monitor`, then do a manual reset/power-cycle.
- If you need logs, use the configured UART console pins (don’t assume `/dev/ttyACM0` will show logs).
- If you suspect the USB Serial/JTAG DOWNLOAD_MODE persistence issue:
  - power-cycle / replug USB
  - avoid workflows that keep the device in download mode longer than necessary

## Notes / open questions

- Board-specific wiring (which button maps to GPIO0 vs EN) and host USB behavior can change the exact symptom.
- This doc intentionally focuses on the *conceptual model* + authoritative references; for this repo’s concrete behavior, see the ticket Diary.
