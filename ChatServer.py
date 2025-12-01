# this is the chat server that handles any and all of the clients connecting over the network and sending/receiving messages

# handle font coloring in terminal
from colorama import init, Fore

init(autoreset=True)  # initialize colorama with auto reset to prevent color bleed in terminal

from protocol import WrappedSocket, sendObject, \
    receiveObject  # imports sendObject and receiveObject functions from protocol.py for sending and receiving messages
import socket  # import socket module for communication over the network
import threading  # import threading module to allow multiple tasks to be run at once while over the same process
import argparse  # import argparse module to handle command line arguments
import \
    time  # import time module to handle the time out after 3 minutes of inactivity and the period of server rest/idle time

MAX_THREADS = 4  # sets the maximum number of threads allowed to 4

# starts the ChatServer communication over the network
class ChatServer:
    def __init__(self, port,
                 debug, clientTimeout):  # ChatServer initialization function that takes the instance of the class, the port number, and the debug level
        self.port = port  # sets the port number for the server
        self.debug = debug  # sets the debug level for the server
        self.clients = {}  # creates an empty dictionary to hold the connected clients
        self.nicknames = set()  # creates an empty set to hold the nicknames of connected users
        self.channels = {}  # creates an empty dictionary to hold the channels and which users are in them
        self.lock = threading.Lock()  # creates a threading lock to prevent data crashes from handling of multiple clients accessing the same resources
        self.recentActivity = time.time()  # variable to store the current timestamp for idle shutdown
        self.clientTimeout = clientTimeout  # the amount of idle time by a client before disconnecting them (0 is disabled)
        self.recentClientActivity = {}  # creates an empty dictionary to store the time of the last message from each client
        self.thread_limit = threading.Semaphore(MAX_THREADS)
        self.threads = []
        self.commands = {  # Dictionary of commands and corresponding functions
            "nick": self.Nicknames,
            "list": self.List,
            "who": self.Who,
            "join": self.Join,
            "say": self.Say,
            "msg": self.Msg,
            "leave": self.Leave,
            "quit": self.Quit,
            "help": self.Help
        }

    def logging(self, msg):  # function to log messages when debug level is set to 1
        if self.debug == 1:  # for when debug level is 1
            print(Fore.BLUE + "server log: ", msg)  # prints the debug message out

    # start the chatserver listening for client connections
    def startServer(self):
        netSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # creates a TCP socket for the server
        netSock.bind(("", self.port))  # binds the socket to all interfaces on the specified port
        netSock.listen(5)  # starts listening for any and all incoming connections
        print(
            Fore.GREEN + f"ChatServer is listening on port {self.port}")  # prints out that the server is listening on the specified port
        try:  # for handling keyboard interrupts to shut down the server cleanly
            while True:  # while the server is currently running
                if time.time() - self.recentActivity > 180:  # checks if the server has been idle for more than 3 minutes or 180 seconds
                    print(
                        Fore.YELLOW + "The server has been idle for 3 minutes. It is now shutting down.")  # prints out that the server is shutting down due to inactivity
                    break  # breaks out of the loop to shut down the server


                # Loops through clients and disconnects if a timeout is detected
                if self.clientTimeout > 0:
                    for client in list(self.recentClientActivity.keys()):
                        if time.time() - self.recentClientActivity[client] > self.clientTimeout:
                            sendObject(client, {
                                "type": "info",
                                "info": f"You have been disconnected from the server due to inactivity for {self.clientTimeout} seconds."
                            })
                            self.quitProcess(client)

                netSock.settimeout(1)  # sets a timeout of 1 second for allowing the acceptance of new connections
                try:  # tries to accept a new client connection
                    chatClientSock, address = netSock.accept()  # successfully accepts a new client connection
                    wrapped_socket = WrappedSocket(chatClientSock)
                    self.logging(
                        Fore.BLUE + f"Accepted connection from {address}")  # logs the accepted connection when debug level is set to 1
                except socket.timeout:  # handles the exception for when the timeout period is reached without a new connection
                    continue  # continues to the next iteration of the loop if no connection was made within the timeout period
                self.thread_limit.acquire()  # gets the thread limit semaphore before starting a new thread

                with self.lock:
                    self.threads = [th for th in self.threads if th.is_alive()]  # cleanup dead threads
                t = threading.Thread(target=self.clientConnections, args=(wrapped_socket,))
                t.start()  # starts a new thread to handle the connected client
                with self.lock:
                    self.threads.append(t)  # append to thread list to keep track of it

        except KeyboardInterrupt:  # handles the keyboard interrupt exception for clean shutdown with Ctrl-C
            print(Fore.RED + "\nThe server is shutting down from Ctrl-C...")
        finally:
            # Notify all connected clients about server shutdown
            for sock in list(self.clients.keys()):
                try:
                    sendObject(sock, {"type": "info", "info": "Server is shutting down."})
                except Exception as e:
                    self.logging(f"Failed to send shutdown message to a client: {e}")
                finally:
                    self.quitProcess(sock)  # clean up the client socket and internal data

            netSock.close()  # finally closes the server socket when the server is shutting down
            for t in self.threads:
                t.join(timeout=1)

    # function to handle the individual client connections
    def clientConnections(self, sock):
        user = {"nickname": None,
                "channels": set()}  # initializes a user dictionary to hold the nickname and channels for the connected client
        self.clients[sock] = user  # adds the connected client socket and user info to the clients dictionary
        self.recentClientActivity[sock] = time.time()  # set initial inactivity timer for new client
        try:  # attempts to handle communication with the connected client
            while True:  # while the client is connected
                obj = receiveObject(sock)  # receives an object from the client socket
                if obj is None:  # if no object is received
                    break  # the loop is broken and the client is disconnected
                if not isinstance(obj, dict):  # if the message is empty
                    continue  # continues to the next iteration of the loop because there is no message to process
                if obj.get("type") != "command":  # if the object is not a valid command
                    continue  # continues to the next iteration of the loop because the command was invalid
                self.recentClientActivity[sock] = time.time()
                self.takingCommands(sock, user, obj)  # process the valid command received from the client
        except Exception as e:  # handles any errors that occur during client communication
            self.logging(f"There is a client error: {e}")  # logs the client error
        finally:
            self.quitProcess(sock)  # finally cleans up the client connection when done
            self.thread_limit.release()  # releases the thread limit semaphore when done handling the client

    # function to process valid commands
    def takingCommands(self, sock, user, obj):  # processes the command received from the client
        command = obj["command"]  # retrieves the valid command from the received object
        args = obj.get("args",
                       [])  # retrieves any arguments associated with the command (i.e. channel name, nickname, etc.)

        self.recentActivity = time.time()  # updates the last activity timestamp to the current time

        # Execute command if it exists, respond with an error if not
        handler = self.commands.get(command)
        if handler:
            handler(sock, user, args)
        else:
            sendObject(sock, {"type": "error", "error": "Unknown command"})

    # nickname command server-side function
    def Nicknames(self, sock, user, args):  # function to handle the /nick command from the client
        if len(args) < 1:  # for when no nickname argument is provided
            sendObject(sock, {
                "type": "error",
                "error": "There was no nickname provided."
            })  # send an error message back to the client that no nickname was provided
            return  # exit the function early since there is no nickname to process
        newName = args[0]  # retrieves the new nickname from the command arguments
        with self.lock:  # uses a threading lock to prevent data corruption when accessing shared resources
            if newName in self.nicknames:  # checks if the new nickname is already being used by another client
                sendObject(sock, {
                    "type": "error",
                    "error": "This nickname is already taken."
                })  # if the nickname is already being used, send an error message back to the client
                return  # exit the function early since the nickname is already being used
            oldName = user["nickname"]  # retrieves the old nickname of the client
            if oldName in self.nicknames:  # for when the old nickname exists in the set of nicknames
                self.nicknames.remove(oldName)  # remove the old nickname from the list of nicknames
            user["nickname"] = newName  # lets the user pick a new nickname by setting it in the user dictionary
            self.nicknames.add(newName)  # adds the new nickname to the list of nicknames
        sendObject(sock, {
            "type": "event",
            "event": "your name was changed",
            "nickname": newName
        })  # sends an event object back to the client confirming that the user has changed their nickname
        self.logging(f"User set nickname to {newName}")  # sends a log message that the user has set their nickname

    # list command server-side function
    def List(self, sock, user, args):  # function to handle the /list command from the client
        with self.lock:  # uses a threading lock to prevent data corruption when accessing shared resources
            NamesAndNumbers = {
                # creates a dictionary comprehension to store the channel names and the number of users in each channel
                channel: len(users)  # for each channel, get the length of the users set to count the number of users
                for channel, users in self.channels.items()
                # iterates through each channel and its associated users in the channels dictionary
            }
        sendObject(sock, {
            "type": "event",
            "event": "list of channels",
            "channels": NamesAndNumbers
        })  # sends an event object back to the client with the list of channels and the number of users in each channel

    # list nicknames of clients in channel
    def Who(self, sock, user, args):
        if len(args) < 1:  # no channel specified
            sendObject(sock, {
                "type": "error",
                "error": "No channel was specified."
            })
            return

        channel = args[0]  # get the requested channel name
        with self.lock:  # thread-safe access to shared resources
            if channel not in self.channels:  # channel does not exist
                sendObject(sock, {
                    "type": "error",
                    "error": f"Channel '{channel}' does not exist."
                })
                return

            users_in_channel = list(self.channels[channel])  # list of nicknames in the channel

        sendObject(sock, {
            "type": "event",
            "event": "channel users",
            "channel": channel,
            "users": users_in_channel
        })

    # join command server-side function
    def Join(self, sock, user, args):  # function to handle the /join command from the client
        if len(args) < 1:  # for when no channel argument is provided
            sendObject(sock, {
                "type": "error",
                "error": "No channel was specified."
            })  # send an error message back to the client that the user did not specify a channel that they wanted to join
            return  # exit the function early since there is no channel to process
        channel = args[0]  # retrieves the channel name that the user would like to joinfrom the command arguments
        with self.lock:  # uses a threading lock to prevent data corruption when accessing shared resources
            if channel not in self.channels:  # for when the channel does not already exist
                self.channels[channel] = set()  # creates a new set for the channel to hold the users that join it
            nickname = user["nickname"]  # retrieves the nickname of the user from the user dictionary
            if nickname is None:  # for when the user has not picked a nickname yet
                sendObject(sock, {
                    "type": "error",
                    "error": "Set nickname first using /nick."
                })  # lets the user know that they must pick a nickname first before joining a channel
                return  # exit the function early since the user has not picked a nickname yet
            self.channels[channel].add(
                nickname)  # adds the user's nickname to the set of users in the specified channel
            user["channels"].add(channel)  # adds the channel to the user's set of joined channels
        sendObject(sock, {
            "type": "event",
            "event": "you joined a channel",
            "channel": channel
        })  # sends an event object back to the client confirming that the user has joined the specified channel
        self.tellAll(channel, {  # notifies all other clients in the channel that a new user has joined
            "type": "event",
            "event": "a user joined a channel",
            "channel": channel,
            "user": nickname
        },
                     except_sock=sock)  # broadcasts that the user joined the channel to all clients in the channel except for the client who has just joined
        self.logging(f"{nickname} has joined {channel}")  # logs that the user has joined the specified channel

    def Say(self, sock, user, args):
        nickname = user["nickname"]
        if nickname is None:
            sendObject(sock, {
                "type": "error",
                "error": "You must set a nickname first using /nick."
            })
            return

        if len(args) < 2:
            sendObject(sock, {
                "type": "error",
                "error": "Usage: /say <channel> <message>"
            })
            return

        channel = args[0]
        message = " ".join(args[1:])

        with self.lock:
            if channel not in user["channels"]:
                sendObject(sock, {
                    "type": "error",
                    "error": f"You are not in channel '{channel}'. Join it first using /join <channel>."
                })
                return

            self.tellAll(channel, {
                "type": "message",
                "channel": channel,
                "user": nickname,
                "message": message
            })

        self.logging(f'{nickname} said in {channel}: "{message}"')

    def Msg(self, sock, user, args):
        sender = user["nickname"]
        if sender is None:
            sendObject(sock, {
                "type": "error",
                "error": "You must set a nickname first using /nick."
            })
            return

        if len(args) < 2:
            sendObject(sock, {
                "type": "error",
                "error": "Usage: /msg <nickname> <message>"
            })
            return

        target_nick = args[0]
        message = " ".join(args[1:])

        # Find the socket of the target nickname
        target_sock = None
        with self.lock:
            for s, u in self.clients.items():
                if u["nickname"] == target_nick:
                    target_sock = s
                    break

        if target_sock is None:
            sendObject(sock, {
                "type": "error",
                "error": f"User '{target_nick}' not found."
            })
            return

        # Send message to the target user
        sendObject(target_sock, {
            "type": "message",
            "from": sender,
            "message": message
        })

        # Optionally, confirm to the sender that the message was sent
        sendObject(sock, {
            "type": "info",
            "info": f"Message sent to {target_nick}."
        })

        self.logging(f'{sender} -> {target_nick}: "{message}"')

    # leave command server-side function
    def Leave(self, sock, user, args):  # function to handle the /leave command from the client
        nickname = user["nickname"]  # retrieves the nickname of the user from the user dictionary
        if nickname is None:  # for when the user has not picked a nickname yet
            sendObject(sock, {
                "type": "error",
                "error": "You need to pick a nickname first using /nick."
            })  # lets the user know that they must pick a nickname first before leaving a channel
            return  # exit the function early since the user has not picked a nickname yet
        if not user["channels"]:  # for when the user is not currently in any channels
            sendObject(sock, {
                "type": "info",
                "info": "You are not currently a part of any channels."
            })  # lets the user know that they are not currently in any channels to leave
            return  # exit the function early since the user is not in any channels
        leavingChannels = [args[0]] if args else list(
            user["channels"])  # determines if a user want to leave all or just one specific channel
        for channel in leavingChannels:  # iterates through each channel that the user wants to leave
            if channel not in user["channels"]:  # for when the user is not in the specified channel
                sendObject(sock, {
                    "type": "error",
                    "error": f"You are not currently in channel '{channel}'."
                })  # lets the user know that they are not in the specified channel that they are trying to leave
                continue  # continues to the next iteration of the loop since the user is not in the specified channel
            with self.lock:  # uses a threading lock to prevent data corruption when accessing shared resources
                self.channels[channel].discard(
                    nickname)  # removes the user's nickname from the set of users in the specified channel
                user["channels"].remove(channel)  # removes the channel from the user's set of joined channels
            sendObject(sock, {
                "type": "event",
                "event": "you left a channel",
                "channel": channel
            })  # sends an event object back to the client confirming that the user has left the specified channel
            self.tellAll(channel, {
                "type": "event",
                "event": "a user left the channel",
                "channel": channel,
                "user": nickname
            },
                         except_sock=sock)  # notifies all other clients in the channel that the user has left, except for the client who has just left
            self.logging(f"{nickname} has left {channel}")  # logs that the user has left the specified channel

    def Quit(self, sock, user, args):
        sendObject(sock, {  # sends the object information to the client confirming disconnection
            "type": "info",
            "info": "You have disconnected from the server."
        })
        self.quitProcess(sock)  # cleans up the client connection when done
        return  # exits the function after disconnecting

    def Help(self, sock, user, args):
        helpMessage = (  # prints out the help message with available commands
            "Commands:\n"
            "/nick <nickname>         -pick your nickname\n"
            "/list                    -list the channels and the number of users in each channel\n"
            "/who <channel>           -list the nicknames of all users in the specified channel\n"
            "/join <channel>          -join a channel\n"
            "/say <channel> <text>    -send a message to the specified channel (must already be joined)\n"
            "/msg <nickname> <text>   -send a private message to a specified user\n"
            "/leave [<channel>]       -leave a channel or all channels\n"
            "/quit                    -disconnect from the server and leave the chat\n"
            "/help                    -show this message"
        )
        sendObject(sock, {  # sends the help message to the client with the available commands
            "type": "info",
            "info": helpMessage
        })

    # cleans up the client connection when done executing
    def quitProcess(self, sock):  # function to clean up the client connection when done executing
        with self.lock:  # uses a threading lock to prevent data corruption when accessing shared resources
            if sock not in self.clients:  # for when the specified client cannot be found in the clients dictionary
                return  # exit the function early since there is no client to clean up
            user = self.clients[sock]  # retrieves the user information for the specified client socket
            nick = user.get("nickname")  # retrieves the nickname of the user
            if nick in self.nicknames:  # for when the nickname exists in the set of nicknames
                self.nicknames.remove(nick)  # removes the nickname from the set of nicknames
            for channel in list(user.get("channels", [])):  # looks through each channel that the user is in
                self.channels[channel].discard(
                    nick)  # removes the user's nickname from the channels that it was a part of
                user["channels"].remove(channel)  # removes the channel from the user's set of joined channels
            del self.recentClientActivity[sock]  # removes the client from the timeout dictionary
            del self.clients[sock]  # removes the client from the clients dictionary
        try:  # attempts to close the client socket
            sock.close()  # closes the client socket connection
        except:  # for when there may be an error when trying to close the socket
            pass  # pass if there is an error when trying to close the socket

    def tellAll(self, channel, obj,
                except_sock=None):  # function to broadcast messages to all clients in a specified channel
        for sock, user in self.clients.items():  # looks at each connected client socket and its associated user information
            if sock == except_sock:  # for when the socket is the exception socket that should not receive the message
                continue  # continues with looking at the next client socket
            if user["nickname"] in self.channels.get(channel,
                                                     []):  # for when the user's nickname is in the set of users for the specified channel
                sendObject(sock, obj)  # sends the object message to the client socket in the specified channel


# main function to start the ChatServer with command line arguments
if __name__ == "__main__":
    parser = argparse.ArgumentParser()  # creates an argument parser object to handle command line arguments
    parser.add_argument("-p", type=int, required=True, help="Port")  # adds the port argument to the parser
    parser.add_argument("-d", type=int, default=0,
                        help="Debug level 0/1")  # adds the debug level argument to the parser
    parser.add_argument("-t", type=int, default=0, help="Amount of inactive seconds to time out client (0 = disabled)")
    args = parser.parse_args()  # parses the command line arguments
    server = ChatServer(args.p, args.d, args.t)  # creates a ChatServer instance with the specified port and debug level
    server.startServer()  # starts the ChatServer
