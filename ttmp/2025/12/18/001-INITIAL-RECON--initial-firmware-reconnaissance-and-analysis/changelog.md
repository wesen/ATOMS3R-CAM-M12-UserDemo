# Changelog

## 2025-12-18

- Initial workspace created


## 2025-12-18

Initial firmware reconnaissance completed. Created comprehensive analysis document and research diary documenting architecture, components, APIs, and usage. Analyzed main application, UVC service, web server, APIs, SharedData system, camera initialization, asset pool, and dependencies.

### Related Files

- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/ttmp/2025/12/18/001-INITIAL-RECON--initial-firmware-reconnaissance-and-analysis/analysis/01-firmware-architecture-and-functionality-analysis.md — Comprehensive firmware analysis
- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/ttmp/2025/12/18/001-INITIAL-RECON--initial-firmware-reconnaissance-and-analysis/reference/01-diary.md — Research diary with step-by-step analysis


## 2025-12-18

Expanded analysis document with comprehensive technical explanations. Added detailed sections on: ESP32-S3 hardware capabilities, USB Video Class (UVC) protocol, TinyUSB implementation, camera sensor details, BMI270/BMM150 sensor fusion, NEC IR protocol, MJPEG streaming protocol, PSRAM memory management, design patterns (Singleton/Dependency Injection), extensive troubleshooting guide, and 'Getting Started for New Developers' section. All sections now include full prose paragraphs, bullet points, and guidance on where to find more information.

### Related Files

- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/ttmp/2025/12/18/001-INITIAL-RECON--initial-firmware-reconnaissance-and-analysis/analysis/01-firmware-architecture-and-functionality-analysis.md — Comprehensive firmware analysis with detailed technical explanations


## 2025-12-18

Diary updated with Step 14 (regression root-cause via ZIP compare: missing AsyncTCP/ESPAsyncWebServer/usb_device_uvc and cmake_utilities/gen_single_bin linkage) and Step 15 (restore ZIP sdkconfig+dependencies.lock to stop lock/config drift; GCC build succeeded; clang-toolchain reconfigure succeeded).

### Related Files

- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/components/usb_device_uvc/idf_component.yml — Declares cmake_utilities dependency
- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/dependencies.lock — Restored from ZIP baseline
- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/main/CMakeLists.txt — include(gen_single_bin) dependency explained
- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/managed_components/espressif__cmake_utilities/gen_single_bin.cmake — Provides gen_single_bin include
- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/sdkconfig — Restored from ZIP baseline
- /home/manuel/code/others/embedded/ATOMS3R-CAM-M12-UserDemo/ttmp/2025/12/18/001-INITIAL-RECON--initial-firmware-reconnaissance-and-analysis/reference/01-diary.md — Recorded full investigation and outcomes

