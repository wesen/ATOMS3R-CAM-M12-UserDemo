# Changelog

## 2025-12-20

- Initial workspace created


## 2025-12-20

Recorded investigation: app boots UVC immediately; console is UART1 (not USB); bootloader hook disables USB Serial/JTAG pullup; symptoms match ESP32-S3 USB-Serial/JTAG DOWNLOAD_MODE persistence; captured external refs.

### Related Files

- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/bootloader_components/boot_hooks/boot_hooks.c — Key bootloader behavior
- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/main/usb_webcam_main.cpp — Shows unconditional UVC start
- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/sdkconfig — Shows console+reset settings


## 2025-12-20

Added analysis doc explaining ESP32-S3 DOWNLOAD_MODE (ROM download/serial bootloader), strap pins (GPIO0/GPIO46), USB Serial/JTAG auto-download, and why it may appear to persist; linked to Espressif docs + esptool issue.

### Related Files

- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/ttmp/2025/12/20/001-UNDERSTAND-BOOTLOADER--understand-bootloader-usb-serial-jtag-behavior-after-flashing-on-atom-s3r-m12/analysis/01-esp32-s3-download-mode-what-it-is-how-it-works-and-why-it-can-persist-with-usb-serial-jtag.md — New reference for DOWNLOAD_MODE


## 2025-12-20

Added analysis doc on bootloader USB Serial/JTAG enumeration suppression (DP pullup disable): explained mechanism, likely rationale for UVC/TinyUSB, implications, and proof it's a project-local override via weak hooks + bootloader map.

### Related Files

- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/ttmp/2025/12/20/001-UNDERSTAND-BOOTLOADER--understand-bootloader-usb-serial-jtag-behavior-after-flashing-on-atom-s3r-m12/analysis/02-bootloader-usb-serial-jtag-enumeration-suppression-d-pullup-disable-rationale-commonality-and-implications.md — New analysis doc


## 2025-12-20

Expanded analysis/02 with: (a) which bootloader hooks are actually used (before_init + linker keep symbol; no after_init), and (b) a pass over bootloader-related sdkconfig flags with explanations sourced from ESP-IDF bootloader Kconfig.

### Related Files

- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/sdkconfig — Bootloader-related config values
- /home/manuel/esp/esp-idf/components/bootloader/Kconfig.projbuild — Authoritative descriptions of bootloader config flags


## 2025-12-20

Expanded both analysis documents with fuller paragraphs explaining context, APIs, and rationale in human-friendly format. Added topic-focused intro paragraphs for major sections, improved explanations of register operations and boot mode selection, and enhanced narrative flow while preserving bullet points and scannable structure. Followed glaze documentation writing guidelines.

### Related Files

- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/ttmp/2025/12/20/001-UNDERSTAND-BOOTLOADER--understand-bootloader-usb-serial-jtag-behavior-after-flashing-on-atom-s3r-m12/analysis/01-esp32-s3-download-mode-what-it-is-how-it-works-and-why-it-can-persist-with-usb-serial-jtag.md — Enhanced with context and explanations
- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/ttmp/2025/12/20/001-UNDERSTAND-BOOTLOADER--understand-bootloader-usb-serial-jtag-behavior-after-flashing-on-atom-s3r-m12/analysis/02-bootloader-usb-serial-jtag-enumeration-suppression-d-pullup-disable-rationale-commonality-and-implications.md — Enhanced with context and explanations

