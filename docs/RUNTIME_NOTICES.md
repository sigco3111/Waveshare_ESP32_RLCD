# Windows 번들 런타임 안내

이 기록은 2026-09-16 독립 빌드를 다룹니다. 빌드 기기에 설치된 모든 소프트웨어를 프로그램 의존성으로 간주하지 않습니다.

## 소프트웨어 OpenGL

PyInstaller는 PySide6의 `opengl32sw.dll`을 자동으로 수집합니다. 실제 DLL에는 Mesa 11.2.2와 LLVM 3.6.2 문자열이 들어 있으며, Qt 문서에 따르면 해당 파일은 llvmpipe 소프트웨어 OpenGL 구현입니다. 소스 패키지와 원래 라이선스는 후보 패키지와 함께 제공됩니다. 벤더 패치를 이미 독립적으로 재빌드하거나 검증했다는 뜻은 아닙니다.

출처: https://doc.qt.io/qt-6.8/windows-graphics.html 및 https://wiki.qt.io/MesaLlvmpipe .

## OpenSSL

CPython 3.11.0 환경은 OpenSSL 1.1.1q를 보고하며, 패키징 매니페스트에는 libssl-1_1.dll / libcrypto-1_1.dll이 포함됩니다. 대응하는 원래 라이선스를 유지하고 업스트림 1.1.1q 소스 패키지를 제공합니다. cryptography 패키지는 자체 라이선스도 별도로 유지합니다. CPython의 OpenSSL 버전이 정적 링크된 모든 의존성의 버전을 대체할 수 없습니다.

## Microsoft VC 런타임

최종 매니페스트에 Microsoft VC 런타임 DLL이 있습니다. MIT/Qt 오픈소스 코드가 아니며, 임의로 재라이선스할 수 있는 소스로 기재하지 않습니다. Microsoft는 VC 런타임 재배포를 적용 가능한 Visual Studio / 소프트웨어 라이선스 조건과 연결합니다.

출처: https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170 .

이 기록의 파일 버전, 소스 경로 형식, 해시는 추적용입니다. 배포자의 Visual Studio 승인 상태가 자동으로 확인되는 것은 아닙니다. 릴리스 전에는 작성자가 적용 가능한 라이선스와 배포 허용 파일 목록을 검증해야 합니다. 빌드 기기에 Visual Studio가 설치되어 있거나 DLL을 다운로드할 수 있다는 이유만으로 승인된 것으로 표시할 수 없습니다.

## 보수적 수집

Qt 모듈 소스에는 테스트, 예제, 플랫폼 구현이 포함되므로, 고지 수집은 보수적 범위로 수행합니다. 자료에 라이선스가 있다고 해서 해당 컴포넌트가 실제 EXE에 반드시 링크된다는 뜻은 아닙니다. 실제 바이너리 매니페스트와 구체적인 구현을 기준으로 하세요.
