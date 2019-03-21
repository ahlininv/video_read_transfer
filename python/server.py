__author__ = 'xxx'

import sys, time
from select import select
from socket import socket, AF_INET, SOCK_STREAM


def now():
    return time.ctime()


my_host = ''
my_port = 50007
if len(sys.argv) == 3:
    my_host, my_port = sys.argv[1:]
num_port_socks = 2 # number of ports for connecting of new clients

# create main sockets for accepting of new connection requests
mainsocks, readsocks, writesocks = [], [], []
for i in range(num_port_socks):
    portsock = socket(AF_INET, SOCK_STREAM)
    portsock.bind((my_host, my_port))
    portsock.listen(5)
    mainsocks.append(portsock)
    readsocks.append(portsock)
    my_port += 1

print("Select server loop starting")
while True:
    # print readsocks
    readables, writeables, exceptions = select(readsocks, writesocks, [])
    for sockobj in readables:
        if sockobj in mainsocks:
            # socket of port: accept connection fron new client
            newsock, address = sockobj.accept()  # mustn't block
            print("Connect: ", address, id(newsock))
            readsocks.append(newsock)
        else:
            # client socket: read the next line
            data = sockobj.recv(1024)  # recv mustn't block
            print('\tgot ', data, ' on ', id(sockobj))
            if not data:
                sockobj.close()
                readsocks.remove(sockobj)
            else:
                # can block: really todo make it use select too
                reply = 'Echo =>%s at %s' % (data, now())
                sockobj.send(reply.encode())







