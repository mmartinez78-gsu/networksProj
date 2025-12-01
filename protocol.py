# this is the protocol module that defines the necessary functions for sending and receiving JSON objects over the socket connection
import json  # import the json module to handle JSON conversions from JSON strings to Python objects and vice versa


def sendObject(sock, obj):  # function to send a JSON object over a socket
    data = json.dumps(obj) + "\n"  # convert the object to a string and adds a newline character
    sock.sendall(data.encode())  # send the encoded data over the socket


def receiveLine(sock):  # function to receive a line of text from the socket until a newline character is encountered
    # attach a buffer attribute if missing
    if not hasattr(sock, "_buffer"):
        sock._buffer = ""

    while True:  # while loop that will continue to read data until a newline character is found
        # if we already have a complete line, extract it
        if "\n" in sock._buffer:  # checks if there are any newline characters in the buffer
            line, sock._buffer = sock._buffer.split("\n", 1)  # split the buffer where the first newline character is found
            return line.strip()  # returns the line without any whitespaces before or after the line

        # need more data
        chunk = sock.recv(1024).decode()  # receives a chunk of data from the socket and decode it
        if not chunk:  # for when there is no more data to read from the socket
            return None  # return None to indicate the end of the data stream

        sock._buffer += chunk


def receiveObject(sock):  # function to receive a JSON object from the socket
    line = receiveLine(
        sock)  # calls the recv_line function to retrieve the line of text that was decoded and added to the buffer from the socket
    if line is None or line.strip() == "":  # for when there is no line received or the line is empty
        return None  # return None to indicate that no object was received
    return json.loads(line)  # convert the JSON string to a Python object
