from datetime import datetime
import json
import socket
import select
import sys
import time
import traceback
import tkinter as tk
from tkinter import scrolledtext

import argparse
username = None
# Command-line argument parsing to get host and port from user
parser = argparse.ArgumentParser(description="Chat Client")
parser.add_argument('--host', type=str, default='localhost', help='Server hostname or IP address')
parser.add_argument('--port', type=int, default=8783, help='Server port number')
args = parser.parse_args()

# Constants
HOST = args.host
PORT = args.port
DELIMITER = "<END>"
BUFFER_SIZE = 1024
DARK_GREY = "#282828"
OCEAN_BLUE = "#2b8cc4"
MEDIUM_GREY = "#444444"
LIGHT_GREY = "#d3d3d3"
DARKER_GREY = "#a9a9a9"
FONT = "Poppins 12"
FONT_BOLD = "Poppins 12 bold"
FONT_LARGE = "Poppins 16"
FONT_SMALL = "Poppins 10"

# Function to create the chat window
def create_chat_window(username, client):

    chat_window = tk.Tk()
    chat_window.title(f"Chat App for Nerd~")
    chat_window.geometry("1200x900")
    chat_window.resizable(False, False)

    #row configuratoin
    chat_window.grid_rowconfigure(0, weight=1)
    chat_window.grid_rowconfigure(1, weight=7)
    chat_window.grid_rowconfigure(2, weight=1)

    # Top frame
    top_frame = tk.Frame(chat_window, width=900, height=100, bg=MEDIUM_GREY)
    top_frame.grid(row=0, column=1, sticky=tk.NSEW)

    # Middle frame
    middle_frame = tk.Frame(chat_window, width=900, height=700, bg=DARK_GREY)
    middle_frame.grid(row=1, column=1, sticky=tk.NSEW)

    # Bottom frame
    bottom_frame = tk.Frame(chat_window, width=900, height=100, bg=MEDIUM_GREY)
    bottom_frame.grid(row=2, column=1, sticky=tk.NSEW)

    # Side frame
    side_frame = tk.Frame(chat_window, width=300, height=900, bg=DARK_GREY)
    side_frame.grid(row=0, column=0, rowspan=3, sticky=tk.NSEW)

    # Chat label
    chat_label = tk.Label(top_frame, text="~Chat App for Nerds~", font=FONT_LARGE, bg=DARK_GREY, fg="white")
    chat_label.pack(pady=10)

    # Chat area
    chat_area = scrolledtext.ScrolledText(middle_frame, wrap=tk.WORD, font=FONT_SMALL, bg=MEDIUM_GREY, fg="black", width=80, height=30)
    chat_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    chat_area.config(state=tk.DISABLED)

    # Message entry box
    message_entry = tk.Entry(bottom_frame, bg=LIGHT_GREY, font=FONT, width=80)
    message_entry.pack(side=tk.LEFT, padx=10, pady=10)

    # Send button
    def send_message():
        message = message_entry.get().strip()

        if message:

            send(client, message)
           
            chat_area.config(state=tk.DISABLED)#dsiable the chat area to avoid putting unauthorized input
            message_entry.delete(0, tk.END)#clear the msg box

    send_button = tk.Button(bottom_frame, text="Send", font=FONT, command=send_message, bg=OCEAN_BLUE)
    send_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def receive_messages():
        global username
        try:
            # for concurrency
            readable, _, _ = select.select([client], [], [], 0.1)

            #if input is ready to read
            if client in readable:

                header = client.recv(4).decode('utf-8')#receive the header to know content length

                if not header:

                    raise ConnectionResetError("Connection closed by the server")
                
                if header == "USER":

                    client.sendall(username.encode('utf-8'))

                else:

                    try:

                        msg_len = int(header)

                    except ValueError:
                        msg_len = 1024

                    buffer = client.recv(msg_len).decode('utf-8')
                    body = json.loads(buffer)   
                    if 'timestamp' in body and 'username' in body and 'message' in body:
                    # Regular chat message
                        time_stamp = body['timestamp']
                        username = body['username']
                        message = body['message']
                        text = f"{time_stamp} {username}: {message}"
                    elif 'message' in body:
                        # Welcome message
                        message = body['message']
                        text = f"{message}"

                    chat_area.config(state=tk.NORMAL)
                    chat_area.insert(tk.END, text + "\n")
                    chat_area.config(state=tk.DISABLED)

        except ConnectionResetError:

            print("Server closed the connection")
            client.close()

        except Exception as e:

            print(f"An error occurred: {e}")
            traceback.print_exc()

            client.close()

        # Schedule the next call to receive_messages
        chat_window.after(100, receive_messages)

    # Start the receive_messages function
    chat_window.after(100, receive_messages)
    chat_window.mainloop()

# Function to get the username
def get_username():

    login_window = tk.Tk()
    login_window.title("Login")

    login_window.geometry("400x200")

    login_window.configure(bg=DARKER_GREY)
    login_window.resizable(False, False)

    # Center the window on the screen
    window_width = 400
    window_height = 200

    screen_width = login_window.winfo_screenwidth()
    screen_height = login_window.winfo_screenheight()

    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)

    login_window.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

    center_frame = tk.Frame(login_window, bg=DARKER_GREY)
    center_frame.pack(expand=True, padx=20, pady=20)

    username_label = tk.Label(center_frame, text="Username: ", font=FONT, bg=DARKER_GREY, fg="black")
    username_label.pack(pady=10)

    username_entry = tk.Entry(center_frame, font=FONT)
    username_entry.pack(pady=10)

    def on_submit():
        global username
        username = username_entry.get().strip()

        if username:
            #remove the login screen when u got the usernanme
            login_window.destroy()

            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #connect with him and start the chat
            client.connect((HOST, PORT))

            print("Connected to server on HOST:", HOST, "PORT:", PORT)
            create_chat_window(username, client)

    submit_button = tk.Button(center_frame, text="Submit", font=FONT, command=on_submit)
    submit_button.pack(pady=10)

    login_window.mainloop()

def send(client, message):
    global username
    try:

        if message == 'quit':

            client.close()
            sys.exit()

        msg_len = len(message)
        
        if msg_len > 0:

            id = time.time()
            time_stamp = datetime.fromtimestamp(id).strftime('%H:%M:%S')
            username = username
            message = message
            msg_json = json.dumps({"timestamp": time_stamp, "username": username, "message": message, "id": id})
            length = f"{len(msg_json):4}".encode('utf-8')

            client.sendall(length+ msg_json.encode('utf-8'))

        else:

            print("Message cannot be empty")

    except BrokenPipeError:

        print("Broken pipe error, connection lost.")
        client.close()

    except Exception as e:

        print(f"An error occurred: {e}")
        traceback.print_exc()
        client.close()
        sys.exit()

def main():
    try:
            
        get_username()

    except KeyboardInterrupt: 
            print("Exiting...")
            sys.exit(0)
    except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
            sys.exit(1)
main()