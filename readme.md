# **Distributed Chat Application with Multi-threaded Web Server**

## **Overview**

This project consists of a multi-threaded web server and a real-time chat client, designed for seamless communication through both a web and desktop interface. The server supports dynamic content and handles message exchanges using socket-based communication. The web client, a single-page application (SPA), interacts with the server via API calls for creating, retrieving, and managing messages. Additionally, user sessions are maintained using cookies for a smooth login experience.

---

## **Key Features**

- **Real-time Messaging**: Users can send and receive messages instantly, without page refreshes.
- **User Authentication**: Users log in with a username. Session management is handled through cookies.
- **Message Management**: Users can create, view, and delete messages.
- **Polling**: The web client uses polling to retrieve new messages periodically.
- **Error Handling**: The server handles errors gracefully, ensuring it never crashes and always returns an appropriate response.

---

## **Project Structure**

1. **Server (`server.py`)**  
   A multi-threaded server that manages incoming socket connections and handles message storage and retrieval.

2. **Web Server (`webserver.py`)**  
   Serves static content (HTML, CSS, JavaScript) and provides dynamic API routes for message management and user authentication.

3. **Web Client (`index.html`, `style.css`, `script.js`)**  
   A front-end built using HTML, CSS, and JavaScript that communicates with the server through API calls and updates the UI dynamically.

4. **Desktop Client (`client.py`)**  
   A Python-based desktop client using `tkinter` for the user interface. The client communicates with the server to send and receive messages.

5. **API Endpoints**  
   - **GET `/api/messages`**: Retrieve a list of all messages.
   - **GET `/api/messages?last=xxxxxx`**: Retrieve messages after a specific ID or timestamp.
   - **POST `/api/messages`**: Create a new message.
   - **DELETE `/api/messages/[message-id]`**: Delete a specific message by ID.
   - **POST `/api/login`**: Log the user in and set a session cookie.
   - **DELETE `/api/login`**: Log the user out and clear the session cookie.

---

## **Installation and Setup**

1. **Clone the repository**  

   ```sh
   git clone https://github.com/yourusername/distributed-chat-app.git
   cd distributed-chat-app
   ```

2. **Install dependencies**  
   Install the required Python packages:

   ```sh
   pip install psutil
   ```

3. **Start the Server**  
   To start the server, run the following commands in separate terminals:

   ```sh
   python3 server.py
   python3 webserver.py
   ```

4. **Access the Web Client**  
   Open your web browser and navigate to [http://localhost:8784](http://localhost:8784) to access the chat web client.

5. **Start the Desktop Client**  
   To run the desktop client, use the following command:

   ```sh
   python3 client.py --host localhost --port 8783
   ```

---

## **Setting Up a Cron Job to Delete `chat.log`**

1. **Make the `clean.sh` Script Executable**:
   Run the following command to make the script executable:

   ```sh
   chmod +x clean.sh
   ```

2. **Set Up a Cron Job**:
   Open the crontab file to set up a cron job:

   ```sh
   crontab -e
   ```

   Add the following line to the crontab file to run the script every hour:

   ```sh
   0 * * * * clean.sh
   ```

---

## **Usage**

- **Login**: Enter a username to log in. The session will be maintained using cookies, so you remain logged in across page loads.
- **Send Messages**: Type and send messages using the chat interface. Messages will appear in real-time across connected clients.
- **View Messages**: Messages will update dynamically via polling, without needing to refresh the page.
- **Delete Messages**: Right-click on a message to delete it (Bonus Feature).

---

## **Server Design and Routing**

### **Paths**

1. **`/`**: Serves the main HTML page, which includes the frontend for the chat application.
2. **`/api/`**: Handles dynamic API routes for actions such as viewing and posting messages, and logging in or out.
3. **Static Files**: Non-API routes serve static files like images, JavaScript, and CSS.
4. **Error Handling**: The server gracefully handles errors, ensuring appropriate HTTP responses (e.g., 404 for not found, 500 for server errors).

### **Message Polling**

The web client uses polling to fetch new messages from the server periodically. This ensures that the interface remains up to date without needing to reload the page.

---

## **Technical Details**

- **Sockets**: The server uses raw socket programming to handle communication between clients and the backend. This ensures efficient message delivery and retrieval.
- **Cookies**: Session management is handled through HTTP-only cookies, ensuring that users remain logged in between interactions.
- **Message Storage**: The server stores chat messages in memory, and uses socket communication to send and receive them.

---

## **Author**  

Ramatjyot Singh  

---

## **See it Live!**

Open incognito mode in your favorite browser and go to [http://osprey.cs.umanitoba.ca:8784](http://osprey.cs.umanitoba.ca:8784).  
Note: It doesn't support secure connections yet, so it won't open in normal mode.
