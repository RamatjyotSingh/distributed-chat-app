import pdb
import socket
import select
import argparse
import sys
import os
import re
import uuid
import json
import tempfile
import time
import random
import traceback
import threading

# Command-line argument parsing to get host and port from user
parser = argparse.ArgumentParser(description="Chat Client")
parser.add_argument('--local-port', type=int, default=8784, help='Local port number where the web server will run')
parser.add_argument('--server-host', type=str, default='localhost', help='Server hostname or IP address')
parser.add_argument('--server-port', type=int, default=8781, help='Server port number')
args = parser.parse_args()

chat_server_host = args.server_host
chat_server_port = args.server_port
web_server_port = args.local_port

def get_request(client):
    request = client.recv(1024).decode()
    while not request:
        request += client.recv(1024).decode()
    return request

def request_parser(client):
    request = get_request(client)
    req = request.split('\r\n\r\n')
    head = req[0]
    body = req[1] if len(req) > 1 else None
    lines = head.replace('\r\n', '\n').split('\n')
    method, path, protocol = lines[0].split(' ')
    headers = {}
    for line in lines[1:]:
        if line:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key] = value
    return method, path, protocol, headers, body

def send_header(client, content_type='text/html', status_code=200, status_text="OK", headers=None):
    header = f"HTTP/1.1 {status_code} {status_text}\r\n"
    header += f"Content-Type: {content_type}\r\n"
    header += "Connection: close\r\n"
    if headers:
        for key, value in headers.items():
            header += f"{key}: {value}\r\n"
    header += "\r\n"
    client.send(header.encode())

def send_file(file_path, client, content_type='text/html', status_code=200, status_text="OK", headers=None,cookie=None):
    if file_path == '/':
        
        file_path = 'index.html'
    elif file_path == '/chats/':
        if cookie is not None:
            send_header(client, "application/json", 200, "OK")
            client.sendall(json.dumps({"status": "success", "message": "Welcome back, gochujin-sama! (✿◠‿◠)", "has_cookie": True,"username":cookie.split('=')[1]}).encode())
        else:
            send_header(client, "application/json", 200, "OK")
            client.sendall(json.dumps({"status": "success", "message": "Hello, new friend! (◕‿◕)", "has_cookie": False}).encode())
        return 

    else:
        file_path = file_path.lstrip('/')
    try:
        if file_path.endswith('.py'):
            raise PermissionError()
        with open(file_path, 'rb') as f:
            send_header(client, content_type, status_code, status_text, headers)
            while True:
                file_data = f.read(1024)
                if not file_data:
                    break
                client.sendall(file_data)
            print(f"\nFile {file_path} sent successfully.")
    except FileNotFoundError as fnfe:
        send_file('404.html', client, "text/html", 404, "Not Found")
        print(f"File {file_path} not found.")
        print(f"Error: {fnfe}")
    except (PermissionError, IsADirectoryError):
        send_file('403.html', client, "text/html", 403, "Forbidden")
        print(f"Permission denied for file {file_path}.")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        send_header(client, "text/html", 500, "Internal Server Error")
        client.sendall(b"<h1>500 Internal Server Error</h1>")

def get_content_type(path):
    content_types = {
        '.html': 'text/html',
        '.txt': 'text/plain',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.ico': 'image/x-icon',
        '.json': 'application/json',
    }
    pos = path.rfind('.')
    ext = path[pos:]
    content_type = content_types.get(ext)
    return content_type
def file_handler(client, method, path, headers):
    cookie = headers.get('Cookie')
    if method == 'GET':
        try:
            content_type = get_content_type(path)
            if not content_type:
                content_type = 'text/html'
            send_file(path, client, content_type, 200, "OK",cookie=cookie)
        except Exception as e:
            print(f"Error handling GET request: {e}")
            send_header(client, "text/html", 500, "Internal Server Error")
            client.send(b"500 Internal Server Error")
    else:
        send_file('400.html', client, "text/html", 400, "Bad Request")

def api_handler(client, method, path, body):
    try:
        match = re.search(r'/api/([^/]+)', path)
        if match:
            api_call = match.group(1)
            print(f"\nAPI call: {api_call}")
            if method == 'POST':
                handle_POST(client, api_call, body)
            elif method == 'GET':
                handle_GET(client, api_call)
            elif method == 'DELETE':
                handle_DELETE(client, api_call, body)
                print("DELETE")
            
            else:
                send_file('400.html', client, "text/html", 400, "Bad Request")
                print("\nNot a valid api call for this route.", method, api_call, body)
    except Exception as e:
        print(60*'-')
        print(f"\nError: {e}\n")
        print(60*'-')
        traceback.print_exc()


def login(client, body):
    username = body['username']
    cookie = username  # Set the user cookie to the username
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((chat_server_host, chat_server_port))
    print("Connected to chat server")
    s.send("USER".encode())
    res = s.recv(2).decode()
    if res == 'OK':
        s.sendall(username.encode())
        welcome_msg = s.recv(1024).decode()
        send_header(client, "application/json", 200, "OK", {"Set-Cookie": f"Cookie={cookie}; Path=/; HttpOnly Secure"})
        client.sendall(json.dumps({"message": welcome_msg}).encode())
        s.close()
    else:
        print("Error: Expected USER header from chat server", res, "received")

def send_msg_to_server( body,client):
    try:
        print(body)
        
        # Convert the dictionary to a JSON string
        body_str = json.dumps(body)
        length = len(body_str)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((chat_server_host, chat_server_port))
            s.send('PMSG'.encode())
            res = s.recv(2).decode()
            if res == 'OK':
                s.sendall(f'{length:04}'.encode() + body_str.encode())
                s.close()
                # Send OK status back to the client
                send_header(client, content_type='application/json', status_code=200, status_text="OK")
                client.send(json.dumps({"status": "success", "message": "Message sent"}).encode())
            else:
                # Handle error response from chat server
                send_header(client, content_type='application/json', status_code=500, status_text="Internal Server Error")
                client.send(json.dumps({"status": "error", "message": "Failed to send message to chat server"}).encode())
    except Exception as e:
        print(f"Error sending message to server: {e}")
        send_header(client, content_type='application/json', status_code=500, status_text="Internal Server Error")
        client.send(json.dumps({"status": "error", "message": str(e)}).encode())

def get_msges(client):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((chat_server_host, chat_server_port))
        s.send(f'{"GMSG":4}'.encode())
        res = s.recv(2).decode()
        if res == 'OK':
            msg = s.recv(4).decode()
            if not msg:
                raise ConnectionResetError("Connection closed by the server")
            try:
                msg_len = int(msg)
            except ValueError:
                print("Error: Unexpected message length:", msg)
            res = s.recv(msg_len).decode()
            s.close()
    send_header(client, "application/json", 200, "OK")
    client.sendall(res.encode())


def get_last_msges(client, id):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((chat_server_host, chat_server_port))
        s.send('LAST'.encode())
        res = s.recv(2).decode()
        if res != 'OK':
            print("Error: Expected OK from chat server, received", res)
            return
        s.sendall(id.encode())
        msg = s.recv(4).decode()
        if not msg:
            raise ConnectionResetError("Connection closed by the server")
        try:
            msg_len = int(msg)
        except ValueError:
            print("Error: Unexpected message length:", msg)
        res = s.recv(msg_len).decode()
       
        s.close()
    send_header(client, "application/json", 200, "OK")
    client.sendall(res.encode())
    
def logout(client):
    headers = {
        "Set-Cookie": "Cookie=; Max-Age=0; Path=/",
    }
    send_header(client, content_type='application/json', status_code=200, status_text="OK", headers=headers)
    client.send(json.dumps({"status": "success", "message": "Logged out successfully"}).encode())
    
def handle_GET(client, api_call):
    if api_call == 'messages':
        get_msges(client)
    elif api_call.startswith('messages?last='):
        match = re.search(r'messages\?last=(\d+)', api_call)
        if match:
            msg_id = match.group(1)
            get_last_msges(client, msg_id)
    else:
        send_file('400.html', client, "text/html", 400, "Bad Request")
        print("\nNot a valid api call for this route. GET", api_call)

def handle_DELETE(client, api_call, body):
    try:

        if api_call == 'login':
            logout(client)

        elif api_call.startswith('messages?ID='):
            match = re.search(r'messages\?ID=(\d+)', api_call)

            if match:
                msg_id = match.group(1)
                body = json.loads(body)
                username = body['username']
                delete_msg(client, msg_id, username)
            else:
                send_file('400.html', client, "text/html", 400, "Bad Request")
                print("\nNot a valid api call for this route. DELETE", api_call)
        else:
            send_file('400.html', client, "text/html", 400, "Bad Request")
            print("\nNot a valid api call for this route. DELETE", api_call)
    except Exception as e:
        send_header(client, content_type='application/json', status_code=500, status_text="Internal Server Error")
        client.send(json.dumps({"status": "error", "message": str(e)}).encode())
        print(f"Error handling DELETE request: {e}")
def delete_msg(client, msg_id, username):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((chat_server_host, chat_server_port))
            s.send('DELT'.encode())
            res = s.recv(2).decode()
            if res == 'OK':
                req = json.dumps({"id": msg_id, "username": username})
                s.sendall(req.encode())
                s.close()
                # Send OK status back to the client
                send_header(client, content_type='application/json', status_code=200, status_text="OK")
                client.send(json.dumps({"status": "success", "message": "Message deleted"}).encode())
            else:
                # Handle error response from chat server
                send_header(client, content_type='application/json', status_code=500, status_text="Internal Server Error")
                client.send(json.dumps({"status": "error", "message": "Failed to delete message on chat server"}).encode())

    except Exception as e:
        print(f"Error deleting message: {e}")
        send_header(client, content_type='application/json', status_code=500, status_text="Internal Server Error")
        client.send(json.dumps({"status": "error", "message": str(e)}).encode())

def handle_POST(client, api_call, body):
    body = json.loads(body)
    username = body['username']
    if api_call == 'login':
        login(client, body)
    elif api_call == 'messages':
        send_msg_to_server(body,client)
    else:
        send_file('400.html', client, "text/html", 400, "Bad Request")
        print("\nNot a valid api call for this route. POST", api_call)

def client_handler(client):
    with client:
        try:
            method, path, protocol, headers, body = request_parser(client)
            print(f"Received request: {method} {path}")
            if path.startswith('/api/'):
                api_handler(client, method, path, body)
            else:
                file_handler(client, method, path, headers)
        except ConnectionResetError:
            print("Connection closed by the client.")
        except Exception as e:
            print(60*'-')
            print(f"\nError: {e}\n")
            print(60*'-')
            traceback.print_exc()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as web_socket:
    web_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    web_socket.bind(('', web_server_port))
    web_socket.listen(5)
    print(f"Server listening on {socket.gethostname()}:{web_server_port}...")
    print(f"Connected to chat server {chat_server_host}:{chat_server_port}.")
    while True:
        client, address = web_socket.accept()
        print(f"\nConnection from {address} has been established!")
        threading.Thread(target=client_handler, args=(client,)).start()