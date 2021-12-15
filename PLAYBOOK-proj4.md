## COS 460/540 - Computer Networks

# Project 4: Octothorpe Server

# Christopher Gifford

This project is written in Python 3.9 on Windows, also recently tested in Unix. The "blessed" python module is required.

## How to compile

No compiling required.

## How to run

Here's how to utilize the client:
```
usage: octothorpe-client.py [-h] [--port p] [--host h] [--root_path r]

A client implementation interfacing with the Octothorpe server        

optional arguments:
  -h, --help     show this help message and exit
  --port p       server port
  --host h       server host
  --root_path r  root directory to client resources
```

Note that the client can only begin running after the octothorpe-server is running. Once both the server and subsequently the client is running, follow the on-screen instructions to first login.

Once you are logged in, the server will provide you with a map and starting position. You can either use the "move" command or the arrow keys to move around the map to find treasures.

As you approach a treasure, a new '#' symbol on the map will appear, indicating you are close to a treasure. The goal is to obtain as many points as possible.

## My experience with this project

Similar to the previous project writing the server, this was a fairly challenging project. The context switch in managing client connection and resources as opposed to server resources made implementation more confusing and harder to wrap my head around. Also, trying to find a UI library (whether that be a GUI or command line UI) in python that worked well with the multi-threading that networking requires, was frustrating.

Nonetheless, it was rewarding to see the octothorpe game be used in a more user-friendly manner and see it really come to life as opposed to the written commands in telnet.
