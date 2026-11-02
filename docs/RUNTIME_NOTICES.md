# Windows Bundled Runtime Notes

This record covers the 2026-09-16 independent build; not all software installed on the build machine is treated as a program dependency.

## Software OpenGL

PyInstaller automatically collects PySide6's `opengl32sw.dll`. The actual DLL contains Mesa 11.2.2 and LLVM 3.6.2 strings; Qt documentation confirms that file is the llvmpipe software OpenGL implementation. The source package and original license are provided with the candidate package; this does not mean vendor patches have already been independently rebuilt or verified.

Source: https://doc.qt.io/qt-6.8/windows-graphics.html and https://wiki.qt.io/MesaLlvmpipe .

## OpenSSL

The CPython 3.11.0 environment reports OpenSSL 1.1.1q; the packaging manifest includes libssl-1_1.dll / libcrypto-1_1.dll. The corresponding original license is retained and the upstream 1.1.1q source package is provided. The cryptography package additionally retains its own license; CPython's OpenSSL version cannot substitute for the versions of all statically linked dependencies.

## Microsoft VC Runtime

Microsoft VC Runtime DLLs are present in the final manifest. They are not MIT/Qt open-source code and are not listed as source that can be arbitrarily re-licensed. Microsoft associates VC Runtime redistribution with the applicable Visual Studio / software license terms.

Source: https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170 .

This record's file versions, source path types, and hashes are for traceability; the publisher's Visual Studio authorization status is not automatically confirmed. Before release the author must verify their applicable license and the list of files allowed for distribution. The item cannot be marked authorized merely because Visual Studio is installed on the build machine or the DLL is downloadable.

## Conservative Collection

Qt module source includes tests, examples, and platform implementations, so notice collection takes a conservative scope. The presence of a license in the materials does not mean that component is necessarily linked into the actual EXE; rely on the actual binary manifest and the specific implementation.
