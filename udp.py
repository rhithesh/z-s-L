import socket


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


sock.bind(('', 8080))   

print("Listening for UDP data on port 8080...")

while True:
    data, addr = sock.recvfrom(4096)  # buffer size in bytes
    print(f"Received from {addr}: {data.decode(errors='ignore')}")
