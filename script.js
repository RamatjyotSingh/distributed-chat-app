"use strict";

let USERNAME = null ; 
let lastMsgId = Date.now(); 



function createMessage(username, timestamp, message,msgID) {
    if(!username && !timestamp && !msgID && message) {
        console.log(message);
        createWelcomeMessage(message);
        return;
    }
    let messageContainer = document.querySelector('.message-container');

    let chatMessage = document.createElement('div');
    chatMessage.classList.add('chat-message');
    chatMessage.id = msgID;

    let messageHeader = document.createElement('div');
    messageHeader.classList.add('message-header');

    let usernameSpan = document.createElement('span');
    usernameSpan.classList.add('username');
    usernameSpan.innerText = username;

    let timestampSpan = document.createElement('span');
    timestampSpan.classList.add('timestamp');
    timestampSpan.innerText = timestamp;

    messageHeader.appendChild(usernameSpan);
    messageHeader.appendChild(timestampSpan);

    let messageContent = document.createElement('div');
    messageContent.classList.add('message-content');

    let messageParagraph = document.createElement('p');
    messageParagraph.innerText = message;

    messageContent.appendChild(messageParagraph);
    chatMessage.appendChild(messageHeader);
    chatMessage.appendChild(messageContent);
    
    let delPopup = document.createElement('div');
    delPopup.classList.add('del-popup', 'is-hidden');

    let deleteButton = document.createElement('button');
    deleteButton.classList.add('delete-btn');
    deleteButton.innerText = 'Delete';

  

    delPopup.appendChild(deleteButton);
    chatMessage.appendChild(delPopup);

    messageContainer.appendChild(chatMessage);
    lastMsgId = Date.now();
}
document.addEventListener('DOMContentLoaded', function() {
     // Fetch the index.html file
     let xhrIndex = new XMLHttpRequest();
     xhrIndex.open('GET', '/');
     xhrIndex.onload = function() {
         if (xhrIndex.status === 200) {
             document.documentElement.innerHTML = xhrIndex.responseText;
             
             // After loading the index.html, check for cookies
             let xhrCookie = new XMLHttpRequest();
             xhrCookie.open('GET', '/chats/');
             xhrCookie.setRequestHeader('Content-Type', 'application/json');
             xhrCookie.withCredentials = true; // Include cookies in the request
 
             xhrCookie.onload = function() {
                 if (xhrCookie.status === 200) {
                     let response = JSON.parse(xhrCookie.responseText);
                     if (response.has_cookie) {
                        document.querySelector('.login-container').classList.add('is-hidden');
                        document.querySelector('.chat-container').classList.remove('is-hidden');
                        USERNAME = response.username;
                        getMessages();
                     }

                        addDeleteEvent();
                     
                 }
             };
 
             xhrCookie.onerror = function() {
                 console.error("Network Error: Unable to complete the request.");
             };
 
             xhrCookie.send();
         }
     };
 
     xhrIndex.onerror = function() {
         console.error("Network Error: Unable to complete the request.");
     };
 
     xhrIndex.send();
    // Select the parent container of chat messages
   

  

}); 

function addDeleteEvent(){

    let messageContainer = document.querySelector('.message-container');
    console.log(messageContainer);
    // Add event listener for right-click (contextmenu) on messages
    messageContainer.addEventListener('contextmenu', function(event) {
        console.log('Right-clicked on the message container');
        let target = event.target;

        // Traverse up to find the .chat-message element
        while (target && !target.classList.contains('chat-message')) {
            target = target.parentElement;
        }

        if (target && target.classList.contains('chat-message')) {
            console.log('Right-clicked on:', target);

            if(target.querySelector('.username').innerText !== USERNAME) {
                return;
            }
            event.preventDefault(); // Prevent the default context menu
            // Get the bounding rectangle of the chat message
            const rect = target.getBoundingClientRect();

            // Calculate mouse position relative to the chat message
            const mouseX = event.clientX - rect.left;
            const mouseY = event.clientY - rect.top;

            // Select the del-popup within the chat message
            const delPopup = target.querySelector('.del-popup');
            const msgID = target.id;
            console.log(msgID);
            if (delPopup) {
                // Position the popup near the cursor
                delPopup.style.left = `${mouseX}px`;
                delPopup.style.top = `${mouseY}px`;

                // Optionally, add a class to style the chat message as active
                delPopup.classList.remove('is-hidden');
            }
            delPopup.addEventListener('click', function(event) {

                console.log(event.target);

                delPopup.classList.add('is-hidden');   
                target.remove(); 
                deleteMessages(msgID);

              
                    
                
            });
            // Handle delete button clicks
            messageContainer.addEventListener('click', function(){
                console.log('clicked')
                delPopup.classList.add('is-hidden');
                
            })
           
        }
    });

   

}
function send() {
    if (!USERNAME) {
        alert('Please enter a username');
        return;
    }
    let timestamp = new Date().toLocaleTimeString();
    let msgID = Date.now();
    console.log(timestamp);
    let message = document.getElementById('message').value;

    if (message.trim() === "") {
        alert("Please enter a message");
        return;
    }

    createMessage(USERNAME, timestamp, message, msgID);

    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/messages');
    xhr.setRequestHeader('Content-Type', 'application/json');

    xhr.withCredentials = true; // Include cookies in the request

    // Handle successful response
    xhr.onload = function() {
        if (xhr.status === 200) {
            console.log("Success:", xhr.responseText);
        } else {
            console.error("Request completed but failed. Status:", xhr.status, "Status Text:", xhr.statusText);
        }
    };

    // Handle network errors
    xhr.onerror = function() {
        console.error("Network Error: Unable to complete the request.");
    };

    xhr.send(JSON.stringify({ "username": USERNAME, "timestamp": timestamp, "message": message, "id": msgID }));
    console.log(USERNAME, timestamp, message);

    // Clear the message input field
    document.getElementById('message').value = '';
}

function leave() {
    let xhr = new XMLHttpRequest();
    xhr.open('DELETE', '/api/login');
    xhr.setRequestHeader('Content-Type', 'application/json');

    xhr.withCredentials = true; // Include cookies in the request
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            console.log(xhr.responseText);
        }
    }
    xhr.send();

    document.querySelector('.login-container').classList.remove('is-hidden');
    document.querySelector('.chat-container').classList.add('is-hidden');
}

function join() {
    USERNAME = document.getElementById('username').value; // Assign value to global variable
    console.log(USERNAME);
    if (USERNAME.trim() === "") {
        alert('Please enter a username');
        return;
    }

    document.querySelector('.login-container').classList.add('is-hidden');
    document.querySelector('.chat-container').classList.remove('is-hidden');

    sendUsername();
}


function createWelcomeMessage(msg) {
    
   
    let welcomeMessage = document.createElement('p');
    welcomeMessage.classList.add('welcome-message');
    welcomeMessage.innerText = msg;
    document.querySelector('.message-container').appendChild(welcomeMessage);
}

function sendUsername() {
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/login');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.withCredentials = true; // Include cookies in the request

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                let res= JSON.parse(xhr.responseText);
                console.log(res);
                let welcomeMsg = res['message'];
                console.log(welcomeMsg);
                getMessages();
                // Handle the response
            } else {
                console.error('Error:', xhr.status, xhr.statusText);
            }
        }
    };

    xhr.send(JSON.stringify({ username: USERNAME }));
    console.log("Username sent");
    
}
function appendMessages(messages) {

    messages.forEach(message => {
        message=JSON.parse(message);
        createMessage(message.username, message.timestamp, message.message,message.id);
    });

}

function getMessages() {
    let xhr = new XMLHttpRequest();
    // xhr.open('GET', `/api/messages?limit=${MSG_LIMIT}`);
    xhr.open('GET', `/api/messages`);
    xhr.withCredentials = true; // Include cookies in the request
   // Handle successful response
    xhr.onload = function() {
        if (xhr.status === 200) {

            console.log("Success:", xhr.responseText);

            let messages = JSON.parse(xhr.responseText);
            if (messages.length > 0){
                appendMessages(messages);
            }

        } 
        else {
            console.error("Request completed but failed. Status:", xhr.status, "Status Text:", xhr.statusText);
        }
    };

    // Handle network errors
    xhr.onerror = function() {
        console.error("Network Error: Unable to complete the request.");
    };

  
    xhr.send();
}

function getLastMessages(msgID) {
    let xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/messages?last=' + encodeURIComponent(msgID));
    xhr.withCredentials = true; // Include cookies in the request
   // Handle successful response
    xhr.onload = function() {
        if (xhr.status === 200) {

            console.log("Success:", xhr.responseText);

            let messages = JSON.parse(xhr.responseText);
            console.log(messages);
            if(messages.length > 0){
                appendMessages(messages);
                console.log(messages[messages.length - 1]);
            }

        } else {

            console.error("Request completed but failed. Status:", xhr.status, "Status Text:", xhr.statusText);

        }
    };

    // Handle network errors
    xhr.onerror = function() {
        console.error("Network Error: Unable to complete the request.");
    };

  
    xhr.send(JSON.stringify({"id":msgID}));
}

function pollMessages() {
    setInterval(function() {
        getLastMessages(lastMsgId);
    }, 5000);
}

document.addEventListener('DOMContentLoaded', function() {
    pollMessages();
    document.querySelector(".send").addEventListener('click', function() {
    });
});

function deleteMessages(msgID) {
    let xhr = new XMLHttpRequest();
    xhr.open('DELETE', `/api/messages?ID=${msgID}`);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.withCredentials = true; // Include cookies in the request

    xhr.onload = function() {
        if (xhr.status === 200) {
            console.log("Success:", xhr.responseText);
        } else {
            console.error("Request completed but failed. Status:", xhr.status, "Status Text:", xhr.statusText);
        }
    };

    // Handle network errors
    xhr.onerror = function() {
        console.error("Network Error: Unable to complete the request.");
    };

    xhr.send(JSON.stringify({ username: USERNAME }));
}