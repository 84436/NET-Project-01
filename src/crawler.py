# BS4-powered crawler

# Externals
from requests import *                      # Better alternative to urllib.request
from bs4 import BeautifulSoup, element      # The Heart Of Crawler.py
                                            # 'element' for using 'element.NavigableString'

import json                                 # Serializing data
import re                                   # RegEx; used for parsing date
from datetime import datetime as dt         # Datetime parsing; also for parsing date

from utils import *

################################################################################
# SITE-SPECIFIC STUFF
################################################################################

# Current target
SITE_ROOT = 'https://xosodaiphat.com'

# Static subpages list
PAGES = {
    'Hà Nội':       {'region': 'Bắc',       'weekday': [2,5],   'site': '/xstd-xo-so-ha-noi.html'},
    'Quảng Ninh':   {'region': 'Bắc',       'weekday': [3],     'site': '/xsqn-xo-so-quang-ninh.html'},
    'Bắc Ninh':     {'region': 'Bắc',       'weekday': [4],     'site': '/xsbn-xo-so-bac-ninh.html'},
    'Hải Phòng':    {'region': 'Bắc',       'weekday': [6],     'site': '/xshp-xo-so-hai-phong.html'},
    'Nam Định':     {'region': 'Bắc',       'weekday': [7],     'site': '/xsnd-xo-so-nam-dinh.html'},
    'Thái Bình':    {'region': 'Bắc',       'weekday': [1],     'site': '/xstb-xo-so-thai-binh.html'},
    'Huế':          {'region': 'Trung',     'weekday': [2],     'site': '/xstth-xo-so-hue.html'},
    'Phú Yên':      {'region': 'Trung',     'weekday': [2],     'site': '/xspy-xo-so-phu-yen.html'},
    'Đắk Lắk':      {'region': 'Trung',     'weekday': [3],     'site': '/xsdlk-xo-so-dak-lak.html'},
    'Quảng Nam':    {'region': 'Trung',     'weekday': [3],     'site': '/xsqna-xo-so-quang-nam.html'},
    'Khánh Hòa':    {'region': 'Trung',     'weekday': [4,1],   'site': '/xskh-xo-so-khanh-hoa.html'},
    'Đà Nẵng':      {'region': 'Trung',     'weekday': [4,7],   'site': '/xsdna-xo-so-da-nang.html'},
    'Bình Định':    {'region': 'Trung',     'weekday': [5],     'site': '/xsbdi-xo-so-binh-dinh.html'},
    'Quảng Bình':   {'region': 'Trung',     'weekday': [5],     'site': '/xsqb-xo-so-quang-binh.html'},
    'Quảng Trị':    {'region': 'Trung',     'weekday': [5],     'site': '/xsqt-xo-so-quang-tri.html'},
    'Ninh Thuận':   {'region': 'Trung',     'weekday': [6],     'site': '/xsnt-xo-so-ninh-thuan.html'},
    'Gia Lai':      {'region': 'Trung',     'weekday': [6],     'site': '/xsgl-xo-so-gia-lai.html'},
    'Quảng Ngãi':   {'region': 'Trung',     'weekday': [7],     'site': '/xsqng-xo-so-quang-ngai.html'},
    'Đắk Nông':     {'region': 'Trung',     'weekday': [7],     'site': '/xsdno-xo-so-dak-nong.html'},
    'Kon Tum':      {'region': 'Trung',     'weekday': [1],     'site': '/xskt-xo-so-kon-tum.html'},
    'Đồng Tháp':    {'region': 'Nam',       'weekday': [2],     'site': '/xsdt-xo-so-dong-thap.html'},
    'TPHCM':        {'region': 'Nam',       'weekday': [2,7],   'site': '/xshcm-xo-so-tphcm.html'},
    'Cà Mau':       {'region': 'Nam',       'weekday': [2],     'site': '/xscm-xo-so-ca-mau.html'},
    'Vũng Tàu':     {'region': 'Nam',       'weekday': [3],     'site': '/xsvt-xo-so-vung-tau.html'},
    'Bến Tre':      {'region': 'Nam',       'weekday': [3],     'site': '/xsbtr-xo-so-ben-tre.html'},
    'Bạc Liêu':     {'region': 'Nam',       'weekday': [3],     'site': '/xsbl-xo-so-bac-lieu.html'},
    'Đồng Nai':     {'region': 'Nam',       'weekday': [4],     'site': '/xsdn-xo-so-dong-nai.html'},
    'Sóc Trăng':    {'region': 'Nam',       'weekday': [4],     'site': '/xsst-xo-so-soc-trang.html'},
    'Cần Thơ':      {'region': 'Nam',       'weekday': [4],     'site': '/xsct-xo-so-can-tho.html'},
    'An Giang':     {'region': 'Nam',       'weekday': [5],     'site': '/xsag-xo-so-an-giang.html'},
    'Tây Ninh':     {'region': 'Nam',       'weekday': [5],     'site': '/xstn-xo-so-tay-ninh.html'},
    'Bình Thuận':   {'region': 'Nam',       'weekday': [5],     'site': '/xsbth-xo-so-binh-thuan.html'},
    'Vĩnh Long':    {'region': 'Nam',       'weekday': [6],     'site': '/xsvl-xo-so-vinh-long.html'},
    'Bình Dương':   {'region': 'Nam',       'weekday': [6],     'site': '/xsbd-xo-so-binh-duong.html'},
    'Trà Vinh':     {'region': 'Nam',       'weekday': [6],     'site': '/xstv-xo-so-tra-vinh.html'},
    'Long An':      {'region': 'Nam',       'weekday': [7],     'site': '/xsla-xo-so-long-an.html'},
    'Bình Phước':   {'region': 'Nam',       'weekday': [7],     'site': '/xsbp-xo-so-binh-phuoc.html'},
    'Hậu Giang':    {'region': 'Nam',       'weekday': [7],     'site': '/xshg-xo-so-hau-giang.html'},
    'Kiên Giang':   {'region': 'Nam',       'weekday': [1],     'site': '/xskg-xo-so-kien-giang.html'},
    'Tiền Giang':   {'region': 'Nam',       'weekday': [1],     'site': '/xstg-xo-so-tien-giang.html'},
    'Đà Lạt':       {'region': 'Nam',       'weekday': [1],     'site': '/xsdl-xo-so-da-lat.html'},
}

# Database (in-memory)
DB = {}

################################################################################
# PARSER LOGIC
################################################################################

# Site parser
def province_parse_site(province):
    # You can't trust yourself
    try:
        is_northern = (PAGES[province]['region'] == 'Bắc')
    except KeyError:
        return None

    # Get the site and soup-ify it
    subpage = get(SITE_ROOT + PAGES[province]['site'])
    subpage_soup = BeautifulSoup(subpage.content, 'html.parser')

    # Filter all relevant tags from the first found table (i.e. latest result)
    table_xsmb_latest = [
        td
        for td in
            subpage_soup.find('table', {'class' : 'table-xsmb'}).contents[1].children
        if
            not isinstance(td, element.NavigableString)
    ]

    # Get date of results
    # https://stackoverflow.com/a/3276190
    if (is_northern):
        # Northern: the date string is one level outside the table, so it needs to be fetched separately.
        date_text = subpage_soup.find('h2', {'class': 'class-title-list-link'}).findAll('a', {'class': 'u-line'})[2].text
        date_text_match = re.search(r'\d{2}/\d{2}/\d{4}', date_text)
        date = dt.strptime(date_text_match.group(), '%d/%m/%Y').timestamp()
    else:
        # Cell 0 contains the date
        date_text = table_xsmb_latest[0].findAll('a', {'class': 'special-code'})[1].text
        date_text_match = re.search(r'\d{2}/\d{2}/\d{4}', date_text)
        date = dt.strptime(date_text_match.group(), '%d/%m/%Y').timestamp()    

    # All the cells (except the first one) contain the results
    results = {0:[], 1:[], 2:[], 3:[], 4:[], 5:[], 6:[], 7:[], 8:[]}
    if (is_northern):
        # Northern: the order is reversed from that of Southern/Central
        tier = 0
        for each_tier in table_xsmb_latest[1:]:
            for each_num in each_tier.findAll('span'):
                results[tier].append(each_num.text)
            tier += 1
    else:
        # Southern/Central
        tier = 8
        for each_tier in table_xsmb_latest[1:]:
            for each_num in each_tier.findAll('span'):
                results[tier].append(each_num.text)
            tier -= 1
    
    # Deliver the results
    return(date, results)

################################################################################
# main
################################################################################

if __name__ == "__main__":
    log.info('Crawler started.')
    var_root_check()

    # Lockfile check
    if lockfile():
            log.error('Lock exists')
            log.info('Check for other (instances of) crawlers that are modifying DB.')
            log.info('If everything\'s clear, you can manually remove db.lock.')
            exit(-1)
    
    try:
        if lockfile('lock'):
            log.info('Lock set')
        else:
            log.error('Failed to set lock')
            raise

        # Test the site for availability
        site = get(SITE_ROOT)
        if (site.status_code != 200):
            log.error('Site status code is {}'.format(site.status_code))
            raise
        else:
            log.info('Site available')

        # Batch parse
        provinces_to_parse = [p for p in PAGES]
        for i, e in enumerate(provinces_to_parse):
            log.info('Parsing {x}/{xtotal} : {name}'.format(x=i+1, xtotal=len(provinces_to_parse), name=strip_accent(e)))
            DB[e] = province_parse_site(e)

        # Save to file
        db_fd = open(DB_FILE, 'w')
        db_fd.write('{}\n'.format(today.timestamp()))
        db_fd.write(json.dumps(DB))
        log.info('File written')
    
    except:
        log.error('Something wrong happened. Lock will be removed. DEBUGME')
        pass

    finally:
        # Lockfile release
        lockfile('unlock')
        log.info('Lock removed')
    
    log.info('Crawler stopped.')
