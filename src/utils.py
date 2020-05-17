# Utilities

import os           # var (Files)
import sys          # var (Files)
import datetime     # Date/Time
import unicodedata  # Strip accents from province name
import logging      # Logging

################################################################################
# Defaults for servers + clients
################################################################################

# Default HOST and PORT
HOST = 'localhost'
PORT = 8652 # XSLA

# Message length limit
MSG_LIMIT = 8192

################################################################################
# Shared consts and utils for server + crawlers
################################################################################

# File locations
VAR_ROOT    = '{}/../data'.format(sys.path[0])
DB_FILE     = VAR_ROOT + '/db'
DB_LOCKFILE = DB_FILE + '.lock'
LOG_FILE    = VAR_ROOT + '/log.txt'

# Automagically create VAR_ROOT if not exists
def var_root_check():
    if not os.path.exists(VAR_ROOT):
        os.makedirs(VAR_ROOT)

# Simple stupid lockfile mechanism.
def lockfile(action='test'):
    if action == 'test':
        return os.path.exists(DB_LOCKFILE)
    elif action == 'lock':
        try:
            if os.path.exists(DB_LOCKFILE): return False
            open(DB_LOCKFILE, 'w+').close()
            return True
        except IOError:
            return False
    elif action == 'unlock':
        try:
            os.remove(DB_LOCKFILE)
            return True
        except:
            return False
    else:
        return None

################################################################################

# Logging
# https://realpython.com/python-logging/ + Py3 docs

# Get the default logger (root)
log = logging.getLogger()
log.setLevel('INFO')

# Create and configure log handlers (i.e. where the logs are written to)
# Currently logs are written to both console (stdout) and file (log.txt in var root)
logh_format_str        = '[{levelname[0]} {filename:<10} {asctime}] : {msg}'
logh_format_str_notime = '[{levelname[0]} {filename:<10} ] : {msg}'
logh_console = logging.StreamHandler(sys.stdout) # Default is sys.stderr
logh_console.setFormatter(logging.Formatter(logh_format_str_notime, style='{'))
var_root_check()
logh_file = logging.FileHandler(LOG_FILE)
logh_file.setFormatter(logging.Formatter(logh_format_str, style='{'))

# Attach log handlers to the logger
log.addHandler(logh_console)
log.addHandler(logh_file)

################################################################################

# Current datetime
today = datetime.datetime.now()

# Get current weekday (2-1) (mapped from Python's weekday range: 0-6)
def map_weekday(o_datetime, type='int'):
    weekday_mapped_int = [2, 3, 4, 5, 6, 7, 1]
    weekday_mapped_str = ['hai', 'ba', 'tư', 'năm', 'sáu', 'bảy', 'Chủ nhật']
    if type == 'int':
        return weekday_mapped_int[o_datetime.weekday()]
    elif type == 'str':
        r = 'Thứ ' if (o_datetime.weekday() != 6) else ''
        r += weekday_mapped_str[o_datetime.weekday()]
        return r
    else:
        return None

################################################################################

# Strip accents and spaces off a Vietnamese string.
# References:
#   - The original SO answer:
#     https://stackoverflow.com/a/518232
#   - Py3 docs on unicodedata module:
#     https://docs.python.org/3/library/unicodedata.html
#   - Table 12 of Unicode Standard Annex 44: "Unicode Character Database":
#     https://www.unicode.org/reports/tr44/
#     'Mn' = 'Nonspacing_Mark'
#     'Lu'/'Ll' = 'Uppercase_Letter'/'Lowercase_Letter'
#
# The whole Vietnamese accented vowel set, with the exception of 'đ', is guaranteed to be decomposed
# into an Ll/Lu, followed by one or more Mn
# The following snippet should prove that:
#   list = [[category(c) for c in normalize('NFD', i)] for i in 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịúùủũụýỳỷỹỵđ']
#   flattened_list = [item for sublist in list for item in sublist]
#   set(flattened_list)
#
# Note to self: why not 'unidecode'?
def strip_accent(str):
    r = ''
    for c in unicodedata.normalize('NFD', str):
        # Đ/đ exception: the letter is a standalone Lu/Ll
        if (c == 'Đ'): r += 'D'
        elif (c == 'đ'): r += 'd'
        elif (c != ' ') and unicodedata.category(c) != 'Mn': r += c
        else: pass
    return r
