#!/usr/bin/env python3
import socket

camera_ip = "192.168.1.12"
ports = [80, 81, 8080, 8081, 8888, 554]

print(f"Quick port check for {camera_ip}:\n")

for port in ports:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((camera_ip, port))
        sock.close()
        
        if result == 0:
            print(f"✓ Port {port}: OPEN")
        else:
            print(f"✗ Port {port}: closed")
    except Exception as e:
        print(f"✗ Port {port}: error")
