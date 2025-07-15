package main

import (
	"os/exec"
	"fmt"
)

func main() {
	cmd := exec.Command("shutdown", "/s", "/t", "0")
	err := cmd.Run()
	if err != nil {
		fmt.Println("Failed to shutdown:", err)
	}
}

func compile() {} 