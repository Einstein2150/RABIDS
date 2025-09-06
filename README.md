## Overview

**RABIDS** (Roving Autonomous Bartmoss Interface Drones) is for building custom malware payloads. It allows you to chain together various modules—such as ransomware, clipboard hijackers, and persistence loaders—into a single, compiled executable for Windows, Linux, or macOS.

This tool is designed for security researchers, red teamers, and educational purposes to simulate advanced adversaries and study malware behavior in a controlled environment.

## Quick Start

1.  **Install GUI Dependency:**

    The user interface requires `PyQt5`. Install it using pip:

    ```bash
    pip install PyQt5
    ```

2.  **Run the Application:**
    ```bash
    python3 main.py
    ```

## Features

- **Modular Payload Creation:** Chain multiple modules together to create sophisticated, multi-stage payloads.
- **Cross-Platform Compilation:** Build executables for Windows, Linux, and macOS with support for `amd64` and `arm64` architectures.
- **Optional Obfuscation:** Leverage a Dockerized Obfuscator-LLVM toolchain to apply advanced obfuscation techniques to Windows payloads.
- **Intuitive Graphical User Interface:** A clean and modern UI makes it easy to select modules, configure options, and build payloads without writing any code.
- **Standalone Tooling:** Includes dedicated tabs for building a file decryptor (`UNKRASH`) and a file restorer (`Garbage Collector`).

## Available Modules

- **`ctrlvamp`**: Hijacks clipboard crypto addresses (BTC, ETH, BEP-20, SOL).
- **`dumpster`**: Collects files from a directory and archives them into a single file.
- **`ghostintheshell`**: Provides a reverse shell over Discord for remote access.
- **`krash`**: Encrypts files in target directories and displays a ransom note.
- **`poof`**: Recursively deletes all files and folders from a target directory.
- **`undeleteme`**: Gains persistence and can add a Windows Defender exclusion.

## Documentation & Setup

All documentation, including installation instructions, setup guides, and detailed module descriptions, can be found within the application itself under the **"DOCUMENTATION" tab**.

This in-app guide provides everything you need to know to:

- Install dependencies (Python, Nim, Rust, Docker).
- Configure build options.
- Understand each module and its parameters.
- Build and find your payloads.

## Legal Disclaimer

This tool is intended for **educational purposes, authorized security testing, and red team operations only**. The author is not responsible for any misuse, damage, or legal consequences that may result from the use of this software. You must have explicit, written permission from the target system's owner before using this tool. Unauthorized use is strictly prohibited and may be illegal.

## License

MIT License. See the `LICENSE` file for details.
