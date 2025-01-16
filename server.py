"""
This is the server code for the chat application. It listens for incoming connections from clients and handles the chat messages.
AUTHOR: Ramatjyot Singh
student ID: 7964553
COMP 3010 Assignment 1
DATE: 11/10/2024

"""


#DEPENDENCIES
import json
import socket
import select
import traceback
import random
import time
from collections import deque
import os
# import psutil  
import queue
from datetime import datetime
n = 0
HOST = ''  # Symbolic name meaning all available interfaces
PORT = 8783  # Arbitrary non-privileged port  
WEB_PORT =8781
CHAT_LOG = "chat.log"
NUM_RECENT_MESSAGES = 20
msg_sent = 0
msg_received = 0
start_time = time.time()

#discord like welcome messages
WELCOME_MESSAGES = [
    "{username} hopped into the server!",
    "Everyone welcome {username}!",
    "Glad to have you here, {username}!",
    "{username} joined the chat!",
    "Say hi to {username}!",
    "{username} is here, let's get started!",
    "Welcome aboard, {username}!",
    "{username} just landed!",
    "Hey {username}, welcome!",
    "{username} has entered the chat!"
]

clients = [] # List of connected clients
w_clients =[]
message_queues = {} # Dictionary to store the message queue for each client
client_username = {} # Dictionary to store the username for each client
 # Get a random welcome message for a new user
def get_random_welcome_message(username):

    welcome_msg = random.choice(WELCOME_MESSAGES).format(username=username)
 
    return welcome_msg
# Get the most recent messages from the chat log DETERMINED BY NUM_RECENT_MESSAGES



def get_recent_messages(filename, num_messages):
    if not os.path.exists(filename):  # Create the file if it doesn't exist
        open(filename, 'w').close()

    messages_list = deque(maxlen=num_messages)  # Use a deque to store the most recent messages
    
    with open(filename, 'r') as file:  # Read the file in reverse order
        for line in reversed(list(file)):
            messages_list.appendleft(line.strip())
            if len(messages_list) >= num_messages:
                break
    
    return list(messages_list)  # Convert deque to list before returning

       
def create_new_client(s):

    client, addr = s.accept()
    client.setblocking(False) # Set the client socket to non-blocking mode

    print('Connected by', addr)

    clients.append(client)
    message_queues[client] = queue.Queue() # Create a message queue for the new client

def get_username(client):

    global n #number of active clients
    global msg_sent
    global msg_received

    try:

        client.sendall("USER".encode()) #check condition for username
        msg_sent+=1

        while True:

            readable, _, _ = select.select([client], [], [], 1.0) # using select for concurrency

            if client in readable:

                username = client.recv(1024).decode().strip() # Receive the username from the client
                msg_received += 1

                if not username: # user aborted the eoperation
                    raise ConnectionResetError
                

                #welome user with recent msg and a cusotmised welcome msg because why not?
                else:

                    print(f"Username received from client: {username}")
                    n += 1

                    print("Client no: " + str(n))
                    # client_username[client] = username

                    msges= get_recent_messages(CHAT_LOG, NUM_RECENT_MESSAGES)
                    for msg in msges:
                        send_all_clients(msg)
                    welcome_msg = get_random_welcome_message(username)
                    welcome_msg = json.dumps({"message":welcome_msg})
                    

                    send_all_clients(welcome_msg)
                    break

    except ConnectionResetError: # user left the chat

        print("Connection reset by peer. The client may have closed the connection.")
        close_client_connection(client)

    except BrokenPipeError: # another reason of user leaving the chat

        print("Broken pipe error")
        close_client_connection(client)

    except Exception as e: #someting happened i guess?????

        print(f"Error getting username: {e}")
        traceback.print_exc()
        close_client_connection(client)

#broadcast msg to everyone
def send_all_clients(message):

    global msg_sent
    
    save_message(message, CHAT_LOG) #save chat history because privacy is a myth

    msg_len = len(message)
    header = f"{msg_len:04}" #send a byte header to know how much u takin in
    

    for client in clients:

        message_queues[client].put((header + message).encode('utf-8')) # put msg in queus so that they dont get overwhelmed by the messages

        try:

            send_message(client) #send the message to the client

        except BlockingIOError:

            print("Resource temporarily unavailable. Retrying...") #overwhelmed i guess

            time.sleep(0.1)  # Wait for a short period before retrying

            try:

                send_message(client) #try again

            except BlockingIOError:

                print("Failed to send message after retrying. Skipping this client.") 

                close_client_connection(client) #sometimes its better to let things go.....

                continue # because life will continue to move on so u too should continue living on

        except BrokenPipeError:

            # Client disconnected
            print(f"Client has disconnected. Cannot send messages")
            close_client_connection(client)

            continue

        except Exception as e: #some weird stuff happened

            print(f"Error sending message to client: {e}")
            traceback.print_exc()
            close_client_connection(client)

            continue

        except ConnectionResetError: #user left the chat
            print("Connection reset by peer. The client may have closed the connection.")
            close_client_connection(client)

            continue

#send message to client
def send_message(client):

    global msg_sent

    while not message_queues[client].empty():

        message = message_queues[client].get_nowait()
        client.sendall(message) #keep sending until the queue is empty

        msg_sent += 1

#close the connection
def close_client_connection(client):

    try:

      

      
        if client in clients:
            # username = client_username.pop(client, "Unknown") #del username from username list
            clients.remove(client) #remove client from the client list
        elif client in w_clients:
            w_clients.remove(client)

        else:
            print("Client not in clients list")
            raise ConnectionError
        
        message_queues.pop(client, None) #remove queued up msges cause what they are needed for?

        # send_all_clients(f"{username} has left the chat") # Pay respects to the fallen

        client.close() #close the socket to prevent wierd stuff from happeneing 
        
    except ConnectionError:

        print("Connection was already closed")

#save the message to the chat log
def save_message(message, filename):
  
    if not os.path.exists(filename): #create the file if it doesnt exist
        open(filename, 'w').close()

    with open(filename, 'a') as file:
        file.write(message + '\n')

#funciton to hadle the messages from the client

def handle_client_messages(client):

    buffer = b''
    global msg_sent
    global msg_received

    try:

        if client not in clients: #verify u dont contact the closed connection!

            print("Client not in clients list")
            raise ConnectionResetError

        # Read the fixed-length header first (4 bytes)
        header = client.recv(4).decode('utf-8')
        msg_received += 1

        if not header: #client closed the connection

            raise ConnectionResetError("Connection closed by the client")

        # Convert the header to an integer to get the message length

        try:

            msg_len = int(header)

        except ValueError: # someone spammed the text box now msges are jumbled up

            msg_len = 1024

        # Read the remaining message based on the length
        buffer = client.recv(msg_len).decode('utf-8')
        # Process the received message
        msg_received += 1

    
        
        send_all_clients(buffer) #broadcast

        msg_sent += 1

        buffer = b''  # Reset buffer for the next message

    #error handling stuff for when user leaves the chat gets sdisconnected ot his laptop sets on fire🔥🔥🔥

    except BlockingIOError:

        print("Resource temporarily unavailable. Retrying...")
        time.sleep(0.1)

    except ConnectionResetError:

        print("Connection reset by peer. The client may have closed the connection.")
        close_client_connection(client)

    except BrokenPipeError:

        print("Broken pipe error. The client has disconnected.")
        close_client_connection(client)

    except OSError as e:

        if e.errno == 9:
            print("Bad file descriptor. The client connection may have been closed.")
            close_client_connection(client)

        else:
            raise


    except Exception as e:
        print(f"Error handling client message: {e}")
        traceback.print_exc()
        close_client_connection(client)


#techincal stuff to log the system metrics for server analysis
# def log_system_metrics():
#     # Take initial snapshot
#     net_io_start = psutil.net_io_counters()
#     bytes_sent_start = net_io_start.bytes_sent
#     bytes_recv_start = net_io_start.bytes_recv

#     # Wait for a short period
#     time.sleep(1)

#     # Take final snapshot
#     net_io_end = psutil.net_io_counters()
#     bytes_sent_end = net_io_end.bytes_sent
#     bytes_recv_end = net_io_end.bytes_recv

#     # Calculate the difference
#     bytes_sent = bytes_sent_end - bytes_sent_start
#     bytes_recv = bytes_recv_end - bytes_recv_start

#     # Convert to KB
#     bytes_sent_kb = bytes_sent / 1024
#     bytes_recv_kb = bytes_recv / 1024

#     cpu_usage = psutil.cpu_percent(interval=1)
#     memory_info = psutil.virtual_memory()
#     disk_usage = psutil.disk_usage('./')
#     load_avg = os.getloadavg()

#     # Get CPU temperature
#     try:
#         temps = psutil.sensors_temperatures()
#         if not temps:
#             cpu_temp = "N/A"
#         else:
#             # Assuming 'coretemp' is the key for CPU temperature
#             cpu_temp = temps['coretemp'][0].current
#     except AttributeError:
#         cpu_temp = "N/A"  # psutil.sensors_temperatures() is not available on this system

#     log_message = (
#         f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
#         f"CPU Usage: {cpu_usage}%\n"
#         f"Memory Usage: {memory_info.percent}%\n"
#         f"Available Memory: {memory_info.available / (1024 ** 2)} MB\n"
#         f"Disk Usage: {disk_usage.percent}%\n"
#         f"Network Sent: {bytes_sent_kb:.2f} KB\n"
#         f"Network Received: {bytes_recv_kb:.2f} KB\n"
#         f"Load Average: {load_avg}\n"
#         f"CPU Temperature: {cpu_temp}°C\n"
#         f"Number of Active Clients: {len(clients)}\n"
#     )

#     with open("system_metrics.log", "a") as log_file:
#         log_file.write(log_message + "\n")

#initialise the connection with the client
def init_client_connection(s,w):

    global start_time
    global msg_sent
    global msg_received

    # last_log_time = time.time()

    # log_interval = 5  # Log every 5 seconds
    try:
        while True:
            # current_time = time.time()
            # if current_time - last_log_time >= log_interval:
            #     log_system_metrics()
            #     last_log_time = current_time

            # Monitor sockets for incoming connections or data
            inputs = [s] + clients + [w] + w_clients
            readable, _, exceptional = select.select(inputs, [], inputs,0.1)

            for client in readable:
                if client is s:  # New chat client connection
                    create_new_client(s)
                    get_username(clients[-1])
                    
                elif client is w:  # New short-lived web client connection
                    handle_web_client(w)

                # elif client in w_clients:  # Handle web client's command (short-lived)
                #     process_web_command(client)
                    
                elif client in clients:  # Handle chat client's message (long-lived)
                    handle_client_messages(client)

    except (KeyboardInterrupt, BrokenPipeError):
        print("Server shutting down")
    
    



    
# Web client handling (Short-lived connections)
def handle_web_client(w):
    client, addr = w.accept()
    print(f"Connected by {addr} (short-lived)")
    w_clients.append(client)
    process_web_command(client)


def process_web_command(client):
    command = client.recv(4).decode('utf-8').strip()
    try:
        if command == "USER":
            get_web_username(client)
        elif command == "GMSG":
            send_recent_messages(CHAT_LOG, NUM_RECENT_MESSAGES, client)
        elif command == "PMSG":
            save_web_message(client)
        elif command == "LAST":
            send_web_message(client)
        elif command == "DELT":
            delete_message(client)
    except Exception as e:
        print(f"Error processing web command: {e}")
        traceback.print_exc()
    finally:
         close_short_lived_client(client)

def save_web_message(client):
    client.sendall("OK".encode())
    msg_len = client.recv(4).decode('utf-8')
    if not msg_len:
        msg_len = 1024
    msg_len = int(msg_len)
   
    message = client.recv(msg_len).decode().strip()
    save_message(message, CHAT_LOG)
    client.close()
    

def send_recent_messages(filename, num_messages, client):
    client.sendall("OK".encode())
    msgs_list= get_recent_messages(filename, num_messages)
    msgs = json.dumps(msgs_list)
    length = len(msgs)
    client.sendall(f'{length:04}{msgs}'.encode('utf-8'))


def close_short_lived_client(client):
    if client in w_clients:
        client.close()
        w_clients.remove(client)
def get_web_username(client):
    global msg_sent
    global msg_received
    global n
    try:
           
        client.sendall("OK".encode())
        username = client.recv(1024).decode().strip()
        message_queues[username] = queue.Queue() # Create a message queue for the new client

        msg_received += 1
        if not username:
            raise ConnectionResetError
        else:
            print(f"Username received from client: {username}")
            n += 1
            print("Client no: " + str(n))
            welcome_msg = get_random_welcome_message(username)
            welcome_msg = {"message":welcome_msg}
            log = json.dumps(welcome_msg)
            
            save_message(log, CHAT_LOG)

            client.sendall((json.dumps(welcome_msg)).encode('utf-8'))
          
            
          
    except  Exception as e:
        print("Exception occured")
        print(e)

def send_all_web_clients(message,username,id):
    for client in w_clients:
        send_web_message(client,message,username,id)
def get_command(client):
    command = client.recv(4).decode('utf-8')
    return command
def send_web_message(client):
    global msg_sent
    global msg_received
    global n
    try:  
            client.sendall("OK".encode())
            # message = [{"message":message, "timestamp":time.time(), "id":time.time(), "username":"test"}]
            # res = json.dumps(message)
            id = client.recv(1024).decode().strip()
            print(id)
            msges_json = search_chat_log(CHAT_LOG, float(id))
            print(msges_json)
            msgs = json.dumps(msges_json)
            print(msgs)
            length = len(msgs)
            print(length)
            client.sendall(f'{length:04}'.encode('utf-8') + msgs.encode('utf-8')) 
            msg_sent+=1
    except Exception as e:
        print("Exception occured")
        print(e.with_traceback())
   
    # try:
    #     if client not in w_clients:
    #         print("Client not in clients list")
    #         return
    #     message = {"username":"test","message":message,"timestamp":time.time(),"id":time.time()}
    #     client.sendall((json.dumps(message)).encode('utf-8'))
    #     msg_sent+=1
    # except Exception as e:
    #     print("Exception occured")
    #     print(e)
    # finally:
    #     client.close()
    #     print("Connection closed")
def search_chat_log(filename, id):
    results = deque()  # Use a deque to store the results

    with open(filename, 'r') as file:
        lines = list(file)  # Read all lines into a list

    for line in reversed(lines):  # Iterate from bottom to top
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        try:
            obj = json.loads(line)
            if 'id' in obj and obj['id'] > id:
                results.appendleft(obj)  # Add to the front of the deque
        except json.JSONDecodeError:
            print(f"Invalid JSON in chat log: {line}")
            continue  # Skip invalid JSON lines

    return list(results)  # Convert deque to list before returning
def delete_message(client):
    client.sendall("OK".encode())
    req = client.recv(1024).decode().strip()
    req = json.loads(req)
    id = req["id"]
    username = req["username"]
    remove_msg(CHAT_LOG, username, float(id))
    
def remove_msg(file_path, username, id):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    with open(file_path, 'w') as file:
        for line in lines:
            try:
                log_entry = json.loads(line)
                if log_entry.get("username") != username or log_entry.get("id") != id:
                    file.write(json.dumps(log_entry) + '\n')
            except json.JSONDecodeError:
                print(f"Invalid JSON in chat log: {line}")
                continue  # Skip invalid JSON lines
def main():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:#TCP connection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as w:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #let us reuse it
            w.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            s.setblocking(False)#non blocking mode
            s.bind((HOST, PORT))
            s.listen()

            print("Server started")
            print("Listening on port", PORT)
            print("Waiting for clients")

            w.setblocking(False)
            w.bind((HOST,WEB_PORT))
            w.listen()
            print("\nserver for web starting\nlistening on port "+str(WEB_PORT))

            init_client_connection(s,w)

            print(f"Messages sent: {msg_sent}")
            print(f"Messages received: {msg_received}")
            print(f"Messages sent per second: {msg_sent / (time.time() - start_time)}")
            print(f"Messages received per second: {msg_received / (time.time() - start_time)}")
            
            print("Server closed")
            print("Goodbye!")

























main()
