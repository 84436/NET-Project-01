# A dirty script for testing the server
# 1 client = 1 process
# Each client will send a request to server every 50ms - 1s (random interval)

import sys
import socket
import multiprocessing
import random
import time
from utils import *

PROCESS_COUNT_LIMIT = 20
SLEEP_INTERVAL_BASE = 50
PROVINCES = [
    'HaNoi', 'QuangNinh', 'BacNinh', 'HaiPhong', 'NamDinh', 'ThaiBinh',
    'Hue', 'PhuYen', 'DakLak', 'QuangNam', 'KhanhHoa', 'DaNang', 'BinhDinh', 'QuangBinh', 'QuangTri', 'NinhThuan', 'GiaLai', 'QuangNgai', 'DakNong', 'KonTum',
    'DongThap', 'TPHCM', 'CaMau', 'VungTau', 'BenTre', 'BacLieu', 'DongNai', 'SocTrang', 'CanTho', 'AnGiang', 'TayNinh', 'BinhThuan', 'VinhLong', 'BinhDuong',
    'TraVinh', 'LongAn', 'BinhPhuoc',  'HauGiang', 'KienGiang', 'TienGiang', 'DaLat'
]

def cprint(sr, msg):
    c_ident = '[{:<5} | {}] '.format(os.getpid(), sr)
    print(c_ident + msg)

def random_ticket():
    return ''.join(x for x in [str(random.randint(0,9)) for i in range(6)])

def client(is_dead=False):
    c_actions_default = ['h', 'help', 'p', 'provinces']
    c_actions = ["random.choice(c_actions_default)", "random.choice(PROVINCES)", "'{} {}'.format(random.choice(PROVINCES), random_ticket())"]
    c_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    sr = ''
    try:
        c_sock.connect((HOST, PORT))
        c_sock.settimeout(5)
        sr = c_sock.recv(MSG_LIMIT).decode()
        if not sr:
            raise Exception(msg='server did not response')
        cprint(sr, '')

        while True:
            # Send
            request = eval(random.choice(c_actions))
            cprint(sr, '> {}'.format(request))
            c_sock.sendall(request.encode())

            # Receive
            response = c_sock.recv(MSG_LIMIT).decode()
            # cprint(sr, response)

            # Sleep
            sleep_interval = SLEEP_INTERVAL_BASE * random.randint(1,20)
            cprint(sr, 'sleep for {:d}ms'.format(sleep_interval))
            time.sleep(sleep_interval / 1000)

    except Exception as msg:
        cprint(sr, 'exception: {}'.format(msg))
    finally:
        c_sock.close()
    cprint(sr, 'dead')

################################################################################

if __name__ == "__main__":
    PROCESSES = []

    try:
        if len(sys.argv) != 2:
            print('This script accepts exactly 1 argument: number of clients to spawn.')
            raise ValueError
        process_count = int(sys.argv[1])
        if (process_count <= 0) or (process_count > PROCESS_COUNT_LIMIT):
            print('Number of processes is limited to max. of {}.'.format(PROCESS_COUNT_LIMIT))
            print('Modify this script to bypass that limit.')
            raise ValueError
        print('Number of processes = {}'.format(process_count))
        for i in range(process_count):
            p = multiprocessing.Process(target=client)
            p.start()
            PROCESSES.append(p)
        while True:
            pass
    
    except ValueError:
        pass
    except (KeyboardInterrupt, SystemExit):
        print('Ctrl-C received, backing off...')
    except Exception as msg:
        print('Exception: {}'.format(msg))
    
    finally:
        for each in PROCESSES:
            if (each.is_alive()): each.terminate()
