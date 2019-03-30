
try:
    from .tests.unittests import *
except ModuleNotFoundError:
    from tests.unittests import *
try:
    from .utils import *
except ModuleNotFoundError:
    from utils import *

import os
import threading


if __name__ == "__main__":
    server = Server('localhost', 8089)
    print("1", threading.enumerate())
    server_thread = threading.Thread(target=server.server_run)
    server_thread.start()
    print("2", threading.enumerate())
    while True:
        with server.server_connections_lock:
            for conn in server.server_connections:
                print("conn ", conn)
                if not conn.working:
                    conn.join()
                    print("Finished monothread receiving ", conn)
                    server.server_connections.remove(conn)
                    exit(0)
        with server.server_connections_lock:
            if server.server_connections:
                receiver = server.server_connections[0]
                print("server_connections connections")
                unpacker = NetworkDecoder("unpacker", receiver)
                unpacker.start()
                run_video(unpacker)

