# RABIDS

This document provides a detailed overview of each module available in the RABIDS graphical user interface, including its purpose and configurable options.

---

## Installation and Setup

Before running RABIDS, you need to install several dependencies for Python, Nim, and Rust. The obfuscation feature also requires Docker.

### 1. Python Dependencies

The GUI is built with PyQt5. Install it using pip:

```bash
pip install PyQt5
```

### 2. Nim and Nimble Packages

The core payload modules are written in Nim.

- **Install Nim:** Follow the official instructions at [nim-lang.org/install](https://nim-lang.org/install.html).

- **Install Nimble Packages:** The modules require several external packages. Install them using the `nimble` command:

  ```bash
  nimble install winim openssl discord nimcrypto clipb
  ```

### 3. Rust Environment

RABIDS uses a Rust wrapper for in-memory execution and obfuscation on Windows targets.

- **Install Rust:** Follow the official instructions at rust-lang.org/tools/install.

- **Install Cross-Compilation Targets:** To build for different architectures, you need to add the corresponding targets via `rustup`:

  ```bash
  # For Windows 64-bit (amd64)
  rustup target add x86_64-pc-windows-gnu

  # For Windows 64-bit (arm64)
  rustup target add aarch64-pc-windows-gnu
  ```

### 4. Docker (for Obfuscation)

The payload obfuscation feature uses a Docker container with a pre-built Obfuscator-LLVM toolchain.

- **Install Docker:** Get Docker Desktop from the official Docker website.

- **Pull the Obfuscator Image:** Download the required Docker image from the GitHub Container Registry:

  ```bash
  docker pull ghcr.io/joaovarelas/obfuscator-llvm-16.0:latest
  ```

---

## Important: Module Chaining Order

When building a payload with multiple modules, the order in which you add them matters. Modules are executed sequentially in the order they appear in the "MODULE CHAIN".

Some modules, like `ctrlvamp` and `ghostintheshell`, are **"blocking"**. This means they run in a continuous loop (e.g., to monitor the clipboard or wait for commands) and will prevent any subsequent modules in the chain from executing.

**Therefore, you should always place blocking modules at the end of your module chain.**

For example, if you want to gain persistence (`undeleteme`) and then start a reverse shell (`ghostintheshell`), the correct order is:

1.  `undeleteme`
2.  `ghostintheshell`

If you place `ghostintheshell` first, the `undeleteme` module will never run.

**Blocking Modules:**

- `ctrlvamp`
- `ghostintheshell`

---

## Module: `ctrlvamp`

**Description:**
Hijacks the system's clipboard to replace cryptocurrency wallet addresses. When a user copies a wallet address, this module swaps it with an address you control, redirecting payments.

**How it works:**
The payload continuously monitors the clipboard. It uses regular expressions to detect patterns matching various cryptocurrency addresses. When a match is found, it replaces the clipboard content with the corresponding address provided in the options.

**Options:**

- `btcAddress`: Your Bitcoin (BTC) address that will replace any BTC address copied by the victim.
- `ethAddress`: Your Ethereum (ETH) or EVM-compatible address that will replace any matching address copied by the victim.
- `bep20Address`: Your Binance Smart Chain (BEP-20) address.
- `solAddress`: Your Solana (SOL) address.

---

## Module: `dumpster`

**Description:**
A data exfiltration tool that collects files from a specified directory, compresses them, and archives them into a single data file (`dumpster.dat`). It can also be used to restore files from this archive.

**How it works:**

- **Collect Mode:** The payload recursively walks through the `inputDir`, reads the files, and writes them into a single archive file specified by `dumpsterFile`. This is the default behavior when building a payload.
- **Restore Mode:** The "Garbage Collector" tab uses this module to reverse the process. It reads a `.dat` file and extracts its contents to a specified output directory.

**Options:**

- `inputDir`: The target directory to collect files from (e.g., `$HOME/Documents`).
- `dumpsterFile`: The path where the collected data will be stored as a single archive file (e.g., `$HOME/dumpster.dat`).
- `collectMode` (Internal): Set to `true` to enable file collection. This is the default.
- `restoreMode` (Internal): Set to `true` to enable file restoration. This is used by the "Garbage Collector" tab.

---

## Module: `ghostintheshell`

**Description:**
Provides a covert reverse shell by leveraging the Discord API. The payload connects to Discord as a bot and listens for commands from a specific user, allowing for remote command execution on the victim's machine.

**How it works:**
The payload logs into Discord using the provided bot token. It then waits for messages from the specified `creatorId`. Any message received from that user is executed as a shell command, and the output is sent back as a message to the same Discord channel.

**Options:**

- `discordToken`: The authentication token for your Discord bot.
- `creatorId`: Your unique Discord user ID. The bot will only accept commands from this user to prevent unauthorized access.

---

## Module: `krash`

**Description:**
A ransomware module that encrypts files within a target directory. After encryption, it can display a ransom note to the user. The "UNKRASH" tab is its counterpart, used to build a decryptor.

**How it works:**

- **Encrypt Mode:** The payload recursively finds all files in `targetDir`, encrypts them using AES with the provided `key` and `iv`, and appends the specified `extension` to the filenames. It then writes the `htmlContent` to a file to serve as the ransom note.
- **Decrypt Mode:** The "UNKRASH" tab builds a decryptor using this same module. When the decryptor runs, it finds files with the `.locked` extension, decrypts them with the same key and IV, and restores their original filenames.

**Options:**

- `key`: The 256-bit AES encryption key (as a 32-character hex string).
- `iv`: The 128-bit AES initialization vector (as a 16-character hex string).
- `extension`: The file extension to append to encrypted files (e.g., `.locked`).
- `targetDir`: The directory whose contents will be encrypted.
- `htmlContent`: The HTML content of the ransom note that will be displayed to the victim.
- `decrypt` (Internal): Set to `true` to build a decryptor instead of an encryptor. This is used by the "UNKRASH" tab.

---

## Module: `poof`

**Description:**
A destructive module that permanently deletes all files and folders within a specified directory. Use with extreme caution.

**How it works:**
The payload recursively traverses the `targetDir` and forcefully removes every file and sub-directory it encounters. This action is irreversible.

**Options:**

- `targetDir`: The directory to wipe clean.

---

## Module: `undeleteme`

**Description:**
A persistence module designed to ensure the payload survives a system reboot. It can also attempt to add an exclusion to Windows Defender to avoid detection.

**How it works:**

- **Persistence:** If enabled, the payload will typically copy itself to a persistent location (like `AppData`) and create a registry key (e.g., in `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`) to ensure it runs automatically every time the user logs in.
- **Defender Exclusion:** If enabled, the payload will execute a PowerShell command (`Add-MpPreference -ExclusionPath`) to add its own path to the Windows Defender exclusion list, reducing the likelihood of being scanned and quarantined.

**Options:**

- `persistence`: A boolean (`true`/`false`) to enable or disable the persistence mechanism.
- `defenderExclusion`: A boolean (`true`/`false`) to enable or disable adding a Windows Defender exclusion.

---
