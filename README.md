# AtomS3R-M12 User Demo

User demo source code of AtomS3R-M12

## Build

### Fetch Dependencies

Initialize and update Git submodules:

```bash
git submodule update --init --recursive
```

Or clone the repository with submodules:

```bash
git clone --recursive <repository-url>
```

### Tool Chains

[ESP-IDF v5.1.4](https://docs.espressif.com/projects/esp-idf/en/v5.1.4/esp32s3/index.html)

### Build

```bash
idf.py build
```

### Flash

```bash
idf.py -p <YourPort> flash -b 1500000
```

#### Flash AssetPool

```bash
parttool.py --port <YourPort> write_partition --partition-name=assetpool --input "asset_pool_gen/output/AssetPool.bin"
```
