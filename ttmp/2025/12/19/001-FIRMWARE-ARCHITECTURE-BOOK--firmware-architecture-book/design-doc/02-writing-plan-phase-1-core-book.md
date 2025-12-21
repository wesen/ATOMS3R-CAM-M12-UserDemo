---
Title: 'Writing Plan: Phase 1 Core Book'
Ticket: 001-FIRMWARE-ARCHITECTURE-BOOK
Status: active
Topics:
    - firmware
    - architecture
    - analysis
    - esp32
    - uvc
    - webserver
DocType: design-doc
Intent: long-term
Owners: []
RelatedFiles: []
ExternalSources: []
Summary: "Comprehensive writing plan for Phase 1 Core Book (Ch 1-9, 250 pages) with detailed TOC, research requirements, exercises, and diagrams"
LastUpdated: 2025-12-19T22:35:00.000000000-05:00
WhatFor: "Actionable plan to begin writing the book"
WhenToUse: "When starting to write any chapter or planning research/exercises"
---

# Writing Plan: Phase 1 Core Book

## Executive Summary

This document provides the complete writing plan for **Phase 1: Core Book** (Chapters 1-9, ~250 pages, 16 weeks).

**For each chapter, this plan specifies:**
- Detailed section outline with page budgets
- Content to write
- Research to conduct
- Exercises to develop (starter + solution code)
- Diagrams to create
- Source files to reference
- Dependencies and writing order

**Audience**: Senior embedded engineers who last programmed Cortex-M3 10 years ago

**Goal**: Get readers from "rusty CM3 knowledge" to "productive with M12 firmware and can extend it"

---

## Complete Table of Contents (Phase 1)

### PART 1: WELCOME BACK (~75 pages)

**Chapter 1: Cortex-M3 to ESP32-S3 Bridge** (30 pages)
- 1.1: Introduction: Welcome Back to Embedded
- 1.2: The Three Big Shifts
- 1.3: Architecture Comparison
- 1.4: Build System & Toolchain
- 1.5: What You'll Learn in This Book

**Chapter 2: ESP-IDF Essentials** (15 pages)
- 2.1: Track A - Quick Start (2 pages)
- 2.2: Track B - Component Architecture (4 pages)
- 2.3: Build System Deep Dive (4 pages)
- 2.4: Partition Tables & Flash Layout (3 pages)
- 2.5: Exercise: Port CM3 Project (2 pages)

**Chapter 3: M12 Annotated Walkthrough** (30 pages)
- 3.1: M12 System Overview
- 3.2: Initialization Sequence
- 3.3: Service Layer Walkthrough
- 3.4: API Layer Walkthrough
- 3.5: Exercises: Build, Test, Customize
- 3.6: What You Just Ran (Review Section)

### PART 2: UNDERSTANDING THE SYSTEM (~140 pages)

**Chapter 4: Thread Safety & SharedData** (20 pages)
- 4.1: Why Thread Safety Matters (CM3 vs ESP32)
- 4.2: Common Mistakes (Gotchas)
- 4.3: Mutex Patterns in FreeRTOS
- 4.4: SharedData Design & Implementation
- 4.5: Exercises: Race Conditions & Proper Locking
- 4.6: When NOT to Use SharedData

**Chapter 5: Real-Time USB & UVC Service** (25 pages)
- 5.1: USB on ESP32-S3 vs Cortex-M3
- 5.2: TinyUSB Architecture
- 5.3: UVC Callback Contracts
- 5.4: Frame Buffer Lifecycle
- 5.5: Service Mode Coordination
- 5.6: Exercises: Timing Measurement & Optimization
- 5.7: Soft Real-Time Reality Check

**Chapter 6: Memory Architecture** (15 pages)
- 6.1: ESP32-S3 Memory Model
- 6.2: IRAM, DRAM, PSRAM Fundamentals
- 6.3: Cache Implications
- 6.4: Memory Allocation Strategies
- 6.5: Exercises: Performance Analysis & IRAM_ATTR

**Chapter 7: I2C & Sensor Patterns** (22 pages)
- 7.1: I2C Fundamentals Refresher
- 7.2: M5Unified HAL Pattern
- 7.3: BMI270 Case Study (Vendor SDK Integration)
- 7.4: Sensor Data Flow (Hardware → SharedData → API)
- 7.5: Exercises: I2C Scanner, Add SHT31, Sensor Fusion
- 7.6: Hardware Abstraction Trade-offs

**Chapter 8: Async Web Patterns** (20 pages)
- 8.1: Sync vs Async (When Each Makes Sense)
- 8.2: ESPAsyncWebServer Architecture
- 8.3: Custom Response Classes
- 8.4: WebSocket Patterns
- 8.5: Exercises: Add Endpoints, WebSocket Control
- 8.6: Debugging Async Code

**Chapter 9: Advanced Memory & Asset Pool** (18 pages)
- 9.1: Flash Memory Mapping
- 9.2: Custom Partitions
- 9.3: Asset Pool Architecture
- 9.4: Asset Generation Pipeline
- 9.5: Exercises: Custom UI Assets, Data Logging Partition
- 9.6: When to Use Memory Mapping

### PART 4: REFERENCE APPENDICES (~30 pages)

**Appendix A**: CM3-to-ESP32 API Quick Reference (8 pages)
**Appendix B**: Threading Patterns Cheat Sheet (6 pages)
**Appendix C**: Troubleshooting Decision Tree (8 pages)
**Appendix D**: Hardware Reference (Pin Tables, Schematics) (8 pages)

**Total: ~265 pages** (includes some buffer)

---

## Chapter-by-Chapter Writing Plan

### Chapter 1: Cortex-M3 to ESP32-S3 Bridge (30 pages)

#### Page Budget
- 1.1 Introduction: 3 pages
- 1.2 Three Big Shifts: 8 pages
- 1.3 Architecture Comparison: 12 pages
- 1.4 Build System: 5 pages
- 1.5 What You'll Learn: 2 pages

#### What to Write

**1.1: Introduction (Emotional Hook)**
- Story: "2015: Your last embedded project. 2025: The world changed."
- Validation: Your CM3 knowledge is valuable
- Promise: This book bridges the gap
- Reading path guide

**1.2: The Three Big Shifts**
- **Shift 1: Bare Metal → Component Architecture**
  - Old: Monolithic firmware
  - New: ESP-IDF components
  - Why: Scalability, reusability
  
- **Shift 2: Simple Memory → Managed Memory**
  - Old: One address space
  - New: IRAM/DRAM/PSRAM split
  - Why: Performance optimization
  
- **Shift 3: Polling/Interrupts → Task/Event Architecture**
  - Old: Main loop + ISRs
  - New: FreeRTOS tasks + queues
  - Why: Complex systems need coordination

**1.3: Architecture Comparison (Side-by-Side Tables)**
- Processor architecture (ARM Cortex-M3 vs Xtensa LX7)
- Interrupt model (NVIC vs Xtensa)
- Memory layout
- Build system (Keil/GCC vs ESP-IDF/CMake)
- RTOS options (optional vs foundational)
- USB support (manual vs TinyUSB)

**1.4: Build System & Toolchain**
- CM3 toolchain: GCC ARM, Keil, IAR
- ESP32 toolchain: Xtensa GCC, ESP-IDF
- Build process comparison
- Flash programming differences

**1.5: What You'll Learn**
- Chapter summaries
- Prerequisites
- Time commitment (with optional paths)
- Hardware required

#### Research Required

**1. Cortex-M3 Specifics (Refresh)**
- [ ] Review ARM Cortex-M3 TRM (Technical Reference Manual)
- [ ] Document common CM3 development patterns circa 2014-2015
- [ ] List popular CM3 boards/IDEs from that era
- [ ] Identify assumptions CM3 developers carry

**2. Xtensa Architecture**
- [ ] Study Xtensa LX7 architecture overview
- [ ] Document key differences from ARM
- [ ] Understand interrupt priority model
- [ ] Windowed registers vs ARM registers

**3. ESP-IDF Build System**
- [ ] Trace complete build process (idf.py build)
- [ ] Document CMake flow
- [ ] Component manager operation
- [ ] Compare to typical CM3 Makefile flow

**4. Historical Context**
- [ ] What embedded books existed in 2015?
- [ ] What were common pain points?
- [ ] How has embedded development changed?

#### Diagrams to Create

**Diagram 1.1**: Timeline (2015 CM3 era → 2025 ESP32 era)
**Diagram 1.2**: Mental Model Shift (monolithic → components)
**Diagram 1.3**: Memory Architecture Comparison (CM3 vs ESP32-S3)
**Diagram 1.4**: Interrupt Flow (NVIC vs Xtensa)
**Diagram 1.5**: Build Process Comparison

#### Source Files Referenced

None (foundational chapter)

#### Dependencies

- Must be written first (foundational for all other chapters)
- No code dependencies

#### Exercises

None (pure comparison/foundation)

---

### Chapter 2: ESP-IDF Essentials (15 pages)

#### Page Budget
- 2.1 Track A (Quick Start): 2 pages
- 2.2 Track B (Components): 4 pages
- 2.3 Build System: 4 pages
- 2.4 Partition Tables: 3 pages
- 2.5 Exercise: 2 pages

#### What to Write

**2.1: Track A - Quick Start**
- Minimal commands to build/flash
- "If this works, skip to Chapter 3"
- Troubleshooting: "If not, read Track B"

**2.2: Track B - Component Architecture**
- What is a component?
- Component dependencies
- M12 component structure
- How components are discovered/built

**2.3: Build System Deep Dive**
- CMakeLists.txt structure
- Component registration
- Build output explained
- Kconfig system basics

**2.4: Partition Tables**
- Flash layout on ESP32-S3
- Partition types (bootloader, app, data, custom)
- M12 partition table walkthrough
- How to modify partitions

**2.5: Exercise - Port CM3 Project**
- Guided: UART echo (bare metal → ESP-IDF)
- Step-by-step conversion
- What changed and why

#### Research Required

**1. ESP-IDF Component System**
- [ ] Read ESP-IDF component documentation
- [ ] Trace component discovery during build
- [ ] Document component registration API
- [ ] List common component patterns

**2. Build Process Internals**
- [ ] Run idf.py build with verbose output
- [ ] Document CMake phases
- [ ] Understand Kconfig generation
- [ ] Trace how components are linked

**3. Partition System**
- [ ] Study partition table format (CSV)
- [ ] Document partition types and subtypes
- [ ] Understand partition tool (parttool.py)
- [ ] Review OTA partition scheme

**4. CM3 → ESP-IDF Migration**
- [ ] Create sample CM3 bare-metal UART code
- [ ] Convert to ESP-IDF step-by-step
- [ ] Document each change with rationale
- [ ] Test on hardware

#### Diagrams to Create

**Diagram 2.1**: Component Dependency Graph (M12 example)
**Diagram 2.2**: Build Process Flow (CMake → Ninja → Binary)
**Diagram 2.3**: Flash Layout (Partition Table Visual)
**Diagram 2.4**: CM3 vs ESP-IDF Code Structure

#### Source Files Referenced

- `CMakeLists.txt` (root)
- `main/CMakeLists.txt`
- `partitions.csv`
- Component `idf_component.yml` files

#### Exercises to Develop

**Exercise 2.1: Port CM3 UART Echo**
- **Starter code**: `ch02-port-project/cortex-m3-original/`
  - Bare metal UART echo (STM32F1 style)
  - ~50 lines, simple polling loop
  
- **Skeleton**: `ch02-port-project/esp32-starter/`
  - ESP-IDF project structure (empty main)
  - CMakeLists.txt templates
  - TODOs for porting

- **Solution**: `ch02-port-project/esp32-solution/`
  - Complete ESP-IDF version
  - Comments explaining each change

- **Time estimate**: 2 hours
- **Validates**: Build system, component structure, FreeRTOS basics

#### Dependencies

- Chapter 1 must be read first (assumes comparison knowledge)

---

### Chapter 3: M12 Annotated Walkthrough (30 pages)

#### Page Budget
- 3.1 System Overview: 4 pages
- 3.2 Initialization: 6 pages
- 3.3 Service Layer: 8 pages
- 3.4 API Layer: 6 pages
- 3.5 Exercises: 4 pages
- 3.6 Review: 2 pages

#### What to Write

**3.1: M12 System Overview**
- Block diagram of complete system
- Component interaction map
- Data flow at high level
- Service coordination overview

**3.2: Initialization Sequence**
- `app_main()` walkthrough
- Dependency injection pattern
- Hardware initialization order
- Why this sequence matters

**3.3: Service Layer Walkthrough**
- UVC service initialization
- Web server initialization
- Service mode coordination
- **Aggressive inline comments** (see Round 3 stress tests)

**3.4: API Layer Walkthrough**
- Camera API endpoints
- IMU WebSocket
- IR transceiver API
- Request/response flow

**3.5: Exercises**
1. Build and flash M12 base
2. Enable stress tests (timing, async)
3. Modify web UI text (asset pool practice)

**3.6: What You Just Ran (Review)**
- SharedData locking (5 times you saw it)
- UVC callbacks (4 different ones)
- Async handlers (3 patterns)
- "Chapter 4-8 explain these in detail"

#### Research Required

**1. M12 Codebase Deep Dive**
- [ ] Trace complete initialization from `app_main()`
- [ ] Document every component initialization
- [ ] Map all SharedData access points
- [ ] List all API endpoints with purpose

**2. Service Coordination**
- [ ] Analyze service mode transitions
- [ ] Document mutex usage patterns
- [ ] Identify potential race conditions
- [ ] Test failure scenarios

**3. Stress Test Design**
- [ ] Create timing stress test (blocking in UVC callback)
- [ ] Create async stress test (blocking in web handler)
- [ ] Verify failures are observable/educational
- [ ] Document expected failure modes

#### Diagrams to Create

**Diagram 3.1**: M12 System Block Diagram
**Diagram 3.2**: Initialization Sequence Diagram
**Diagram 3.3**: Service Mode State Machine
**Diagram 3.4**: Data Flow (Camera → USB/HTTP)
**Diagram 3.5**: API Endpoint Map

#### Source Files Referenced

- `main/usb_webcam_main.cpp` (complete walkthrough)
- `main/service/service_uvc.cpp`
- `main/service/service_web_server.cpp`
- `main/service/apis/*.cpp`
- `main/utils/shared/shared.h/cpp`

#### Exercises to Develop

**Exercise 3.1: Build and Flash M12** (30 min)
- **Source**: `ch03-m12-base/` (clean M12 firmware)
- **Tasks**:
  - Clone, build, flash
  - Connect via USB, verify UVC
  - Connect via WiFi, test web UI
- **Validates**: Build environment, hardware setup

**Exercise 3.2: Stress Tests** (30 min)
- **Modify**: Enable `#define TIMING_STRESS_TEST` in callbacks
- **Observe**: USB enumeration failure
- **Modify**: Enable async blocking test
- **Observe**: Web server hangs
- **Goal**: See constraints before deep dive

**Exercise 3.3: Customize UI** (1 hour)
- **Task**: Change web UI title text
- **Steps**:
  - Modify `main/utils/assets/images/index.html.gz` (decompress first)
  - Rebuild asset pool (`asset_pool_gen/`)
  - Flash asset pool partition
  - Verify changes
- **Validates**: Asset pool pipeline, partition flashing

#### Dependencies

- Requires Chapter 2 (build system knowledge)
- Provides base for all subsequent exercises

---

### Chapter 4: Thread Safety & SharedData (20 pages)

#### Page Budget
- 4.1 Why Thread Safety: 3 pages
- 4.2 Common Mistakes: 4 pages
- 4.3 Mutex Patterns: 4 pages
- 4.4 SharedData Implementation: 4 pages
- 4.5 Exercises: 4 pages
- 4.6 When NOT to Use: 1 page

#### What to Write

**4.1: Why Thread Safety Matters**
- CM3: `__disable_irq()` pattern
- ESP32: Dual-core + FreeRTOS → more complex
- Race conditions demonstrated
- Memory consistency model basics

**4.2: Common Mistakes (Gotchas from Marcus)**
- Using `GetData()` instead of `BorrowData()`
- Assumption: Interrupts are disabled
- Reality: Core 0 writes while Core 1 reads
- Debug screenshots showing corruption

**4.3: Mutex Patterns in FreeRTOS**
- Mutex vs semaphore vs critical section
- When to use each
- Deadlock prevention
- Lock ordering rules

**4.4: SharedData Design & Implementation**
- Singleton pattern explained
- `BorrowData()` / `ReturnData()` discipline
- Why this pattern for M12
- Performance implications

**4.5: Exercises (Gotchas → Education → Checklist)**
- Exercise 1: Find race condition bug
- Exercise 2: Add sensor data with proper locking
- Exercise 3: Deadlock prevention challenge

**4.6: When NOT to Use SharedData**
- High-frequency data (use queue)
- Large data transfers
- Producer-consumer patterns
- Event notification (use event groups)

#### Research Required

**1. FreeRTOS Synchronization**
- [ ] Study FreeRTOS mutex implementation
- [ ] Document API: `xSemaphoreTake/Give`, `xTaskNotify`, etc.
- [ ] Understand priority inheritance
- [ ] Research common deadlock patterns

**2. Dual-Core Memory Model**
- [ ] ESP32-S3 cache coherency protocol
- [ ] Memory barriers
- [ ] Atomic operations
- [ ] When manual synchronization is needed

**3. SharedData Pattern Analysis**
- [ ] Profile lock contention in M12
- [ ] Measure `BorrowData()` overhead
- [ ] Identify alternatives (message passing, lock-free)
- [ ] Document when pattern breaks down

**4. Race Condition Examples**
- [ ] Create reproducible race condition
- [ ] Make it visible (data corruption)
- [ ] Show fix with proper locking
- [ ] Stress test to verify fix

#### Diagrams to Create

**Diagram 4.1**: Race Condition Illustration (Timeline)
**Diagram 4.2**: Mutex State Machine
**Diagram 4.3**: SharedData Class Diagram
**Diagram 4.4**: Lock Ordering (Deadlock Prevention)
**Diagram 4.5**: Decision Tree (Which Sync Primitive?)

#### Source Files Referenced

- `main/utils/shared/shared.h` (complete)
- `main/utils/shared/shared.cpp`
- `main/utils/shared/types.h`

#### Exercises to Develop

**Exercise 4.1: Find the Race Condition** (30 min)
- **Buggy code**: Reads/writes SharedData without locking
- **Stress test**: Multiple tasks accessing simultaneously
- **Observable**: IMU data corruption, crashes
- **Fix**: Add proper `BorrowData()`/`ReturnData()`

**Exercise 4.2: Add Sensor Data** (1 hour)
- **Task**: Extend SharedData with new sensor
- **Requirements**: Follow BMI270 pattern, proper locking
- **Validates**: Understanding of SharedData discipline

**Exercise 4.3: Deadlock Prevention** (2 hours, Challenge)
- **Scenario**: Two tasks need SharedData + CameraMutex
- **Naive**: Deadlocks with different lock order
- **Fix**: Consistent lock ordering
- **Advanced**: Use `xSemaphoreTake` with timeout

#### Dependencies

- Chapter 3 (knows SharedData exists, has seen it used)
- Critical for Chapters 5-8 (all use SharedData)

---

### Chapter 5: Real-Time USB & UVC Service (25 pages)

#### Page Budget
- 5.1 USB Comparison: 4 pages
- 5.2 TinyUSB Architecture: 4 pages
- 5.3 UVC Callbacks: 5 pages
- 5.4 Frame Buffer Lifecycle: 4 pages
- 5.5 Service Mode: 3 pages
- 5.6 Exercises: 4 pages
- 5.7 Reality Check: 1 page

#### What to Write

**5.1: USB on ESP32-S3 vs Cortex-M3**
- CM3: Manual endpoint configuration, register access
- ESP32: TinyUSB abstraction, class drivers
- Timing constraints (1ms USB frames)
- Why callbacks exist

**5.2: TinyUSB Architecture**
- Device stack overview
- Class drivers (UVC, CDC, MSC, HID)
- Descriptor system
- Task model

**5.3: UVC Callback Contracts**
- `camera_start_cb()`: Resolution negotiation
- `camera_fb_get_cb()`: Timing-critical!
- `camera_fb_return_cb()`: Must return buffers
- `camera_stop_cb()`: Cleanup

**5.4: Frame Buffer Lifecycle**
- `esp_camera_fb_get()` allocates from PSRAM
- Buffer passed to TinyUSB
- MUST call `esp_camera_fb_return()`
- Leaks if not returned

**5.5: Service Mode Coordination**
- Why UVC and WebServer can't run simultaneously
- SharedData-based coordination
- Checking service mode in callbacks
- Graceful degradation

**5.6: Exercises**
- Measure callback timing
- Optimize frame rate
- Add custom UVC control (challenge)

**5.7: Soft Real-Time Reality**
- ESP32 is NOT hard real-time
- WiFi can preempt
- Design for variance, not guarantees

#### Research Required

**1. USB Protocol Fundamentals**
- [ ] Review USB 2.0 basics (frame structure, endpoints)
- [ ] UVC class specification overview
- [ ] Video formats and descriptors
- [ ] Isochronous vs bulk trade-offs

**2. TinyUSB Implementation**
- [ ] Study TinyUSB device stack
- [ ] Trace UVC class driver
- [ ] Document callback invocation points
- [ ] Understand task/interrupt split

**3. Timing Analysis**
- [ ] Measure callback timing with oscilloscope/logic analyzer
- [ ] Profile frame capture duration
- [ ] Measure JPEG encoding time by resolution
- [ ] Document worst-case timings

**4. Service Coordination**
- [ ] Trace service mode state machine
- [ ] Test race conditions (simultaneous UVC + web request)
- [ ] Verify mutex protection
- [ ] Document failure modes

#### Diagrams to Create

**Diagram 5.1**: USB Frame Timing (1ms frames)
**Diagram 5.2**: TinyUSB Architecture (stack layers)
**Diagram 5.3**: UVC Callback Sequence Diagram
**Diagram 5.4**: Frame Buffer Lifecycle (get → use → return)
**Diagram 5.5**: Service Mode State Machine

#### Source Files Referenced

- `main/service/service_uvc.cpp` (complete analysis)
- `components/usb_device_uvc/` (TinyUSB integration)
- `components/esp32-camera/` (frame capture)

#### Exercises to Develop

**Exercise 5.1: Measure Callback Timing** (30 min)
- **Instrument**: Add `esp_timer_get_time()` to callbacks
- **Collect**: 1000 frames of timing data
- **Analyze**: mean, p50, p95, p99, max
- **Goal**: Understand timing variance

**Exercise 5.2: Optimize Frame Rate** (2 hours)
- **Current**: Varies by resolution/quality
- **Task**: Experiment with quality settings, buffering
- **Measure**: fps, latency, frame drops
- **Document**: Trade-offs

**Exercise 5.3: Custom UVC Control** (4 hours, Challenge)
- **Add**: Brightness control via UVC extension unit
- **Requires**: Understanding UVC descriptors
- **Advanced**: Real-time host control

#### Dependencies

- Chapter 4 (SharedData locking)
- Chapter 3 (knows UVC service exists)

---

### Chapter 6: Memory Architecture (15 pages)

#### Page Budget
- 6.1 Memory Model: 4 pages
- 6.2 IRAM/DRAM/PSRAM: 4 pages
- 6.3 Cache: 3 pages
- 6.4 Allocation Strategies: 2 pages
- 6.5 Exercises: 2 pages

#### What to Write

**6.1: ESP32-S3 Memory Model**
- Unified vs split memory (CM3 comparison)
- Address spaces and regions
- Memory map diagram
- Access speeds

**6.2: IRAM, DRAM, PSRAM Fundamentals**
- IRAM: Fast, limited (192KB), for ISRs
- DRAM: General purpose (512KB)
- PSRAM: Large (8MB), slower, for buffers
- `IRAM_ATTR` attribute explained

**6.3: Cache Implications**
- L1 cache (instruction + data)
- Cache line size
- Cache misses cause stalls
- Flash XIP performance

**6.4: Memory Allocation Strategies**
- `malloc()` vs `heap_caps_malloc()`
- Specifying memory type (IRAM/PSRAM)
- Frame buffers in PSRAM
- When to use each

**6.5: Exercises**
- PSRAM vs SRAM performance benchmark
- Fix ISR crash (missing IRAM_ATTR)

#### Research Required

**1. ESP32-S3 Memory Architecture**
- [ ] Study Xtensa memory model
- [ ] Document address space layout
- [ ] Understand memory protection unit (MPU)
- [ ] Review cache architecture

**2. Performance Characteristics**
- [ ] Benchmark IRAM vs DRAM vs PSRAM access
- [ ] Measure cache hit/miss penalties
- [ ] Profile malloc performance by heap
- [ ] Document XIP vs RAM execution speed

**3. Common Pitfalls**
- [ ] ISR without IRAM_ATTR (crash)
- [ ] PSRAM access from ISR (crash)
- [ ] Frame buffer allocation strategies
- [ ] Heap exhaustion scenarios

#### Diagrams to Create

**Diagram 6.1**: ESP32-S3 Memory Map
**Diagram 6.2**: Cache Architecture
**Diagram 6.3**: Memory Access Speed Comparison (chart)

#### Source Files Referenced

- `main/usb_webcam_main.cpp` (IRAM_ATTR examples)
- `sdkconfig` (memory configuration)

#### Exercises to Develop

**Exercise 6.1: Memory Performance** (1 hour)
- **Benchmark framework provided**
- **Tasks**: Run tests on IRAM/DRAM/PSRAM
- **Measure**: Access latency, bandwidth
- **Analyze**: When to use each

**Exercise 6.2: Fix IRAM_ATTR Bug** (30 min)
- **Buggy ISR**: Crashes due to missing IRAM_ATTR
- **Debug**: Understand crash dump
- **Fix**: Add attribute, verify
- **Learn**: Why this is required

#### Dependencies

- Foundation for Chapter 7 (ISR in sensors)
- Referenced in Chapter 5 (frame buffers)

---

### Chapter 7: I2C & Sensor Patterns (22 pages)

#### Page Budget
- 7.1 I2C Fundamentals: 4 pages
- 7.2 M5Unified HAL: 4 pages
- 7.3 BMI270 Case Study: 5 pages
- 7.4 Sensor Data Flow: 3 pages
- 7.5 Exercises: 5 pages
- 7.6 Trade-offs: 1 page

#### What to Write

**7.1: I2C Fundamentals Refresher**
- Protocol basics (start, address, data, stop)
- Pull-ups and addressing
- Clock stretching
- ESP32 I2C quirks vs standard I2C

**7.2: M5Unified HAL Pattern**
- `I2C_Device` base class
- Why abstraction (board portability)
- How to debug through abstraction
- Direct ESP-IDF I2C comparison

**7.3: BMI270 Case Study**
- Three-layer architecture (vendor / HAL / wrapper)
- Vendor API integration pattern
- Two-stage init (BMI270 + BMM150 auxiliary)
- Data conversion (raw → engineering units)

**7.4: Sensor Data Flow**
- Hardware → I2C read → Vendor SDK → Wrapper
- Wrapper → SharedData (with locking!)
- SharedData → API → Client
- Complete pipeline diagram

**7.5: Exercises**
- I2C scanner (both ways: ESP-IDF + M5Unified)
- Add SHT31 sensor (full guided example from Round 3)
- Sensor fusion with IMU
- Add sensor of your choice (challenge)

**7.6: Hardware Abstraction Trade-offs**
- Pros: Portability, convenience
- Cons: Debugging complexity, lock-in
- When to use direct HAL

#### Research Required

**1. I2C Protocol Details**
- [ ] Review I2C specification
- [ ] Document ESP32-S3 I2C peripheral
- [ ] Test I2C scanner on hardware
- [ ] Identify common failure modes (pullups, addressing)

**2. M5Unified I2C Implementation**
- [ ] Study `m5::I2C_Class` source
- [ ] Document `I2C_Device` base class
- [ ] Trace read/write operations
- [ ] Compare to ESP-IDF i2c_master_* API

**3. Sensor Integration**
- [ ] Review BMI270 datasheet
- [ ] Study Bosch vendor SDK
- [ ] Document init sequence
- [ ] Test BMM150 auxiliary sensor init

**4. SHT31 Integration**
- [ ] Obtain SHT31 sensor
- [ ] Wire to M12 hardware
- [ ] Download Sensirion SDK
- [ ] Create complete working example
- [ ] Test on hardware

#### Diagrams to Create

**Diagram 7.1**: I2C Protocol (waveform)
**Diagram 7.2**: M5Unified I2C Class Hierarchy
**Diagram 7.3**: BMI270 Three-Layer Architecture
**Diagram 7.4**: Sensor Data Flow (end-to-end)
**Diagram 7.5**: SHT31 Wiring Diagram

#### Source Files Referenced

- `main/utils/bmi270/src/bmi270.h/cpp`
- `main/utils/bmi270/src/utilities/BMI270-Sensor-API/`
- `main/utils/bmi270/src/utilities/BMM150-Sensor-API/`
- `components/M5Unified/` (I2C HAL)

#### Exercises to Develop

**Exercise 7.1: I2C Scanner** (20 min)
- **Two versions**: ESP-IDF API + M5Unified
- **Compare**: Code complexity, clarity
- **Validates**: I2C wiring, pullups, device detection

**Exercise 7.2: Add SHT31 Sensor** (1 hour, GUIDED)
- **Complete from Round 3 sample**
- Wiring + SDK + SharedData + API
- Fully documented starter + solution

**Exercise 7.3: Sensor Fusion** (2-3 hours)
- **Combine**: Accel + Gyro + Mag
- **Calculate**: Roll, pitch, yaw
- **Expose**: 3D visualization via web API
- **Bonus**: Kalman filter

**Exercise 7.4: Your Choice** (Challenge)
- **Pick any I2C sensor**
- **Integrate** following SHT31 pattern
- **Document** what you learned

#### Dependencies

- Chapter 4 (SharedData locking)
- Chapter 6 (IRAM for ISRs if added)
- Chapter 3 (knows BMI270 exists)

---

### Chapter 8: Async Web Patterns (20 pages)

#### Page Budget
- 8.1 Sync vs Async: 3 pages
- 8.2 ESPAsyncWebServer: 4 pages
- 8.3 Custom Response Classes: 5 pages
- 8.4 WebSocket: 4 pages
- 8.5 Exercises: 3 pages
- 8.6 Debugging: 1 page

#### What to Write

**8.1: Sync vs Async (When Each Makes Sense)**
- Synchronous: Simple, blocking, okay for low-frequency
- Asynchronous: Complex, non-blocking, required for high-frequency
- Decision tree: When do you need async?
- Event loop mental model

**8.2: ESPAsyncWebServer Architecture**
- Event-driven server
- Request → Handler → Response flow
- Async task model
- Memory management (who owns what?)

**8.3: Custom Response Classes**
- Why they exist (streaming without blocking)
- `AsyncBufferResponse`
- `AsyncFrameResponse`
- `AsyncJpegStreamResponse` (MJPEG complexity)
- Lifetime management

**8.4: WebSocket Patterns**
- Connection lifecycle
- Daemon task pattern (IMU example)
- Broadcast vs unicast
- Connection cleanup

**8.5: Exercises**
- Add simple sync endpoint
- Add async sensor data fetch
- WebSocket camera control
- Rate limiting (challenge)

**8.6: Debugging Async Code**
- Common mistakes (blocking in handler)
- Symptoms and fixes
- Debugging event loop issues

#### Research Required

**1. ESPAsyncWebServer Internals**
- [ ] Study library source code
- [ ] Trace request handling
- [ ] Document event loop
- [ ] Understand AsyncTCP integration

**2. Response Class Patterns**
- [ ] Analyze AsyncJpegStreamResponse implementation
- [ ] Understand chunked transfer encoding
- [ ] Document memory ownership rules
- [ ] Test memory leaks

**3. WebSocket Implementation**
- [ ] Study AsyncWebSocket class
- [ ] Document connection management
- [ ] Trace daemon task pattern
- [ ] Test multiple concurrent clients

**4. Performance Testing**
- [ ] Load test with multiple clients
- [ ] Measure throughput
- [ ] Identify bottlenecks
- [ ] Test failure modes

#### Diagrams to Create

**Diagram 8.1**: Sync vs Async Request Flow
**Diagram 8.2**: Event Loop Architecture
**Diagram 8.3**: Custom Response Class Lifecycle
**Diagram 8.4**: WebSocket Connection Lifecycle
**Diagram 8.5**: IMU WebSocket Data Flow

#### Source Files Referenced

- `main/service/service_web_server.cpp`
- `main/service/apis/api_camera.cpp` (async responses)
- `main/service/apis/api_imu.cpp` (WebSocket)
- `components/ESPAsyncWebServer/`

#### Exercises to Develop

**Exercise 8.1: Simple Sync Endpoint** (15 min)
- **Add**: `/api/v1/status` returning system info
- **Template provided**, fill in blanks
- **Easy win**, builds confidence

**Exercise 8.2: Async Sensor Fetch** (45 min)
- **Challenge**: I2C read blocks, can't block event loop
- **Solution**: Offload to FreeRTOS task, respond async
- **Pattern**: Queue-based task communication

**Exercise 8.3: WebSocket Control** (2 hours)
- **Add**: WebSocket for real-time camera control
- **Client sends**: `{"resolution": "VGA"}`
- **Camera updates**: Resolution changes
- **Challenge**: Concurrent clients, race conditions

**Exercise 8.4: Rate Limiting** (Challenge)
- **Implement**: Rate limiter per-client
- **Prevent**: DOS via rapid requests
- **Learn**: Production-level concerns

#### Dependencies

- Chapter 3 (knows web server exists)
- Chapter 4 (SharedData locking for async handlers)

---

### Chapter 9: Advanced Memory & Asset Pool (18 pages)

#### Page Budget
- 9.1 Flash Memory Mapping: 4 pages
- 9.2 Custom Partitions: 4 pages
- 9.3 Asset Pool Architecture: 4 pages
- 9.4 Asset Pipeline: 3 pages
- 9.5 Exercises: 3 pages

#### What to Write

**9.1: Flash Memory Mapping**
- Memory-mapped flash on ESP32-S3
- `esp_partition_mmap()` API
- Zero-copy reads from flash
- Performance implications (cache)

**9.2: Custom Partitions**
- Partition table format
- Types and subtypes
- How to add custom partition
- Flashing separate partitions

**9.3: Asset Pool Architecture**
- Why M12 uses memory mapping
- 234KB of web assets, 0KB RAM used
- `StaticAsset_t` structure
- Injection pattern

**9.4: Asset Generation Pipeline**
- `asset_pool_gen/` tool
- Desktop build creates binary
- `parttool.py` flashes to custom partition
- Complete workflow

**9.5: Exercises**
- Add custom image to web UI
- Create data logging partition

#### Research Required

**1. Flash Memory Mapping**
- [ ] Study ESP32-S3 flash controller
- [ ] Document `esp_partition_mmap()` API
- [ ] Measure read performance (cached vs uncached)
- [ ] Understand MMU translation

**2. Partition System**
- [ ] Review partition table generator
- [ ] Document partition types (app, data, custom)
- [ ] Test custom partition creation
- [ ] Verify flash tool operation

**3. Asset Pool Implementation**
- [ ] Trace asset pool initialization
- [ ] Study `asset_pool_gen` build tool
- [ ] Document binary format
- [ ] Test asset updates

#### Diagrams to Create

**Diagram 9.1**: Memory-Mapped Flash Architecture
**Diagram 9.2**: Partition Table Layout (M12 example)
**Diagram 9.3**: Asset Generation Pipeline
**Diagram 9.4**: Asset Pool Memory Map

#### Source Files Referenced

- `main/utils/assets/assets.h/cpp`
- `partitions.csv`
- `asset_pool_gen/main.cpp`
- `upload_asset_pool.sh`

#### Exercises to Develop

**Exercise 9.1: Add Custom Image** (1 hour)
- **Task**: Add logo to web UI
- **Steps**:
  - Add image file to `assets/images/`
  - Rebuild asset pool
  - Flash asset partition
  - Update HTML to reference image
- **Validates**: Complete asset pipeline

**Exercise 9.2: Data Logging Partition** (2 hours)
- **Create**: Custom partition for logging
- **Implement**: Write/read log entries
- **Add**: Web API to download logs
- **Learn**: Custom partition patterns

#### Dependencies

- Chapter 2 (partition tables)
- Chapter 3 (knows asset pool exists)

---

## Appendix Writing Plan

### Appendix A: CM3-to-ESP32 API Quick Reference (8 pages)

**Format**: Side-by-side comparison tables

**Sections**:
- GPIO operations
- UART operations
- I2C operations
- Timers
- Interrupts
- Memory operations
- Common peripherals

**Research**:
- [ ] Document common CM3 HAL functions (STM32 HAL, CMSIS)
- [ ] Map to ESP-IDF equivalents
- [ ] Include code examples

### Appendix B: Threading Patterns Cheat Sheet (6 pages)

**Content**:
- Mutex usage patterns
- Queue patterns
- Semaphore patterns
- Event groups
- Task notifications
- When to use each

**Format**: Quick reference with code snippets

### Appendix C: Troubleshooting Decision Tree (8 pages)

**Common Issues**:
- Build failures
- Flash failures
- Runtime crashes
- USB enumeration failures
- I2C communication failures
- WebSocket disconnects

**Format**: Flowchart-style decision trees

### Appendix D: Hardware Reference (8 pages)

**Content**:
- M12 pin table
- I2C device addresses
- Power supply specifications
- Schematic excerpts
- Hardware modifications

**Format**: Tables and diagrams

---

## Development Requirements

### Code Repository Setup

**Structure** (from Round 3):
```
M12-Firmware-Book/
├── README.md
├── hardware/
│   ├── schematic.pdf
│   ├── wiring-diagrams/
├── common/
│   ├── components/
│   └── tools/
├── ch02-hello-idf/
│   ├── cortex-m3-original/
│   ├── esp32-starter/
│   └── esp32-solution/
├── ch03-m12-base/
├── ch04-thread-safety/
│   ├── ex01-race-bug/
│   ├── ex02-add-sensor/
│   └── ex03-deadlock/
├── ch05-realtime-usb/
├── ch06-memory/
├── ch07-sensors/
├── ch08-async-web/
├── ch09-advanced-memory/
└── tests/
```

**Setup Tasks**:
- [ ] Create repository structure
- [ ] Set up CI for testing exercises
- [ ] Create exercise templates
- [ ] Document repo README

### Hardware Required

**For Writing/Testing**:
- [ ] M5Stack AtomS3R-M12 board (x2 for testing)
- [ ] SHT31 temperature/humidity sensor
- [ ] BME280 (alternative sensor for exercises)
- [ ] Logic analyzer (for I2C/USB debugging)
- [ ] USB cable, breadboard, jumpers

### Tool Setup

**Required**:
- [ ] ESP-IDF v5.1.4 installed
- [ ] Python 3.8+ with ESP-IDF tools
- [ ] Git with submodules
- [ ] LaTeX/Pandoc for book formatting
- [ ] Diagram tool (draw.io, PlantUML, or similar)

---

## Writing Order and Dependencies

### Critical Path

**Week 1-2: Foundation**
1. Chapter 1 (no dependencies)
2. Chapter 2 (depends on Ch 1)
3. Setup code repository

**Week 3-4: Base System**
4. Chapter 3 (depends on Ch 1-2, provides base for all)
5. Develop ch03-m12-base code

**Week 5-6: Core Patterns**
6. Chapter 4 (depends on Ch 3, critical for rest)
7. Chapter 6 (can be parallel to Ch 4)

**Week 7-10: Services**
8. Chapter 5 (depends on Ch 3-4)
9. Chapter 7 (depends on Ch 4, 6)
10. Chapter 8 (depends on Ch 3-4)

**Week 11-12: Advanced**
11. Chapter 9 (depends on Ch 2-3)

**Week 13-14: Polish**
12. Appendices
13. Technical review
14. Exercise testing on hardware

**Week 15-16: Final**
15. Editing pass
16. Diagram finalization
17. Index, TOC, etc.

---

## Checklist Per Chapter

**Before Writing**:
- [ ] Complete research tasks
- [ ] Develop exercises (starter + solution)
- [ ] Test exercises on hardware
- [ ] Create diagrams (rough drafts)

**While Writing**:
- [ ] Follow page budget
- [ ] Include "CM3 Refugee Warning" boxes (2-3 per chapter)
- [ ] Add code examples with aggressive commenting
- [ ] Reference source files with line numbers
- [ ] Link to exercises at appropriate points

**After Writing**:
- [ ] Technical review by CM3 veteran
- [ ] Test all exercises work as documented
- [ ] Verify all diagrams are accurate
- [ ] Polish diagrams for publication
- [ ] Add to CI test suite

---

## Success Metrics

**Per Chapter**:
- [ ] All exercises tested on hardware
- [ ] 2-3 beta readers complete successfully
- [ ] Average completion time matches estimates
- [ ] Technical accuracy verified

**Overall**:
- [ ] Phase 1 complete in 16 weeks
- [ ] All 25 exercises working
- [ ] ~250 pages core content
- [ ] Ready for Phase 2 or publication

---

## Risk Mitigation Reminders

**From Round 4**:

1. **Version Pin Everything**
   - ESP-IDF v5.1.4
   - Document exact component versions
   - Create migration guides as needed

2. **Hardware Alternatives**
   - Document 2-3 sensor options
   - Test primary + one alternative

3. **Support Boundaries**
   - Clear SUPPORT.md in repo
   - Code disclaimers
   - MIT + Apache license

4. **Pattern Alternatives**
   - "When NOT to use" sections
   - Decision matrices
   - Multiple approaches shown

---

## Next Session Action Items

**To Begin Writing**:

1. **Start with Chapter 1**
   - Most foundational
   - No code dependencies
   - Sets tone for book

2. **Parallel: Set Up Repo**
   - Create ch03-m12-base
   - Test build/flash workflow
   - Document setup

3. **Hardware Prep**
   - Verify M12 board works
   - Test sensors
   - Validate I2C connections

4. **First Week Goal**
   - Chapter 1 draft complete
   - Code repo initialized
   - Hardware validated

**Files to Have Open**:
- This writing plan
- Chapter 1 outline
- M12 firmware analysis document
- Debate Round 1-4 (for reference)

---

**Ready to write!** 📝
