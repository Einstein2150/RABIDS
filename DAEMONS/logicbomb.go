package main

import (
	"syscall"
	"fmt"
	"time"
)

func main() {
	user32 := syscall.NewLazyDLL("user32.dll")
	blockInput := user32.NewProc("BlockInput")
	r, _, err := blockInput.Call(1)
	if r == 0 {
		fmt.Println("Failed to block input:", err)
		return
	}
	fmt.Println("Keyboard and mouse input blocked. Press Ctrl+Alt+Del to unlock (if possible).")
	for {
		time.Sleep(10 * time.Second)
	}
}

