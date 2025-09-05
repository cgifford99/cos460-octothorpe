## COS 460/540 - Computer Networks

# Project 3: Octothorpe Server

# Christopher Gifford

This project is written in Python 3.9 on Windows.

## How to compile

No compiling required.

## How to run

Here's how to utilize the server:

```
usage: octothorpeServer.py [-h] [--port p] [--root_path r]

An implementation of Octothorpe with sockets and a custom protocol

optional arguments:
  -h, --help     show this help message and exit
  --port p       port to bind server
  --root_path r  root directory to game resources
```

Once the server is running, use telnet on the server port to start playing the game. Then follow the on-screen instructions and play the game according to the specifications in the written document.

## My experience with this project

This project definitely challenged my skills as a software developer as I've not written something like this from scratch, alone before. The most challenging compenent of the project was ensuring the appropriate functionality received their own thread. Inter-thread communication is not something I've dealt with outside of C on Unix, so working in python on Windows was a new experience for me. Also working with multiple threads combined with server-client interaction wasn't something I've worked with before either.

Despite the challenges, it was incredibly rewarding to have built a program of this nature and of this size. I look forward to building a client for the next section of this project.
