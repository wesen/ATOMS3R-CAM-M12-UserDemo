---
Title: 'Bootloader USB Serial/JTAG enumeration suppression (D+ pullup disable): rationale, commonality, and implications'
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
    - https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/usb-serial-jtag-console.html
    - https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/boot-mode-selection.html
    - https://github.com/espressif/esptool/issues/970
Summary: "Explains the repo’s bootloader hook that disables USB Serial/JTAG D+ pullup (suppresses enumeration): what the registers do, why this is likely used in a UVC/TinyUSB project, how it affects flashing/monitoring, and how we know it’s a project-local override."
LastUpdated: 2025-12-20T10:45:48.590236795-05:00
WhatFor: "Understand and justify the bootloader_before_init USB Serial/JTAG enumeration suppression, and assess its implications (UVC/OTG behavior, flashing workflow, and debugging)."
WhenToUse: "Use when you see the USB Serial/JTAG device appear/disappear around boot, when UVC needs reliable enumeration, or when you suspect the bootloader is intentionally hiding USB Serial/JTAG from the host."
---

# Bootloader USB Serial/JTAG enumeration suppression (D+ pullup disable): rationale, commonality, and implications

## What the repo is doing (exact behavior)

This repository customizes the ESP32-S3 bootloader by implementing a hook function that runs before the bootloader's main initialization code. The hook directly manipulates hardware registers controlling the USB Serial/JTAG Controller's physical layer, specifically disabling the D+ pull-up resistor that signals USB device presence to the host computer.

The implementation lives in `bootloader_components/boot_hooks/boot_hooks.c`, where `bootloader_before_init()` performs three register operations on `USB_SERIAL_JTAG_CONF0_REG`:

- **Enable software control**: Sets `USB_SERIAL_JTAG_PAD_PULL_OVERRIDE` to take manual control of the D+ and D- pull resistors, overriding the hardware's default behavior.
- **Disable D+ pullup**: Clears `USB_SERIAL_JTAG_DP_PULLUP`, removing the pull-up resistor on the D+ line that normally signals "device present" to USB hosts.
- **Disable USB pad enable**: Clears `USB_SERIAL_JTAG_USB_PAD_ENABLE`, effectively disabling the USB pad drivers entirely.

**Net effect**: Without the D+ pull-up resistor, the USB host cannot detect the device's presence. The USB Serial/JTAG Controller remains electrically invisible during the bootloader phase, preventing enumeration and descriptor retrieval.

The code comment explicitly states the intent: "Disable D+ pullup, to prevent the USB host from retrieving USB-Serial-JTAG's descriptor." This is a deliberate design choice, not an accidental side effect.

## Why this is "weird" but plausible (likely rationale)

At first glance, disabling USB Serial/JTAG enumeration seems counterintuitive—after all, that's the interface you use for flashing and debugging. However, the ESP32-S3's USB architecture creates a conflict when you want to use the same physical USB port for multiple purposes.

The ESP32-S3 provides two USB-related hardware blocks that share the same physical USB connector:

- **USB Serial/JTAG Controller**: A fixed-function hardware block that provides a USB CDC-ACM serial port and JTAG debugging. This controller cannot be reconfigured or disabled by software in normal operation—it's always "there" unless you take explicit steps to hide it.
- **USB-OTG peripheral**: A flexible USB controller that can operate as either a USB host or USB device. This is what TinyUSB uses to implement USB device classes like UVC (USB Video Class) for webcam functionality.

**The conflict**: Both controllers want to use the same USB D+ and D- lines. When the chip boots, the USB Serial/JTAG Controller may enumerate first, causing the host operating system to bind USB serial port drivers and create a `/dev/ttyACM0` device. Then, when your application starts and TinyUSB initializes the USB-OTG peripheral to enumerate as a UVC device, the USB Serial/JTAG device disappears and a new video device appears. This device "flapping" can confuse host applications, cause driver binding issues, and make debugging workflows unreliable.

**Why this matters for UVC**: Camera applications are particularly sensitive to USB device enumeration. They expect a stable, persistent video device. If the device appears and disappears, or if the host caches the wrong device identity, video streaming can fail or become unreliable. By suppressing USB Serial/JTAG enumeration during bootloader execution, this hook ensures that when the application boots and enumerates as UVC, it's the first (and only) USB device the host sees, creating a clean enumeration path.

So suppressing USB Serial/JTAG enumeration in the bootloader is a pragmatic trade-off: you sacrifice the convenience of monitoring bootloader logs over USB Serial/JTAG in exchange for reliable UVC enumeration and a cleaner USB device identity.

## How this affects your workflow (implications)

Understanding this bootloader hook helps explain why certain development workflows behave unexpectedly and guides you toward the right tools for each task.

**Flashing still works, but transitions are confusing**: Flashing firmware over `/dev/ttyACM0` continues to function because the ROM bootloader and USB Serial/JTAG Controller can still enter DOWNLOAD_MODE when needed. However, the transition from "flashing mode" to "application mode" can be disorienting: the serial port you just used for flashing disappears entirely, replaced by a video device. This isn't a bug—it's the intended behavior, but it can make debugging feel broken when it's actually working as designed.

**Monitoring expectations need adjustment**: Attempting to monitor application logs on `/dev/ttyACM0` is unreliable for this project for two reasons. First, the `sdkconfig` explicitly routes console output to **UART1** (TX=GPIO5, RX=GPIO44), not to USB Serial/JTAG. Second, even if console were routed to USB Serial/JTAG, the device re-enumerates as a UVC webcam after boot, causing the serial port to disappear. To see application logs, you need a USB-to-UART adapter connected to GPIO5/GPIO44, or you need to reconfigure the console routing.

**JTAG debugging limitations**: If you rely on the internal USB-JTAG bridge for debugging, you may find it unavailable during early boot phases when the hook suppresses enumeration. For consistent JTAG access, especially during bootloader execution, an external JTAG adapter connected to the dedicated JTAG pins may be more reliable.

## How we know this is a project-local override (not "standard ESP-IDF behavior")

It's important to distinguish between ESP-IDF's built-in bootloader behavior and project-specific customizations. This USB Serial/JTAG suppression is definitely the latter—a deliberate override implemented by this project, not something that happens automatically in every ESP-IDF build.

We can prove this with two independent lines of evidence:

### 1) ESP-IDF design: bootloader hooks are explicitly weak + user-overridable

ESP-IDF's bootloader architecture uses the C linker's "weak symbol" mechanism to allow projects to customize bootloader behavior without modifying ESP-IDF source code. In your local ESP-IDF installation, `components/bootloader/subproject/main/bootloader_hooks.h` declares `bootloader_before_init()` with the `__attribute__((weak))` attribute. This means the symbol has a default "do nothing" implementation that can be overridden by any project that provides its own definition.

The header file's documentation explicitly states that these hooks are "meant to be defined by user projects" and points developers to the `custom_bootloader` example for reference. The bootloader startup code in `bootloader_start.c` calls `bootloader_before_init()` before `bootloader_init()`, but if no project provides an implementation, the weak symbol resolves to nothing and the call effectively does nothing.

**Meaning**: ESP-IDF does not disable USB Serial/JTAG enumeration by default. If you create a fresh ESP-IDF project without any bootloader hooks, the USB Serial/JTAG Controller will enumerate normally during bootloader execution. This project's hook is a deliberate customization.

### 2) Your build artifacts: the symbol is coming from the project's boot hook library

The linker map file (`build/bootloader/bootloader.map`) provides concrete proof of where code originates. When you examine the map, you'll find that `bootloader_before_init` is located in `esp-idf/boot_hooks/libboot_hooks.a(boot_hooks.c.obj)`, which corresponds to this project's `bootloader_components/boot_hooks/boot_hooks.c` source file.

Additionally, the linker command line includes `-u bootloader_hooks_include`, which is a "force undefined" flag that ensures the `bootloader_hooks_include()` symbol is treated as required, forcing the linker to include the boot_hooks library even though the hook functions themselves are weak symbols. This matches the "force link" technique documented in the project's `bootloader_components/boot_hooks/CMakeLists.txt`.

**This demonstrates**: The override is being compiled into your project's bootloader build from your project's source code, not from ESP-IDF's stock bootloader support. If you removed the `bootloader_components/` directory, the hook would disappear and USB Serial/JTAG would enumerate normally.

## Is this common? (what we found / didn't find)

When evaluating whether this bootloader customization is a standard practice or an unusual workaround, the answer depends on what level of abstraction you're asking about.

**The mechanism is standard**: ESP-IDF explicitly supports bootloader hook overrides as a first-class feature. The `bootloader_before_init()` hook mechanism is documented, has example code in ESP-IDF's `custom_bootloader` example, and is intended for exactly this kind of project-specific customization. So from ESP-IDF's perspective, using bootloader hooks is a normal, supported way to customize boot behavior.

**The specific technique is uncommon**: However, the specific choice to disable USB Serial/JTAG D+ pullup to suppress enumeration appears to be less commonly documented in public codebases. Our searches for other projects using `USB_SERIAL_JTAG_DP_PULLUP` in combination with `bootloader_before_init()` found few direct matches, suggesting this is either a niche solution or a technique that's not widely shared.

**Why this might be**: Most ESP32-S3 projects probably don't need to suppress USB Serial/JTAG enumeration. Projects that use USB Serial/JTAG as their primary console benefit from normal enumeration. Projects that use USB-OTG for other purposes might not encounter the enumeration conflict, or they might solve it differently (for example, by configuring the application to disable USB Serial/JTAG after boot rather than suppressing it in the bootloader).

The strongest justification for this approach comes from the repository's own comment, combined with ESP-IDF's documented USB Serial/JTAG limitations and the specific needs of a UVC device that must enumerate reliably. If you want to find more examples, searching GitHub for `USB_SERIAL_JTAG_DP_PULLUP` combined with `bootloader_before_init()` or similar register manipulation might yield additional cases, but the technique appears to be specialized rather than common practice.

## Bootloader hooks used by this repo (and why)

ESP-IDF provides a flexible hook system that lets projects inject custom code at specific points in the bootloader execution sequence. Understanding which hooks this project uses (and which it doesn't) helps clarify the scope of the bootloader customization.

ESP-IDF exposes two primary bootloader hook points:

- **`bootloader_before_init()`**: A weak function called before the bootloader's main initialization code runs. This is the earliest point where you can execute custom code, but system services aren't available yet—you're limited to direct register manipulation.
- **`bootloader_after_init()`**: A weak function called after `bootloader_init()` completes. At this point, more system services are available, but you're closer to application boot.

**This repo's hook usage**:

- **`bootloader_before_init()` is implemented**: The project uses this hook to suppress USB Serial/JTAG enumeration by disabling the D+ pullup resistor. This must happen early because USB enumeration can begin as soon as the USB pad drivers are enabled, which happens during bootloader initialization.
- **`bootloader_after_init()` is not implemented**: There's no implementation provided, and the bootloader link map confirms no project-defined `bootloader_after_init` is linked. This suggests the project doesn't need to perform any actions after bootloader initialization completes.
- **`bootloader_hooks_include()` is a linker helper**: This function serves no runtime purpose—it exists solely to force the linker to include the boot_hooks object file. Because `bootloader_before_init()` is a weak symbol, the linker might otherwise discard the entire object file if it thinks the symbol isn't needed. By referencing `bootloader_hooks_include()` with the `-u` linker flag, the project ensures the hook code is always included.

**Evidence from build artifacts**:

- The repository only contains one bootloader hook component: `bootloader_components/boot_hooks/boot_hooks.c`.
- The bootloader link map (`build/bootloader/bootloader.map`) shows `bootloader_before_init` and `bootloader_hooks_include` symbols originating from `esp-idf/boot_hooks/libboot_hooks.a(boot_hooks.c.obj)`, confirming they're compiled from the project's source, not ESP-IDF defaults.

## Bootloader-related `sdkconfig` settings (this repo)

The ESP-IDF build system uses Kconfig to manage configuration options, and bootloader-specific settings are defined in `components/bootloader/Kconfig.projbuild`. These settings control how the 2nd-stage bootloader behaves, what features it enables, and how it interacts with the application. Understanding these settings helps explain bootloader behavior and guides troubleshooting when boot issues occur.

The following settings are present in this project's `sdkconfig` and directly affect bootloader operation:

### `CONFIG_BOOTLOADER_OFFSET_IN_FLASH=0x0`

**Meaning**: Where the 2nd-stage bootloader is flashed. ESP-IDF notes this value is “determined by the ROM bootloader” and “not configurable in ESP-IDF”.

**Why you care**: If this didn’t match the target’s ROM expectations, the chip wouldn’t boot your 2nd-stage bootloader at all.

### `CONFIG_BOOTLOADER_COMPILER_OPTIMIZATION_SIZE=y`

**Meaning**: Builds bootloader with `-Os` (optimize for size).

**Why you care**: Smaller bootloader footprint; occasionally interacts with debug visibility/perf but usually a sensible default.

### `CONFIG_BOOTLOADER_LOG_LEVEL_INFO=y` and `CONFIG_BOOTLOADER_LOG_LEVEL=3`

**Meaning**: Bootloader log verbosity set to INFO (3).

**Why you care**: If you are monitoring the bootloader console output path, you’ll see informational boot logs (helpful when diagnosing reset/boot loops).

### `CONFIG_BOOTLOADER_FLASH_XMC_SUPPORT=y`

**Meaning**: Enables the startup flow recommended by XMC flash chips. ESP-IDF warns: “DON’T DISABLE THIS UNLESS YOU KNOW WHAT YOU ARE DOING.”

**Why you care**: If your board uses an XMC flash part, disabling could break boot or flash operations.

### `CONFIG_BOOTLOADER_VDDSDIO_BOOST_1_9V=y`

**Meaning**: If VDDSDIO is configured to 1.8V, bootloader will boost to 1.9V to avoid brownout during flash programming operations (no effect if VDDSDIO is 3.3V or internal regulator disabled).

**Why you care**: Helps prevent marginal flash power issues during writes (especially at higher flash speeds).

### `CONFIG_BOOTLOADER_REGION_PROTECTION_ENABLE=y`

**Meaning**: Enables protection for unmapped memory regions; triggers an exception on unintended accesses to unmapped address space.

**Why you care**: Hardens early boot against “wild pointer” style faults.

### `CONFIG_BOOTLOADER_WDT_ENABLE=y` and `CONFIG_BOOTLOADER_WDT_TIME_MS=9000`

**Meaning**: Enables the RTC (Real-Time Clock) watchdog timer, which tracks total boot time from the moment the bootloader starts executing until `app_main()` is called. The watchdog uses the slow clock source (which depends on RTC_CLK_SRC configuration), so the bootloader resets the timeout whenever it changes the slow clock frequency. If the total boot time exceeds 9000 milliseconds (9 seconds), the watchdog triggers a chip reset.

**Why you care**: This watchdog prevents hard hangs during early boot caused by power instability, broken initialization code, or infinite loops. However, if your boot path legitimately takes longer—for example, if you're performing flash encryption, triggering factory reset logic, or doing extensive hardware initialization—you must increase `CONFIG_BOOTLOADER_WDT_TIME_MS` to avoid false resets. The default 9 seconds is usually sufficient for normal boot paths but may be too short for security-enabled configurations.

### `CONFIG_BOOTLOADER_RESERVE_RTC_SIZE=0`

**Meaning**: RTC fast memory reserved size for bootloader features is 0 (no extra reservation beyond defaults).

**Why you care**: Some bootloader features (factory reset triggers, etc.) can reserve RTC memory; not used here.

### `CONFIG_SECURE_BOOT_V2_RSA_SUPPORTED=y` and `CONFIG_SECURE_BOOT_V2_PREFERRED=y`

**Meaning**: SoC supports Secure Boot V2 RSA, and V2 is preferred where applicable. (These are capability/preferences flags; not the same as “Secure Boot is enabled”.)

**Why you care**: Indicates the platform supports SBv2; whether it’s actually enabled depends on additional flags and eFuse provisioning.

### `CONFIG_SECURE_ROM_DL_MODE_ENABLED=y`

**Meaning**: Enables support for “secure download mode” (SoC capability dependent). ESP-IDF uses this to control whether secure ROM download mode choices apply.

**Why you care**: In production security configurations (secure boot/flash encryption), ROM download mode behavior often becomes a security policy decision. Even in dev, this helps explain why “download mode” behavior can differ between builds/devices.

### `CONFIG_ESPTOOLPY_BEFORE="default_reset"` / `CONFIG_ESPTOOLPY_AFTER="hard_reset"`

**Meaning**: These settings control how `esptool.py` (invoked by `idf.py flash`) resets the chip before and after flashing operations. `default_reset` uses DTR/RTS control lines (or USB Serial/JTAG reset mechanisms) to trigger a reset, while `hard_reset` performs a more forceful reset sequence. The "before" reset ensures the chip enters DOWNLOAD_MODE, while the "after" reset attempts to boot the newly flashed application.

**Why you care**: With ESP32-S3 USB Serial/JTAG, the reset semantics can interact with the DOWNLOAD_MODE persistence issue documented in esptool #970. A "hard reset" after flashing may not properly clear the strapping pin state if the chip originally entered DOWNLOAD_MODE via USB Serial/JTAG, leaving the device stuck waiting for flash commands. This is part of why running `idf.py flash monitor` can leave you thinking the device didn't boot—it may genuinely be stuck in DOWNLOAD_MODE, requiring a physical reset button press or USB replug to recover.

### Console routing (relevant to boot perception)

- `# CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG is not set`
- `CONFIG_ESP_CONSOLE_UART_CUSTOM=y` with UART1 TX=GPIO5 RX=GPIO44

**Meaning**: Your console logs are not on USB Serial/JTAG.

**Why you care**: Watching `/dev/ttyACM0` after boot can be misleading even when everything is working, especially if the device enumerates as UVC.

## Questions to validate next (if you want to go deeper)

- Does the ATOM S3R M12 hardware/efuse setup select USB-OTG as the primary USB function (vs USB Serial/JTAG)?
- Is the hook needed only on specific hosts (Windows vs Linux) or only when the host aggressively enumerates USB devices during reset?
- Would disabling this hook improve flashing/monitor convenience at the cost of UVC stability? (likely yes)
