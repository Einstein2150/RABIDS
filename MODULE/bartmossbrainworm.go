package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"time"
	"github.com/go-rod/rod"
	"github.com/go-rod/rod/lib/launcher"
	"github.com/go-rod/rod/lib/proto"
)

func getDefaultProfileDir() string {
	home, _ := os.UserHomeDir()
	switch runtime.GOOS {
	case "windows":
		return filepath.Join(home, "AppData", "Local", "Google", "Chrome", "User Data", "Default")
	case "darwin":
		return filepath.Join(home, "Library", "Application Support", "Google", "Chrome", "Default")
	case "linux":
		return filepath.Join(home, ".config", "google-chrome", "Default")
	default:
		return ""
	}
}

func killChromeProcesses() {
	fmt.Println("Killing existing Chrome processes...")
	
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		cmd = exec.Command("taskkill", "/F", "/IM", "chrome.exe")
	case "darwin":
		cmd = exec.Command("pkill", "-f", "Google Chrome")
	case "linux":
		cmd = exec.Command("pkill", "-f", "google-chrome")
	default:
		fmt.Println("Unsupported OS for killing Chrome processes")
		return
	}
	
	if cmd != nil {
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		err := cmd.Run()
		if err != nil {
			fmt.Println("No Chrome processes found or already killed")
		} else {
			fmt.Println("Chrome processes killed successfully")
		}
		
		time.Sleep(2 * time.Second)
	}
}

func main() {
	killChromeProcesses()
	
	profileDir := getDefaultProfileDir()
	if profileDir == "" {
		fmt.Println("Unsupported OS or could not determine profile directory.")
		return
	}
	if _, err := os.Stat(profileDir); err != nil {
		fmt.Printf("Default Chrome profile not found at: %s\n", profileDir)
		return
	}

	fmt.Printf("Using Chrome profile: %s\n", profileDir)

	u := launcher.New().
		UserDataDir(filepath.Dir(profileDir)).
		Set("profile-directory", "Default").
		Headless(true).
		Leakless(false).
		Set("disable-web-security", "false").
		Set("disable-features", "TranslateUI").
		Set("no-first-run", "true").
		Set("no-default-browser-check", "true").
		Set("disable-background-timer-throttling", "true").
		Set("disable-backgrounding-occluded-windows", "true").
		Set("disable-renderer-backgrounding", "true").
		Set("disable-ipc-flooding-protection", "true").
		Set("disable-hang-monitor", "true").
		Set("disable-prompt-on-repost", "true").
		Set("disable-domain-reliability", "true").
		Set("disable-component-extensions-with-background-pages", "true").
		Set("disable-background-mode", "true").
		Set("disable-sync", "true").
		Set("disable-translate", "true").
		Set("disable-default-apps", "true").
		Set("disable-extensions", "true").
		Set("disable-background-networking", "true").
		Set("mute-audio", "true").
		Set("safebrowsing-disable-auto-update", "true").
		Set("disable-popup-blocking", "true").
		Set("disable-notifications", "true").
		Set("disable-single-process", "true").
		Set("no-zygote", "true").
		Set("disable-dev-shm-usage", "true").
		Set("no-sandbox", "true").
		Set("disable-gpu", "true").
		Set("remote-debugging-port", "0").
		Set("window-size", "1920,1080").
		Set("start-maximized", "true").
		Set("new-window", "true").
		Set("new-process", "true").
		Set("no-reuse-windows", "true").
		Set("disable-background-apps", "true").
		MustLaunch()

	browser := rod.New().ControlURL(u)
	if err := browser.Connect(); err != nil {
		fmt.Printf("Failed to connect to browser: %v\n", err)
		fmt.Println("Trying to launch a new Chrome instance...")
		
		u2 := launcher.New().
			UserDataDir(filepath.Dir(profileDir)).
			Set("profile-directory", "Default").
			Headless(false).
			Leakless(false).
			Set("remote-debugging-port", "9222").
			Set("new-window", "true").
			Set("new-process", "true").
			Set("no-reuse-windows", "true").
			Set("disable-background-apps", "true").
			Set("no-sandbox", "true").
			Set("disable-gpu", "true").
			MustLaunch()
		
		browser = rod.New().ControlURL(u2)
		if err := browser.Connect(); err != nil {
			fmt.Printf("Failed to connect to browser after retry: %v\n", err)
			fmt.Println("Please close all Chrome instances and try again.")
			return
		}
	}
	defer browser.MustClose()

	page := browser.MustPage("https://web.whatsapp.com")
	fmt.Println("Waiting for WhatsApp Web to load...")

	qrSel := "canvas[aria-label='Scan me!']"
	chatListSel := "div[role='listitem']"
	loadTimeout := time.Now().Add(60 * time.Second)
	loggedIn := false
	for time.Now().Before(loadTimeout) {
		if page.MustHas(chatListSel) {
			loggedIn = true
			break
		}
		if page.MustHas(qrSel) {
			break
		}
		time.Sleep(2 * time.Second)
	}

	if !loggedIn {
		if page.MustHas(qrSel) {
			fmt.Println("WhatsApp Web is not logged in. Please scan the QR code in the opened browser window.")
		} else {
			fmt.Println("Could not detect WhatsApp Web login or chat list. Please check manually.")
		}
		return
	}

	fmt.Println("Logged in! Cycling through all chats...")
	chats, err := page.Elements(chatListSel)
	if err != nil || len(chats) == 0 {
		fmt.Println("No chats found or error extracting chats.")
		return
	}

	maxChats := len(chats)

	processedChats := make(map[string]bool)
	chatProcessTimeout := time.Now().Add(300 * time.Second)

	for i := 0; i < maxChats && time.Now().Before(chatProcessTimeout); i++ {
		chatName, _ := chats[i].Text()
		if chatName == "" || processedChats[chatName] {
			continue
		}
		processedChats[chatName] = true

		fmt.Printf("\n=== Chat %d: %s ===\n", i+1, chatName)

		clickErr := chats[i].Click(proto.InputMouseButtonLeft, 1)
		if clickErr != nil {
			fmt.Printf("Failed to click on chat %s: %v\n", chatName, clickErr)
			continue
		}

		time.Sleep(3 * time.Second)
		fmt.Printf("Cycled to chat: %s\n", chatName)

		inputBox, err := page.Element("div[aria-label='Type a message'][contenteditable='true']")
		if err != nil {
			fmt.Printf("Could not find message input for chat %s: %v\n", chatName, err)
			continue
		}
		predefinedMessage := "Hello from BartmossBrainworm!"
		err = inputBox.Input(predefinedMessage)
		if err != nil {
			fmt.Printf("Could not type message in chat %s: %v\n", chatName, err)
			continue
		}

		sendButton, err := page.Element("button[aria-label='Send']")
		if err != nil {
			fmt.Printf("Could not find send button for chat %s: %v\n", chatName, err)
			continue
		}
		err = sendButton.Click(proto.InputMouseButtonLeft, 1)
		if err != nil {
			fmt.Printf("Could not click send button for chat %s: %v\n", chatName, err)
			continue
		}

		fmt.Printf("Sent message to chat: %s\n", chatName)
		time.Sleep(2 * time.Second)
	}

	fmt.Printf("\nTotal chats cycled: %d\n", len(processedChats))
	fmt.Println("Done.")
}