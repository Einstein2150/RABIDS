import os, strutils, base64

proc collect(input_dir: string, dumpster: string) =
    try:
        let dumpDir = parentDir(dumpster)
        if dumpDir != "":
            createDir(dumpDir)
    except Exception:
        echo "error creating the dumpster directory"

    try:
        let lootFile = open(dumpster, fmWrite)
        defer: lootFile.close()

        let fileExt: seq[string] = @[]

        for file in walkDirRec(input_dir):
            try:
                if fileExists(file) and not (splitFile(file).ext.replace(".", "").toLowerAscii() in fileExt):
                    let content = readFile(file)
                    let b64 = encode(content)
                    let rel = relativePath(file, input_dir)
                    lootFile.write(rel & "\n" & b64 & "\n\n")
            except Exception:
                echo "error processing file: ", file
    except Exception:
        echo "error writing to the dumpster file"

proc restore(dumpster: string, output_dir: string) =
    try:
        createDir(output_dir)
    except Exception:
        echo "error creating the output directory"

    try:
        let content = readFile(dumpster)
        for dataBlock in content.split("\n\n"):
            let trimmed = dataBlock.strip()
            if trimmed == "": continue
            let parts = trimmed.split("\n", 1)
            if parts.len != 2: continue
            let rel = parts[0]
            let b64 = parts[1]
            try:
                let data = $decode(b64)
                let outpath = output_dir / rel
                let outDir = parentDir(outpath)
                if outDir != "":
                    createDir(outDir)
                writeFile(outpath, data)
            except Exception:
                echo "error restoring file: ", rel
    except Exception:
        echo "error reading from the dumpster file"
    
const
    inputDir* = ""
    dumpsterFile* = ""
    outputDir* = ""

proc main() =
    when defined(collectMode):
        var currentInputDir = inputDir
        var currentDumpsterFile = dumpsterFile
        
        if "$HOME" in currentInputDir:
            currentInputDir = currentInputDir.replace("$HOME", getHomeDir())
        if "$HOME" in currentDumpsterFile:
            currentDumpsterFile = currentDumpsterFile.replace("$HOME", getHomeDir())

        if currentInputDir.len > 0 and currentDumpsterFile.len > 0:
            collect(currentInputDir, currentDumpsterFile)
    elif defined(restoreMode):
        var currentDumpsterFile = dumpsterFile
        var currentOutputDir = outputDir

        if "$HOME" in currentDumpsterFile:
            currentDumpsterFile = currentDumpsterFile.replace("$HOME", getHomeDir())
        if "$HOME" in currentOutputDir:
            currentOutputDir = currentOutputDir.replace("$HOME", getHomeDir())
        if currentDumpsterFile.len > 0 and currentOutputDir.len > 0:
            restore(currentDumpsterFile, currentOutputDir)
    else: # Fallback to original command-line argument behavior
        if paramCount() >= 3:
            let mode = paramStr(1)
            if mode == "--collect":
                collect(paramStr(2), paramStr(3))
            elif mode == "--restore":
                restore(paramStr(2), paramStr(3))
