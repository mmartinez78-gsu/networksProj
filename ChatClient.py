#this is the text based chat client that connect to the server and takes no command line arguments
import socket#brings in the socket module so that the client can communicate over the network
import threading#threading module will allow for multiple tasks to be run at once while over the same process
from email.mime.text import MIMEText#formatting for the text to be used with messages being sent and received
from protocol import send_object, recv_object#gets these modules from protocol.py for sending and receiving messages
#start the ChatClient  
class ChatClient:
    def __init__(self):
        self.sock = None#initialize with None because there is no connection over a network yet
        self.nickname = None#initialize with None because the user has not set a nickname yet
    #begin connection to server
    def connect(self, host, port):#connect function that will take the instance of the class, the server address, and the server port number
        if self.sock is not None:#for when there is already a connection over the network
            print("You are already connected to a server. Try /quit first.")
            return
        try:#for when the user is not already connected to a server and a new connection can be made
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#create socket object at specific IPv4 address and TCP connection for socket type
            self.sock.connect((host, port))#connect to the server using the retrieved host and port
            print(f"Connected to {host}:{port}")#print confirmation the you are now connected to the server at a specific host and port
            threading.Thread(target=self.listen_loop, daemon=True).start()#create new thread object that will be continuously listening for any and all incoming messages from the server
        except Exception as e:#if the connection fails for any reason, an error message will be printed
            print("The connection failed:", e)
            self.sock = None#will reset the socket to None since the connection was not successful
    #threaded listener function for incoming messages from the server to the client
    def listen_loop(self):
        while True:#while the thread is looping to listen for incoming messages
            try:
                msg = recv_object(self.sock)#receives an object from the server over the network socket
                if msg is None:#if there is no message received, the server has disconnected
                    print("The server has disconnected.")
                    self.sock.close()#close the socket connection
                    self.sock = None#will reset the socket to None since there is no longer a connection
                    break#thread breaks out of the listening loop
                print(msg)#print the received message to the console for the user to see
            except Exception as e:#if there is an error receiving the message, an error message will be printed
                print("There was an error trying to receive your message", e)
                break#thread breaks out of the listening loop
    #possible user input commands that are sent to the server
    def input_loop(self):
        while True:#continuously loops to wait for user input
            text = input("> ").strip()#has > to prompt the user for input and .strip() to remove any whitespaces before or after the input
            if not text:#for when the user inputs nothing and just hits enter
                continue#it will continue to prompt the user for input
            #possible commands for the user to input
            if text.startswith("/connect"):#for when the user inputs the /connect command to attempt connection to a server
                parts = text.split()#split the input text into parts based on whitespace
                if len(parts) < 2:#for if the user forgets to include the host address and/or port number
                    print("Use this format: /connect <host> [port]")#provides user with correct format for the command
                    continue#continues to prompt the user for input
                host = parts[1]#retrieves the host address from the input
                port = 12345#default port number
                if len(parts) > 2:#for when the user provides a port number
                    port = int(parts[2])#retrieves the port number from the input and converts it to an integer
                self.connect(host, port)#attempts to connect to the server using the provided host and port
                
            elif text.startswith("/nick"):#for when the user inputs the /nick command to set their nickname
                if self.sock is None:#for when there is no connection to a server yet
                    print("To set a nickname, you must /connect to a server first.")#lets the user know that they must connect to a server before setting a nickname
                    continue#continues to prompt the user for input
                parts = text.split(maxsplit=1)#splits the input text into parts based on whitespace, command entered and nickname chosen
                if len(parts) < 2:#for when the user forgets to include a nickname
                    print("Use this format: /nick <nickname>")#provides user with correct format for the command
                    continue#continues to prompt the user for input
                self.nickname = parts[1]#retrieves the nickname from the input
                send_object(self.sock, {"type": "command", "command": "nick", "args": [self.nickname]})#sends the nickname to the server as a command object to set the user's nickname

            elif text.startswith("/list"):#for when the user inputs the /list command to request a list of available channels and the number of users in each channel
                if self.sock is None:#for when there is no connection to a server yet
                    print("To see a list of available channels and the # of users for each channel, you must /connect to a server first.")#lets the user know that they must connect to a server before requesting a list
                    continue#continues to prompt the user for input
                send_object(self.sock, {"type": "command", "command": "list"})#sends the list command to the server as a command object to request the list of channels and # of users per channel

            elif text.startswith("/join"):#for when the user inputs the /join command to join a specific channel
                if self.sock is None:#for when there is no connection to a server yet
                    print("To join a channel, you must /connect to a server first.")#lets the user know that they must connect to a server before joining a channel
                    continue#continues to prompt the user for input
                parts = text.split(maxsplit=1)#splits the input text into parts based on whitespace, command entered and channel name
                if len(parts) < 2:#for when the user forgets to include a channel name
                    print("Use this format: /join <channel>")#provides user with correct format for the command
                    continue#continues to prompt the user for input
                channel = parts[1]#retrieves the channel name from the input
                send_object(self.sock, {"type": "command", "command": "join", "args": [channel]})#sends the join command to the server as a command object to join the specified channel
                
            elif text.startswith("/leave"):#for when the user inputs the /leave command to leave a channel
                if self.sock is None:#for when there is no connection to a server yet
                    print("To leave a channel, you must /connect to a server first.")#lets the user know that they must connect to a server before leaving a channel
                    continue#continues to prompt the user for input
                parts = text.split(maxsplit=1)#splits the input text into parts based on whitespace, command entered and channel name
                args = [parts[1]] if len(parts) > 1 else []#retrieves the channel name if provided
                send_object(self.sock, {"type": "command", "command": "leave", "args": args})#sends the leave command to the server as a command object to leave the specified channel

            elif text.startswith("/quit"):#for when the user inputs the /quit command to disconnect from the server and exit the client
                send_object(self.sock, {"type": "command", "command": "quit"})#sends the quit command to the server as a command object to disconnect from the server and leave the chat
                try:#attempts to receive any final messages from the server before disconnecting
                    obj = recv_object(self.sock)#receives an object from the server over the network socket
                    if obj:#if there is a message received from the server
                        print(obj.get("info", obj))#prints the received message to the console for the user to see
                except:#for when there is an error receiving the message
                    pass#ignore the error and proceed to disconnect
                    self.sock.close()#closes the socket connection
                    self.sock = None#resets the socket to None and disconnects from the server
                print("You have disconnected from the server.")#lets the user know they have disconnected from the server
                break#breaks out of the input loop and exits the client

            elif text.startswith("/help"):#for when the user inputs the /help command to see a list of available commands
                print("Here are your available commands:")
                print("/connect <host> [port] -connect to a server")
                print("/nick <nickname>       -set your nickname")
                print("/list                  -list channels and the number of users in each channel")
                print("/join <channel>        -join a channel")
                print("/leave [<channel>]     -leave a channel")
                print("/quit                  -leave the chat and disconnect from the server")
                print("/help                  - print this message")

            else:#for when the user inputs an unknown command
                print("Unknown command. Type /help for a list of commands.")
                continue#continues to prompt the user for input

#calls the ChatClient class and starts the input loop for the user to be able to begin entering commands
if __name__ == "__main__":
    client = ChatClient()
    client.input_loop()
