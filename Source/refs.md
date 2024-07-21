# Resources

- [Basic Python Socket Programming](https://docs.python.org/3/howto/sockets.html#)
- [FTP Socket](https://github.com/hadis98/FTP-Client-Server-Python-Socket-Programming)
- [Fast file transfer UDP Socket](https://github.com/pratiklotia/Client-Server-Fast-File-Transfer-using-UDP-on-Python)
- [further reading](https://github.com/akshayjoshii/socket_programming)
- [Python Socket Programming](https://realpython.com/python-sockets/#handling-multiple-connections)
- [Python Threading](https://realpython.com/intro-to-python-threading)
- [file.flush() explaination](https://stackoverflow.com/questions/7127075/what-exactly-is-file-flush-doing)
- [Sockets Deep Dive into networking fundamentals](https://medium.com/@dhar.ishan04/tcp-connections-and-sockets-deep-dive-into-networking-fundamentals-with-linux-and-python-4c717ca6115)

# Report Refs

- [Example Report](https://github.com/hatradev/HCMUS-ComputerNetwork-Socket/blob/main/Report.pdf)

- [Best for report with comments and explanation](https://thepythoncode.com/article/send-receive-files-using-sockets-python)
- [3-way handshaking](https://medium.com/@dhar.ishan04/tcp-connections-and-sockets-deep-dive-into-networking-fundamentals-with-linux-and-python-4c717ca6115)
- [Python Socket Server](https://iximiuz.com/en/posts/writing-web-server-in-python-sockets/)

# Definitions

- `AF_INET` stands for "Address Family - Internet".
- The `backlog` parameter defines the size of the queue of established but not accepted yet connections. Until the number of connected but not yet being served clients is lower than the backlog size, the operating system will be establishing new connections in the background. However, when the number of such connections reaches the backlog size, all new connection attempts will be explicitly rejected or implicitly ignored (depends on the OS configurations).
- Terminate the connection with the concept of 4-way handshaking.
  - Client sends a FIN packet to the server.
  - Server recvs FIN and sends an ACK packet to the client.
  - Server sends a FIN packet to the client.
  - Client recvs FIN and sends an ACK packet to the server.
- When set nonblocking for socket -> should use `select` module to check if the socket is ready to read/write.
  => Use threading to handle multiple connections.
  - Using multithreading in this project is safe because the server is only reading and writing to the file, not sharing any data between threads => no `race condition` => no use of `lock` => no `deadlock`.
