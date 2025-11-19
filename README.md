# Team 16

### Authors
Lauren Warren <br>
Fernando Curiel-Moysen (002710521)
<br>
### Video Link
placeholder
<br>

### Summary
We have created a Chat Server that can handle multiple clients over an internet connection. These clients communicate with the server and accept basic commands that allow for client modifications and personalizations. Beginning with the protocol module, we have the handling for the encoding and decoding of the JSON objects. This is how all of the communication between the client and the server is actually received and sent between each other. This module converts JSON strings to Python modules and vice versa. Objects are sent over sockets, converted into strings, encoded, retrieved from the socket, decoded, and then checked for any whitespaces before or after the data. The line of text is then received over a socket and converted into a Python object. This is how the clients can communicate with the server.

The chat server handles any and all clients (and their messages) that connect over the network. We first import the sendObject and receiveObject functions from our protocol so that the encoded and decoded data can be sent and received. We also used the socket, threading, and argparse modules to handle the communication over the network connection, allow for multiple channels and servers to connect, and to handle the arguments being passed with each command, respectively. We then included  the time module to handle the time out after idling feature and the period of rest for the server. The chat server communication begins with a function aptly named, ChatServer. This function begins by intitializing the variables that will be used throughout the connection so that varying functions (i.e. connecting to a port, setting the debug level, storing chosen nicknames, etc) can operate at the highest level. We included a logging function so that the server messages and user activity could be logged. The server is started by creating a TCP socket that is binded to all interfaces on the specific port. The socket is then able to listen for any incoming connections from clients. This function checks for any idleness of the server over 3 minutes, makes sure there are no more than 4 threads connected at once, and shows the logging message that is sent once a client is successfully connected. It also shows the message that is sent if the user presses ctrl-c. The function for handling client connections initalizes with the client not yet having a nickname or having joined a channel. We then receive the user's keyboard input as an object over the socket that is interpreted as one of the many commands that will be listed below. If the connection is severed or the user disconnects, the cleanup process begins where all of the user information is cleaned out to prevent against server corruption. The processingCommands function includes conditional statements for all of the possible user commands. Each of the commands has a function that sends objects over the socket based on what the user is entering. The main function handles the very beginning of connection to the server and allows for the reading of arguments that are trying to parsed during connection attempts. 
*describe chat client*

<br>

### How to run
1. Navigate to the folder path where the files are located.
2. If you are running Homebrew, create a local venv in the terminal
- `python -m venv venv_name name`
- `source venv_name/bin/activate`
3. Install colorama
- `python3 -m pip install colorama`
4. Start the chat server
- `python3 ChatServer.py -p 5050` (port number can be changed)
5. Start chat client in a **separate** terminal while the serving is running
- `python3 ChatClient.py`

<br>

### Testing
We tested the functionality of this program while incrementaly building it. We used unit testing to test each function and feature after being built. Integration testing was also helpful because we were able to test how different parts of the server work together to be able to handle multiple clients. Lastly, we tested the program as a whole which included starting the server and multiple clients. The clients made several calls to the server and we excpected the server to respond appropiately. We also used a table along the way to keep track of which features worked and which didn't. 

| Test Case | Description | Input | Expected Outcome | Actual Outcome | 
| ----------- | ----------- | ----------- | ----------- | ----------- |
|  | Title |
| Paragraph | Text |
<br>

### Reflection

<br>