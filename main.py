import socket
import threading
from stem import Signal
from stem.control import Controller

# Configure Tor settings
tor_proxy_ip = '127.0.0.1'
tor_proxy_port = 9050

def renew_tor_identity():
    # Function to renew Tor identity by sending a NEWNYM signal
    with Controller.from_port(address=tor_proxy_ip, port=tor_proxy_port) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)

def handle_client(client_socket, target_host, target_port):
    # Establish a connection to the target server via Tor SOCKS proxy
    tor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tor_socket.connect((tor_proxy_ip, tor_proxy_port))

    # Request a new Tor identity for each connection
    renew_tor_identity()

    # Send an initial Tor connection handshake (SOCKS protocol version)
    tor_socket.sendall(b'\x05\x01\x00')

    # Receive the Tor connection handshake response
    response = tor_socket.recv(2)

    if response == b'\x05\x00':
        # If the Tor proxy successfully connected to the target server

        while True:
            # Read data from the client
            client_data = client_socket.recv(4096)
            if not client_data:
                break

            # Forward data to the target server via Tor
            tor_socket.sendall(client_data)

            # Read data from the target server via Tor
            target_data = tor_socket.recv(4096)
            if not target_data:
                break

            # Forward data back to the client
            client_socket.sendall(target_data)

        tor_socket.close()

    client_socket.close()

def proxy_server(proxy_ip, proxy_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((proxy_ip, proxy_port))
    server_socket.listen(5)

    print(f"Proxy server listening on {proxy_ip}:{proxy_port}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address}")

        target_host = input("Enter the target URL: ")
        target_port = int(input("Enter the target port: "))

        client_handler = threading.Thread(
            target=handle_client,
            args=(client_socket, target_host, target_port)
        )
        client_handler.start()

if __name__ == "__main__":
    proxy_ip = '127.0.0.1'
    proxy_port = 8888

    proxy_server(proxy_ip, proxy_port)