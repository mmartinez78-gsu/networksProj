# this is the protocol module that defines the necessary functions for sending and receiving JSON objects over the socket connection
import json  # import the json module to handle JSON conversions from JSON strings to Python objects and vice versa

class WrappedSocket:
    def __init__(self, raw_sock):
        self.raw_sock = raw_sock
        # The buffer is now safely initialized on this standard Python object
        self._buffer = ""

        # Delegate I/O methods to the raw socket

    def recv(self, size):
        return self.raw_sock.recv(size)

    def sendall(self, data):
        return self.raw_sock.sendall(data)

    def close(self):
        return self.raw_sock.close()

def sendObject(sock, obj):  # function to send a JSON object over a socket
    data = json.dumps(obj) + "\n"  # convert the object to a string and adds a newline character
    sock.sendall(data.encode())  # send the encoded data over the socket


def receiveLine(sock):  # function to receive a line of text from the socket until a newline character is encountered
    while True:
        # if we already have a complete line, extract it
        if "\n" in sock._buffer:
            line, sock._buffer = sock._buffer.split("\n", 1)
            return line.strip()

        # need more data
        chunk = sock.recv(1024).decode()  # Calls WrappedSocket.recv
        if not chunk:
            return None

        sock._buffer += chunk


def receiveObject(sock):  # function to receive a JSON object from the socket
    line = receiveLine(
        sock)  # calls the recv_line function to retrieve the line of text that was decoded and added to the buffer from the socket
    if line is None or line.strip() == "":  # for when there is no line received or the line is empty
        return None  # return None to indicate that no object was received
    return json.loads(line)  # convert the JSON string to a Python object
