---
Title: clangd Setup for Cursor
Ticket: 001-INITIAL-RECON
Status: active
Topics:
    - firmware
    - esp32
    - analysis
DocType: playbook
Intent: long-term
Owners: []
RelatedFiles: []
ExternalSources: []
Summary: Step-by-step playbook for configuring clangd IntelliSense in Cursor IDE for ESP-IDF development using ESP-clang toolchain
LastUpdated: 2025-12-18T09:00:35.993496876-05:00
---


# clangd Setup for Cursor

## Purpose

Configure clangd (via Cursor's Anysphere C/C++ extension) for ESP-IDF development to enable accurate symbol resolution, autocomplete, and go-to-definition for C/C++ code in the AtomS3R-M12 firmware project.

## Environment Assumptions

- ESP-IDF v5.1.4 or later installed and configured
- Cursor IDE installed
- ESP-IDF environment sourced: `source $IDF_PATH/export.sh`
- Project already cloned and dependencies fetched (`python ./fetch_repos.py`)
- Write access to project root directory

## Commands

### Step 1: Install ESP-clang Toolchain

ESP-clang provides a clang-based toolchain that generates better `compile_commands.json` for clangd:

```bash
idf_tools.py install esp-clang
```

**Expected output**: Toolchain downloads and installs to `~/.espressif/tools/esp-clang/`

### Step 2: Configure Build with ESP-clang

Create a separate build directory using the clang toolchain for IntelliSense (not for actual firmware builds):

```bash
idf.py -B build.clang -D IDF_TOOLCHAIN=clang reconfigure
```

**Expected output**: 
- Creates `build.clang/` directory
- Generates `build.clang/compile_commands.json` optimized for clang-based tools
- Build configuration completes successfully

**Note**: This build directory is only for code analysis. Use `idf.py build` (GCC) for actual firmware builds.

### Step 3: Create .clangd Configuration

Create `.clangd` file in project root:

```bash
cat > .clangd << 'EOF'
CompileFlags:
  CompilationDatabase: build.clang/
EOF
```

**Verify**:
```bash
cat .clangd
```

Should show:
```
CompileFlags:
  CompilationDatabase: build.clang/
```

### Step 4: Configure Cursor Settings

Create `.vscode/settings.json`:

```bash
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
    "C_Cpp.intelliSenseEngine": "disabled",
    "clangd.path": "/home/manuel/.espressif/tools/esp-clang/15.0.0-23786128ae/esp-clang/bin/clangd",
    "files.associations": {
        "*.h": "c",
        "*.hpp": "cpp",
        "*.c": "c",
        "*.cpp": "cpp",
        "sdkconfig": "properties",
        "Kconfig*": "kconfig",
        "*.cmake": "cmake",
        "CMakeLists.txt": "cmake"
    },
    "files.watcherExclude": {
        "**/build/**": true,
        "**/build.clang/**": true,
        "**/.git/**": true,
        "**/managed_components/**": true
    },
    "search.exclude": {
        "**/build": true,
        "**/build.clang": true,
        "**/managed_components": true,
        "**/.git": true
    }
}
EOF
```

**Important**: Update `clangd.path` to match your ESP-clang installation:

```bash
find ~/.espressif/tools/esp-clang -name clangd -type f
```

Update the path in `.vscode/settings.json` accordingly.

### Step 5: Restart clangd in Cursor

1. Open Command Palette: `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
2. Type: "clangd: Restart language server"
3. Press Enter

**Alternative**: Reload Cursor window: `Ctrl+Shift+P` → "Developer: Reload Window"

## Exit Criteria

### Success Indicators

1. **clangd is running**:
   - Open Output panel: `Ctrl+Shift+U`
   - Select "clangd" from dropdown
   - Should see clangd startup messages, no errors

2. **Symbol resolution works**:
   - Open `main/usb_webcam_main.cpp`
   - Hover over `esp_camera_init` - should show tooltip with definition
   - Press `F12` on symbol - should navigate to definition
   - Autocomplete works when typing function names

3. **No IntelliSense errors**:
   - ESP-IDF symbols (e.g., `ESP_LOGI`, `esp_err_t`) resolve correctly
   - Standard library symbols resolve correctly
   - No red squiggles on valid ESP-IDF code

### Verification Commands

```bash
# Verify compile_commands.json exists and is non-empty
ls -lh build.clang/compile_commands.json

# Verify .clangd configuration
cat .clangd

# Verify settings.json exists
cat .vscode/settings.json

# Check clangd path exists
test -f ~/.espressif/tools/esp-clang/*/esp-clang/bin/clangd && echo "clangd found" || echo "clangd not found"
```

## Notes

### Why ESP-clang?

- **Better compatibility**: clangd understands clang-generated `compile_commands.json` better than GCC-generated ones
- **Accurate flags**: ESP-clang generates flags that clangd can parse correctly
- **No manual configuration**: No need to manually add include paths or compiler flags
- **ESP-IDF optimized**: Designed specifically for ESP-IDF projects

### Build Directories

- **`build.clang/`**: Used only for IntelliSense (clang-based)
- **`build/`**: Used for actual firmware builds (GCC-based)

Always use `idf.py build` for firmware builds. The `build.clang/` directory is only for code analysis.

### Troubleshooting

**Symbols not resolving?**
1. Regenerate: `idf.py -B build.clang -D IDF_TOOLCHAIN=clang reconfigure`
2. Verify `.clangd` contains: `CompilationDatabase: build.clang/`
3. Restart clangd: `Ctrl+Shift+P` → "clangd: Restart language server"

**clangd path not found?**
- Find correct path: `find ~/.espressif/tools/esp-clang -name clangd -type f`
- Update `.vscode/settings.json` with correct path

**Still having issues?**
- Check clangd output: `Ctrl+Shift+U` → "clangd" → look for errors
- Verify ESP-IDF environment: `echo $IDF_PATH`
- Check `compile_commands.json` exists and is non-empty

### Files Created

- `.clangd` - clangd configuration (points to `build.clang/`)
- `.vscode/settings.json` - Cursor workspace settings

### Related Documentation

- ESP-IDF Programming Guide: https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/
- clangd Documentation: https://clangd.llvm.org/
