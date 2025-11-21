# Team 16

### Authors
Lauren Warren (002672844) <br>
Fernando Curiel-Moysen (002710521)
<br>
### Video Link
[YouTube video for presentation](https://youtu.be/GBtwiPCMIps)
<br>

### Summary/Guide
**see manifestGuide.md file**

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
6. Connect to server from client
- `/connect localhost 5050`
7. Begin entering commands, start with creating a nickname
- `/nick insert_name_here`
8. Use /help to see what other commands are available to you!
9. Open up to 3 additional terminals to try out the multi-channel, multi-threaded feature


<br>

### Testing
We tested the functionality of this program while incrementally building it. We used unit testing to test each function and feature after being built. Integration testing was also helpful because we were able to test how different parts of the server work together to be able to handle multiple clients. We started out by looking at how one client would behave when trying to connect to the server. After some trial and error, we managed to get the one client to be fully functional, but had a few issues with the quit and ctrl-c implementation. Most of the confusion with this portion of the project was aided by ChatGPT, in that, we could better understand what the skeleton structure of our quit and ctrl-c functions should look like. It helped us to visualize which attributes were unnecessary to the functions and which attributes needed to be implemented immediately. Once we got those bugs straightened out, we were able to move on to implementing functionality for multiple channels at a time. This stage of the process was not too difficult, as it simply involved creating a dictionary to store the channels and the users that occupied/left them at any time. The most difficult portion came when trying to figure out the behavior for multiple clients operating at once AND providing multiple channels. We had to find a way to assign each client its own thread, which is where generative AI lended a helping hand. We needed to know how we could create a thread for each client and allow them to run concurrently without using daemon since it was resulting in terminating too soon. Our interactions with generative AI were documented and can be found in a file titled ai_interactions.md. As we moved along through the connection process and kept on trying to get multiple servers and multiple channels to work concurrently, we made sure to frequently run the program along the way so as to debug any smaller errors that popped up along the way. Lastly, we tested the program as a whole which included starting the server and multiple clients. The clients made several calls to the server and we expected the server to respond appropriately. We also used a table along the way to keep track of which features worked and which didn't. 

| Test Case | Description | Input | Expected Outcome | Actual Outcome | 
| ----------- | ----------- | ----------- | ----------- | ----------- |
| client connect to server | client attempts to connect to correct chat server with correct port number | /connect localhost 5050 | client successfully connects to chat server | client successfully connects to chat server and corresponding message is shown |
| client connect to server | client attempts to connect to correct chat server with incorrect port number | /connect localhost 5051 | client unsuccessfully connects to chat server | client fails to connect to chat server and corresponding message is shown |
| client picks nickname | client attempts to self assign a nickname when connected to the server | /nick nickname | nickname is assigned to the user successfully | nickname is assigned to user and message is displayed |
| client picks nickname | client attempts to assign nickname that is already taken | /nick nickname | nickname will not be assigned and display message | nickname is nickname is not assigned and an error message is shown in the output |
| show list of channels | client will enter command to show the list of available channels to join while connected to server | /list | an output is shown with the list of available servers | an output is shown with the list of available servers |
| joining a channel | client will try to enter a channel not yet created | /join channel1 | server creates the channel and client auto joins | server created the channel and placed the user in the channel; an output listing the channel is displayed |
| leaving a channel | client will attemp to leave a channel without being in a channel | /leave | error message is show | an error message is shown in the output stating the client is not a part of any channel |
| leaving a channel | client will attemp to leave a channel | /leave | client successfully leaves channel | client leaves channel and a message is displayed stating which channel was left|
| disconnect from server | client wants to disconnect from the server | /quit | client leaves the server | client disconnects from the server and a message is displayed to confirm this |
| show list of commands | client doesn't know which commands are available and uses command to display the options | /help | a list of commands is shown | a list of commands is shown in the output along with their descriptions |
<br>

### Reflection
All in all, this project was a great way to test our knowledge of what we've learned so far in the course. It provided a refreshing throwback to the TCP/UDP mini project we had earlier on in the semester and also had some similarities to the wireshark lab assignments. While there were parts that were more difficult to complete than others, many of the functions were alike which made them easier to replicate when it came to writing one after the other. The internet relay chat protocol link also came in handy when trying to understand how the channels and clients should behave and be named. It also helped to see what the message formatting should look like for every log message that appeared in the client. This resource was most useful in understanding the overall concept of the project and how the general structure of our project should appear. While we were both responsible for testing the connection and debugging throughout the entirety of the project, Lauren most focused on getting the initial chat protocol commands working and designing their functions while Fernando focused more on getting the multi-threading connection. As of November 20, 2025, Matthew Martinez has not communicated with fellow group members, despite attempts via discord, and made 0 contributions to the project.

<br>
