package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
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

	fmt.Println("Logged in! Extracting chat names and messages...")
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

		fmt.Printf("Waiting for messages in chat: %s...\n", chatName)
		
		messageTimeout := time.Now().Add(20 * time.Second)
		messagesFound := false
		var messages []*rod.Element
		
		for time.Now().Before(messageTimeout) {
			selectors := []string{
				"[data-testid='conversation-message']",
				".message-in",
				".message-out", 
				"[data-testid='msg-meta']",
				".copyable-text",
				"[role='row']",
			}
			
			for _, selector := range selectors {
				if page.MustHas(selector) {
					elements, err := page.Elements(selector)
					if err == nil && len(elements) > 0 {
						messages = elements
						messagesFound = true
						fmt.Printf("Found %d messages using selector: %s\n", len(elements), selector)
						break
					}
				}
			}
			
			if messagesFound {
				break
			}
			
			fmt.Printf("Still waiting for messages... (%d seconds remaining)\n", int(messageTimeout.Sub(time.Now()).Seconds()))
			time.Sleep(2 * time.Second)
		}

		if !messagesFound {
			fmt.Printf("No messages found in chat: %s after timeout\n", chatName)
			continue
		}

		maxMessages := 5
		if len(messages) < maxMessages {
			maxMessages = len(messages)
		}

		startIndex := len(messages) - maxMessages
		if startIndex < 0 {
			startIndex = 0
		}

		fmt.Printf("Found %d messages, showing last %d:\n", len(messages), maxMessages)

		messageProcessTimeout := time.Now().Add(15 * time.Second)
		processedCount := 0
		
		for j := startIndex; j < len(messages) && time.Now().Before(messageProcessTimeout) && processedCount < maxMessages; j++ {
			message := messages[j]
			
			classes, _ := message.Attribute("class")
			messageType := "MESSAGE"
			if classes != nil {
				if strings.Contains(*classes, "message-in") {
					messageType = "INCOMING"
				} else if strings.Contains(*classes, "message-out") {
					messageType = "OUTGOING"
				}
			}

			text, textErr := message.Text()
			if textErr != nil || text == "" {
				continue
			}
			
			if len(text) > 100 {
				text = text[:100] + "..."
			}
			
			processedCount++

			sender := chatName
			recipient := chatName
			
			if messageType == "OUTGOING" {
				sender = "You"
			}

			var typeColor, textColor string
			if messageType == "INCOMING" {
				typeColor = "\033[32m"
				textColor = "\033[37m"
			} else {
				typeColor = "\033[33m"
				textColor = "\033[37m"
			}
			resetColor := "\033[0m"

			if messageType == "INCOMING" {
				fmt.Printf("%s[%s]%s %s%s%s → %s%s%s\n",
					typeColor, messageType, resetColor,
					"\033[36m", sender, resetColor,
					textColor, text, resetColor)
			} else {
				fmt.Printf("%s[%s]%s %s%s%s → %s%s%s\n",
					typeColor, messageType, resetColor,
					"\033[35m", recipient, resetColor,
					textColor, text, resetColor)
			}
		}
		
		if processedCount == 0 {
			fmt.Printf("No valid messages processed from chat: %s\n", chatName)
		} else {
			fmt.Printf("Processed %d messages from chat: %s\n", processedCount, chatName)
		}

		time.Sleep(2 * time.Second)
	}

	fmt.Printf("\nTotal chats processed: %d\n", len(processedChats))
	fmt.Println("Done.")
}