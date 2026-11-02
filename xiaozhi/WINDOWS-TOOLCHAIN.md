# Windows Toolchain Notes

ESP-IDF 6.0.2, the ESP32-S3 compiler, and Git are required. Prefer the [general build steps](../docs/BUILD.md), executed in a PowerShell environment with official ESP-IDF activated.

The author's convenience scripts default to D:/syna-toolchains and try to locate Git from the author's Visual Studio directory; these are example layouts and do not mean Git is installed on your computer. Add Git to PATH and point SourceRoot / ToolchainRoot at your own ASCII paths. Do not copy someone else's Python virtual environment.

This open-source snapshot does not include the toolchain, upstream source, private configuration, or historical logs. The full build chain still needs acceptance testing in a clean Windows environment before the official release.
