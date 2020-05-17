# Query handler (aka the server)

import socket           # Standard TCP socket
import multiprocessing  # Alternative client handling method
                        # ('threading' was okay, but it doesn't have an obvious way to terminate)
import os               # DB file
import json             # DB file
import collections      # OrderedDict for a specific DB view

from utils import *
from crawler import *

################################################################################
# DATABASES
################################################################################

# [Early run] Open database
if lockfile():
    log.error('DB: lockfile exists')
    log.info('Check for other (instances of) crawlers that are modifying DB.')
    log.info('If everything\'s clear, you can manually remove db.lock.')
    exit(-1)
try:
    f = open(DB_FILE, 'r')
    DB_LAST_UPDATED = datetime.datetime.fromtimestamp(float(f.readline()))
    DB = json.loads(f.readline())
except (ValueError, json.JSONDecodeError):
    log.error('DB: invalid file format')
    log.info('DB: Check timestamp and/or its following serialized JSON object.')
    exit(-1)
except FileNotFoundError:
    log.critical('DB: file does not exist')
    log.info('DB: If this is the first time you\'re using this server, run crawler first.')
    exit(-1)

# DB view: provinces, accent_stripped (for searching)
PList_Search = {strip_accent(x).lower(): x for x in DB.keys()}

# DB view: all provinces, grouped by date; date sorted by most recent timestamps
# max_count = Optional filter (only show x most recent days)
def Province_PrintAll(max_count=None):
    # Group provinces by date, then sort the dates in descending order
    d = {}
    for province, details in DB.items():
        timestamp_int = int(details[0])
        if timestamp_int not in d:
            d[timestamp_int] = []
        d[timestamp_int].append(province)
    d = collections.OrderedDict(sorted(d.items(), reverse=True))

    # Export to human-readable string
    r = ''
    for timestamp, provinces in d.items():
        date = datetime.datetime.fromtimestamp(timestamp)
        r += '{wd:<8} {d:02d}/{m:02d}: {plist}\n'.format(wd=map_weekday(date, 'str'), d=date.day, m=date.month, plist=', '.join(provinces))
        if (max_count is not None):
            if (max_count == 1):
                break
            else:
                max_count -= 1
    return r

# DB view: result of one province
def Province_PrintResult(province):
    r = ''
    date = datetime.datetime.fromtimestamp(DB[province][0])
    result_d = DB[province][1]

    r += '{pname}, {weekday}, {d:02d}/{m:02d}\n'.format(pname=province, weekday=map_weekday(date, 'str'), d=date.day, m=date.month)
    for tier, nums in result_d.items():
        if len(nums) == 0:
            continue
        elif tier == '0':
            r += 'Giải ĐB : {}\n'.format(', '.join(nums))
        else:
            r += 'Giải {:>2} : {}\n'.format(tier, ', '.join(nums))
    return r

################################################################################
# PRIZES
################################################################################

# https://www.minhngoc.net.vn/thong-tin/co-cau-giai-thuong-mien-bac.html
# https://www.minhngoc.net.vn/thong-tin/co-cau-giai-thuong-mien-trung.html
# https://www.minhngoc.net.vn/thong-tin/co-cau-giai-thuong-mien-nam.html
# Northern has the extra "special code" for each ticket, but this is not covered/explicitly required in the assignment description.
# Central and Southern actually has the same table .-.
_PRIZE_TABLE = {
    'Bắc':      {0:1000000000, 1:10000000, 2:5000000,  3:1000000,  4:400000,  5:200000,  6:100000, 7:40000},
    'Trung':    {0:2000000000, 1:30000000, 2:15000000, 3:10000000, 4:3000000, 5:1000000, 6:400000, 7:200000, 8:100000},
    'Nam':      {0:2000000000, 1:30000000, 2:15000000, 3:10000000, 4:3000000, 5:1000000, 6:400000, 7:200000, 8:100000}
}

def Prize_Check(province, ticket):
    try:
        result_d = DB[province][1]
        if not ticket.isdigit(): raise
    except:
        return None
    
    prizes = []
    is_northern = (PAGES[province]['region'] == 'Bắc')
    applied_prize_table = _PRIZE_TABLE[PAGES[province]['region']]
    for tier in range(7+1 if is_northern else 8+1):
        for each in result_d[str(tier)]:
            if ticket[6-len(each):] == each:
                prizes.append((tier, applied_prize_table[tier]))
    return prizes

def Prize_Print(province, ticket):
    r = ''
    date = datetime.datetime.fromtimestamp(DB[province][0])
    prizes = Prize_Check(province, ticket)
    r += '{pname}, {weekday}, {d:02d}/{m:02d}\n'.format(pname=province, weekday=map_weekday(date, 'str'), d=date.day, m=date.month)
    if not prizes:
        r += 'Chúc bạn may mắn lần sau :<\n'
    else:
        value_total = 0
        r += 'Bạn đã trúng (các) giải:\n'
        for tier, value in prizes:
            value_total += value
            r += 'Giải {t} - {v}đ\n'.format(t=tier if tier != 0 else 'ĐẶC BIỆT', v=value)
        r += 'Tổng giá trị các giải = {}đ\n'.format(value_total)
        r += '(Trúng số rồi kìa :>)\n'
    return r

################################################################################
# CLIENTS
################################################################################

# Static help text. Meant to be used by the client handler.
_HELP_TEXT = """\b\b
TiloTilos (Tiny Lottery Ticket Lookup Server) : Máy chủ tra cứu xổ số cơ bản.
Nguồn dữ liệu: XS Đại Phát (kết quả), XS Minh Ngọc (cơ cấu giải)

Các lệnh hiện có:
    h (help)        :   Thứ bạn đang đọc
    p (provinces)   :   Liệt kê danh sách tỉnh hợp lệ
    <Tỉnh>          :   Tra kết quả XS mới nhất của một tỉnh
    <Tỉnh> <Vé>     :   Tra theo tỉnh và tự động dò kết quả trúng thưởng của vé
Ghi chú:
    - Tên tỉnh phải được viết không dấu và không cách (không phân biệt hoa thường).
    - Vé số phải có định dạng là chính xác 6 chữ số.
"""
_HELP_PLIST_SAMPLE = """
Các tỉnh có KQXS trong 2 ngày gần đây nhất:
(Xem trợ giúp để biết cách liệt kê tất cả các tỉnh.)
"""
_HELP_PLIST_ALL = 'Danh sách các tỉnh, xếp theo ngày gần đây nhất trước:\n'
_HELP_POST_ERROR = 'Xem trợ giúp để biết thêm thông tin.\n'

# Client handler
def client_handler(c_sock, c_ap):
    instance_pid = os.getpid()
    c_addr = c_ap[0]
    c_port = c_ap[1]
    log.info('[{pid:<5} / {host}:{port} +] New client'.format(pid=instance_pid, host=c_addr, port=c_port))

    # Initial response: client's own host:port
    c_sock.sendall('Client = {host}:{port}'.format(host=c_addr, port=c_port).encode())

    # Receive/send msg
    command = ''
    try:
        while True:
            # Listen for (and tokenize) commands
            command = c_sock.recv(MSG_LIMIT).decode()
            command_t = [x for x in list(dict.fromkeys(command.split(' '))) if x != '']

            # Print to log
            if command:
                log.info('[{pid:<5} / {host}:{port} >] {cmd}'.format(pid=instance_pid, host=c_addr, port=c_port, cmd=command))

            # Send help
            if (command == 'h') or (command == 'help'):
                msg = _HELP_TEXT + _HELP_PLIST_SAMPLE + Province_PrintAll(2)
                c_sock.sendall(msg.encode())
                continue
            
            # List all provinces
            if (command == 'p') or (command == 'provinces'):
                msg = _HELP_PLIST_ALL + Province_PrintAll()
                c_sock.sendall(msg.encode())
                continue

            # Block commands with excess args
            if len(command_t) > 2:
                c_sock.sendall('Lệnh không hợp lệ.\n{}'.format(_HELP_POST_ERROR).encode())
                continue
            else:
                p, t = strip_accent(command_t[0]).lower(), (command_t[1] if len(command_t) == 2 else '')

            # Look up
            if p not in PList_Search:
                c_sock.sendall('Tỉnh không hợp lệ.\n{}'.format(_HELP_POST_ERROR).encode())
                continue
            elif not t:
                c_sock.sendall(Province_PrintResult(PList_Search[p]).encode())
                continue

            # Look up with ticket
            if len(t) == 6:
                c_sock.sendall(Prize_Print(PList_Search[p], t).encode())
                continue
            else:
                c_sock.sendall('Vé số không hợp lệ.\n{}'.format(_HELP_POST_ERROR).encode())
                continue
    
    # The client has broke the connection (either accidentally or on purpose)
    except (ConnectionAbortedError, ConnectionResetError, ConnectionRefusedError):
        pass

    # Sssh.
    except:
        pass

    finally:
        c_sock.close()
        log.info('[{pid:<5} / {host}:{port} -] Client disconnected'.format(pid=instance_pid, host=c_addr, port=c_port))

################################################################################
# main
################################################################################        

if __name__ == "__main__":
    print('TiloTilos (Tiny Lottery Ticket Lookup Server)\nCtrl-C to stop.\n')

    log.info('Server started.')
    var_root_check()

    # Warn if database is older than 1 day
    log.info('DB: last updated = {}'.format(DB_LAST_UPDATED))
    if (today - DB_LAST_UPDATED).days >= 1:
        log.warning('DB: oudated data')
        log.info('DB: Please manually run crawler.')

    # Create the socket
    server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    # Reuse address if possible
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket
    server.bind((HOST, PORT))

    # Show current server PID and bounded addr (just in case)
    log.info('Server is ready: PID = {pid}, Bounded addr = {host}:{port}'.format(pid=os.getpid(), host=HOST, port=PORT))

    # Waiting for clients
    log.info('Listening for connections')
    _PROCESSES = []

    try:
        while True:
            server.listen(0)
            server.settimeout(1)
            
            # socket.accept() is blocking.
            # The server will have about 1s window to accept client, after which
            # it will stop and return to main to catch the pending KeyboardInterrupt if it exists
            try:
                c_sock, c_ap = server.accept()
            except:
                continue

            p = multiprocessing.Process(target=client_handler,
                                        args=(c_sock, c_ap))
            p.start()
            _PROCESSES.append(p)

            # Process list "housekeeping":
            # Remove any dead process entries
            for each in _PROCESSES:
                if not each.is_alive(): _PROCESSES.remove(each)
    
    except (KeyboardInterrupt, SystemExit):
        log.info('Ctrl-C received. Shutting down...')
        for each in _PROCESSES:
            if (each.is_alive()): each.terminate()
    
    finally:
        server.close()
    
    log.info('Server stopped.')
