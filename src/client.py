# Interactive client

import socket
import os           # Cross-platform "clear screen" because why not
import subprocess   # ^             

# Custom
from utils import *

# Clear screen
def clrscr():
    _ = subprocess.call('clear' if os.name == 'posix' else 'cls', shell=True)

################################################################################

SERVER_1STR = None

if __name__ == "__main__":
    try:
        # Connect to server
        print('Đang kết nối tới {host}:{port}...'.format(host=HOST, port=PORT))
        client = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        client.connect((HOST, PORT))

        # Get self IP and address
        print('Chờ phản hồi đầu từ server...')
        client.settimeout(5)
        try:
            SERVER_1STR = client.recv(MSG_LIMIT).decode()
        except socket.timeout:
            raise ConnectionError
        if not SERVER_1STR:
            raise ConnectionError
        print(SERVER_1STR)
        client.settimeout(None)
        
        print('Đã kết nối. "cls" để clear screen, "h" (hoặc "help") để bắt đầu, Ctrl-C để kết thúc phiên.')
        print()

        # Start sending/receiving msgs
        while True:
            command = input('> ').strip()
            # Pass empty commands
            if command == '':
                print()
                continue
            if command == 'cls':
                clrscr()
                continue
            client.sendall(command.encode())
            result = client.recv(MSG_LIMIT)
            print(result.decode())

    except (ConnectionResetError, ConnectionRefusedError, ConnectionError):
        print('Không thể kết nối tới server.')

    except KeyboardInterrupt:
        print('Ctrl-C')

    except:
        print('[!] Có gì đó sai sai.')

    finally:
        client.close()
        print('Kết thúc phiên.')
