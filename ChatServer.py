#this is the chat server that handles any and all of the clients connecting over the network and sending/receiving messages
import socket#import socket module for communication over the network
import threading#import threading module to allow multiple tasks to be run at once while over the same process
import argparse#import argparse module to handle command line arguments
import time#import time module to handle the time out after 3 minutes of inactivity and the period of server rest/idle time
from protocol import send_object, recv_object#imports send_object and recv_object functions from protocol.py for sending and receiving messages
MAX_THREADS = 4#sets the maximum number of threads allowed to 4

#starts the ChatServer communication over the network
class ChatServer:
    def __init__(self, port, debug):#ChatServer initialization function that takes the instance of the class, the port number, and the debug level
        self.port = port#sets the port number for the server
        self.debug = debug#sets the debug level for the server
        self.clients = {}#creates an empty dictionary to hold the connected clients
        self.nicknames = set()#creates an empty set to hold the nicknames of connected users
        self.channels = {}#creates an empty dictionary to hold the channels and which users are in them  
        self.lock = threading.Lock()#creates a threading lock to prevent data crashes from handling of multiple clients accessing the same resources
        self.last_activity = time.time()#variable to store the current timestamp for idle shutdown
        self.thread_limit = threading.Semaphore(MAX_THREADS)

    def log(self, msg):#function to log messages when debug level is set to 1
        if self.debug == 1:#for when debug level is 1
            print("[DEBUG]", msg)#prints the debug message out
            
    #start the chatserver listening for client connections
    def start(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#creates a TCP socket for the server
        server_sock.bind(("", self.port))#binds the socket to all interfaces on the specified port
        server_sock.listen(5)#starts listening for any and all incoming connections
        print(f"ChatServer is listening on port {self.port}")#prints out that the server is listening on the specified port
        try:#for handling keyboard interrupts to shut down the server cleanly
            while True:#while the server is currently running
                if time.time() - self.last_activity > 180:#checks if the server has been idle for more than 3 minutes or 180 seconds
                    print("The server has been idle for 3 minutes. It is now shutting down.")#prints out that the server is shutting down due to inactivity
                    break#breaks out of the loop to shut down the server
                
                #limiting the number of threads to prevent data corruption from overload
                # if threading.active_count()-1 >= MAX_THREADS:#checks if the number of active threads minus the main thread is greater than or equal to the maximum allowed threads
                #     time.sleep(0.1)#lets the server rest for a short time before checking again
                #     continue#continues to the next iteration of the loop
                server_sock.settimeout(1)#sets a timeout of 1 second for allowing the acceptance of new connections
                
                try:#tries to accept a new client connection
                    client_sock, addr = server_sock.accept()#successfully accepts a new client connection
                    self.log(f"Accepted connection from {addr}")#logs the accepted connection when debug level is set to 1
                except socket.timeout:#handles the exception for when the timeout period is reached without a new connection
                    continue#continues to the next iteration of the loop if no connection was made within the timeout period
                self.last_activity = time.time()#updates the last activity timestamp to the current time
                
                self.thread_limit.acquire()#gets the thread limit semaphore before starting a new thread
                threading.Thread(target=self.handle_client, args=(client_sock,), daemon=True).start()#starts a new thread to handle the connected client
                
        except KeyboardInterrupt:#handles the keyboard interrupt exception for clean shutdown with Ctrl-C
            print("\nThe server is shutting down from Ctrl-C...")
        finally:
            server_sock.close()#finally closes the server socket when the server is shutting down
    
    #function to handle the individual client connections
    def handle_client(self, sock):
        user = {"nickname": None, "channels": set()}#initializes a user dictionary to hold the nickname and channels for the connected client
        self.clients[sock] = user#adds the connected client socket and user info to the clients dictionary
        try:#attempts to handle communication with the connected client
            while True:#while the client is connected
                obj = recv_object(sock)#receives an object from the client socket
                if obj is None:#if no object is received
                    break#the loop is broken and the client is disconnected
                if obj == "":#if the message is empty
                    continue#continues to the next iteration of the loop because there is no message to process
                if obj.get("type") != "command":#if the object is not a valid command
                    continue#continues to the next iteration of the loop because the command was invalid
                self.process_command(sock, user, obj)#process the valid command received from the client
        except Exception as e:#handles any errors that occur during client communication
            self.log(f"There is a client error: {e}")#logs the client error
        finally:
            self.cleanup_client(sock)#finally cleans up the client connection when done
            self.thread_limit.release()#releases the thread limit semaphore when done handling the client
    
    #function to process valid commands
    def process_command(self, sock, user, obj):#processes the command received from the client
        cmd = obj["command"]#retrieves the valid command from the received object
        args = obj.get("args", [])#retrieves any arguments associated with the command (i.e. channel name, nickname, etc.)
        if cmd == "nick":#if the command is to pick a nickname
            self.handle_nick(sock, user, args)#calls the handle_nick function to process the nickname command
        elif cmd == "list":#if the command is to list channels and the number of users in each channel
            self.handle_list(sock, user)#calls the handle_list function to process the list command
        elif cmd == "join":#if the command is to join a channel
            self.handle_join(sock, user, args)#calls the handle_join function to process the join command
        elif cmd == "leave":#if the command is to leave a channel
            self.handle_leave(sock, user, args)#calls the handle_leave function to process the leave command
        elif cmd == "quit":#if the command is to disconnect from the server and leave the chat
            send_object(sock, {#sends the object information to the client confirming disconnection
                "type": "info",
                "info": "You have disconnected from the server."
            })
            self.cleanup_client(sock)#cleans up the client connection when done
            return#exits the function after disconnecting
        elif cmd == "help":#if the command is to show the help message
            help_msg = (#prints out the help message with available commands
                "Commands:\n"
                "/nick <nickname>     -pick your nickname\n"
                "/list                -list the channels and the number of users in each channel\n"
                "/join <channel>      -join a channel\n"
                "/leave [<channel>]   -leave a channel or all channels\n"
                "/quit                -disconnect from the server and leave the chat\n"
                "/help                -show this message"
            )
            send_object(sock, {#sends the help message to the client with the available commands
                "type": "info",
                "info": help_msg
            })
    
    #nickname command server-side function
    def handle_nick(self, sock, user, args):#function to handle the /nick command from the client
        if len(args) < 1:#for when no nickname argument is provided
            send_object(sock, {
                "type": "error",
                "error": "There was no nickname provided."
            })#send an error message back to the client that no nickname was provided
            return#exit the function early since there is no nickname to process
        new_nick = args[0]#retrieves the new nickname from the command arguments
        with self.lock:#uses a threading lock to prevent data corruption when accessing shared resources
            if new_nick in self.nicknames:#checks if the new nickname is already being used by another client
                send_object(sock, {
                    "type": "error",
                    "error": "This nickname is already taken."
                })#if the nickname is already being used, send an error message back to the client
                return#exit the function early since the nickname is already being used
            old_nick = user["nickname"]#retrieves the old nickname of the client
            if old_nick in self.nicknames:#for when the old nickname exists in the set of nicknames
                self.nicknames.remove(old_nick)#remove the old nickname from the list of nicknames
            user["nickname"] = new_nick#lets the user pick a new nickname by setting it in the user dictionary
            self.nicknames.add(new_nick)#adds the new nickname to the list of nicknames
        send_object(sock, {
            "type": "event",
            "event": "nick_changed",
            "nickname": new_nick
        })#sends an event object back to the client confirming that the user has changed their nickname
        self.log(f"User set nickname to {new_nick}")#sends a log message that the user has set their nickname
    
    #list command server-side function
    def handle_list(self, sock, user):#function to handle the /list command from the client
        with self.lock:#uses a threading lock to prevent data corruption when accessing shared resources
            channel_info = {#creates a dictionary comprehension to store the channel names and the number of users in each channel
                channel: len(users)#for each channel, get the length of the users set to count the number of users
                for channel, users in self.channels.items()#iterates through each channel and its associated users in the channels dictionary
            }
        send_object(sock, {
            "type": "event",
            "event": "channel_list",
            "channels": channel_info
        })#sends an event object back to the client with the list of channels and the number of users in each channel
    
    #join command server-side function
    def handle_join(self, sock, user, args):#function to handle the /join command from the client
        if len(args) < 1:#for when no channel argument is provided
            send_object(sock, {
                "type": "error",
                "error": "No channel was specified."
            })#send an error message back to the client that the user did not specify a channel that they wanted to join
            return#exit the function early since there is no channel to process
        channel = args[0]#retrieves the channel name that the user would like to joinfrom the command arguments
        with self.lock:#uses a threading lock to prevent data corruption when accessing shared resources
            if channel not in self.channels:#for when the channel does not already exist
                self.channels[channel] = set()#creates a new set for the channel to hold the users that join it
            nickname = user["nickname"]#retrieves the nickname of the user from the user dictionary
            if nickname is None:#for when the user has not picked a nickname yet
                send_object(sock, {
                    "type": "error",
                    "error": "Set nickname first using /nick."
                })#lets the user know that they must pick a nickname first before joining a channel
                return#exit the function early since the user has not picked a nickname yet
            self.channels[channel].add(nickname)#adds the user's nickname to the set of users in the specified channel
            user["channels"].add(channel)#adds the channel to the user's set of joined channels
        send_object(sock, {
            "type": "event",
            "event": "joined_channel",
            "channel": channel
        })#sends an event object back to the client confirming that the user has joined the specified channel
        self.broadcast_to_channel(channel, {#notifies all other clients in the channel that a new user has joined
            "type": "event",
            "event": "user_joined",
            "channel": channel,
            "user": nickname
        }, except_sock=sock)#broadcasts that the user joined the channel to all clients in the channel except for the client who has just joined
        self.log(f"{nickname} has joined {channel}")#logs that the user has joined the specified channel
    
    #leave command server-side function
    def handle_leave(self, sock, user, args):#function to handle the /leave command from the client
        nickname = user["nickname"]#retrieves the nickname of the user from the user dictionary
        if nickname is None:#for when the user has not picked a nickname yet
            send_object(sock, {
                "type": "error",
                "error": "You need to pick a nickname first using /nick."
            })#lets the user know that they must pick a nickname first before leaving a channel
            return#exit the function early since the user has not picked a nickname yet
        if not user["channels"]:#for when the user is not currently in any channels
            send_object(sock, {
                "type": "info",
                "info": "You are not currently a part of any channels."
            })#lets the user know that they are not currently in any channels to leave
            return#exit the function early since the user is not in any channels
        channels_to_leave = [args[0]] if args else list(user["channels"])#determines if a user want to leave all or just one specific channel
        for channel in channels_to_leave:#iterates through each channel that the user wants to leave
            if channel not in user["channels"]:#for when the user is not in the specified channel
                send_object(sock, {
                    "type": "error",
                    "error": f"You are not currently in channel '{channel}'."
                })#lets the user know that they are not in the specified channel that they are trying to leave
                continue#continues to the next iteration of the loop since the user is not in the specified channel
            with self.lock:#uses a threading lock to prevent data corruption when accessing shared resources
                self.channels[channel].discard(nickname)#removes the user's nickname from the set of users in the specified channel
                user["channels"].remove(channel)#removes the channel from the user's set of joined channels
            send_object(sock, {
                "type": "event",
                "event": "left_channel",
                "channel": channel
            })#sends an event object back to the client confirming that the user has left the specified channel
            self.broadcast_to_channel(channel, {
                "type": "event",
                "event": "user_left",
                "channel": channel,
                "user": nickname
            }, except_sock=sock)#notifies all other clients in the channel that the user has left, except for the client who has just left
            self.log(f"{nickname} has left {channel}")#logs that the user has left the specified channel
    
    #cleans up the client connection when done executing
    def cleanup_client(self, sock):#function to clean up the client connection when done executing
        with self.lock:#uses a threading lock to prevent data corruption when accessing shared resources
            if sock not in self.clients:#for when the specified client cannot be found in the clients dictionary
                return#exit the function early since there is no client to clean up
            user = self.clients[sock]#retrieves the user information for the specified client socket
            nick = user.get("nickname")#retrieves the nickname of the user
            if nick in self.nicknames:#for when the nickname exists in the set of nicknames
                self.nicknames.remove(nick)#removes the nickname from the set of nicknames
            for channel in list(user.get("channels", [])):#looks through each channel that the user is in
                self.channels[channel].discard(nick)#removes the user's nickname from the channels that it was a part of
                user["channels"].remove(channel)#removes the channel from the user's set of joined channels
            del self.clients[sock]#removes the client from the clients dictionary
        try:#attempts to close the client socket
            sock.close()#closes the client socket connection
        except:#for when there may be an error when trying to close the socket
            pass#pass if there is an error when trying to close the socket
    
    def broadcast_to_channel(self, channel, obj, except_sock=None):#function to broadcast messages to all clients in a specified channel
        for sock, user in self.clients.items():#looks at each connected client socket and its associated user information
            if sock == except_sock:#for when the socket is the exception socket that should not receive the message
                continue#continues with looking at the next client socket
            if user["nickname"] in self.channels.get(channel, []):#for when the user's nickname is in the set of users for the specified channel
                send_object(sock, obj)#sends the object message to the client socket in the specified channel
                
#main function to start the ChatServer with command line arguments
if __name__ == "__main__":
    parser = argparse.ArgumentParser()#creates an argument parser object to handle command line arguments
    parser.add_argument("-p", type=int, required=True, help="Port")#adds the port argument to the parser
    parser.add_argument("-d", type=int, default=0, help="Debug level 0/1")#adds the debug level argument to the parser
    args = parser.parse_args()#parses the command line arguments
    server = ChatServer(args.p, args.d)#creates a ChatServer instance with the specified port and debug level
    server.start()#starts the ChatServer
