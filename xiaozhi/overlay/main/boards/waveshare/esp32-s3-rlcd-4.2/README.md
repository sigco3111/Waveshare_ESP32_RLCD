# Product Link

[Waveshare ESP32-S3-RLCD-4.2](https://www.waveshare.net/shop/ESP32-S3-RLCD-4.2.htm)

# Build Configuration Commands

**Clone the project**

```bash
git clone https://github.com/78/xiaozhi-esp32.git
```

**Enter the project**

```bash
cd xiaozhi-esp32
```

**Set the build target to ESP32S3**

```bash
idf.py set-target esp32s3
```

**Open menuconfig**

```bash
idf.py menuconfig
```

**Select the board**

```bash
Xiaozhi Assistant -> Board Type -> Waveshare ESP32-S3-RLCD-4.2
```

**Build**

```ba
idf.py build
```

**Flash and open the serial monitor**

```bash
idf.py build flash monitor
```

