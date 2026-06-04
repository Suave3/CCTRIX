#!/usr/bin/env python3
import socket

camera_ip = "192.168.1.12"

print(f"Scanning all ports on {camera_ip}...\n")
print("Open ports found:")

open_ports = []
for port in range(1, 65535):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.2)
        result = sock.connect_ex((camera_ip, port))
        sock.close()
        
        if result == 0:
            open_ports.append(port)
            print(f"   Port {port}: OPEN")
    except:
        pass

if not open_ports:
    print("   No open ports found")
else:
    print(f"\nSummary: Found {len(open_ports)} open ports")
