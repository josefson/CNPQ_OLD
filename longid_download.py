# -*- coding: utf-8 -*-
"""
This file is responsible to download the curriculum xml
"""
import re
import sys
import logging
import requests
import argparse
from PIL import Image
from captcha import Captcha
from bs4 import BeautifulSoup
from driver import LattesDriver
from selenium.webdriver.common.by import By
from multiprocessing import Process, current_process
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException


LOG_FILENAME = 'log.txt'

FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(format=FORMAT, filename=LOG_FILENAME, level=logging.INFO)

def short_ids(short_id_file):
    """This function expects a short_id file and returns a list with all
    short_ids."""
    short_id_list = []
    invalid_ids = []
    with open(short_id_file) as data_file:
        for line in data_file:
            short_id = line.strip('\n')
            if len(short_id) == 10:
                short_id_list.append(line.strip('\n'))
            else:
                invalid_ids.append(short_id)
    print 'Total of IDs in the file: {}.'.format(
        len(short_id_list) + len(invalid_ids))
    print 'InvalidIDs: {}'.format(len(invalid_ids))
    print 'Valid IDs to downlaod: {}'.format(len(short_id_list))
    data_file.close()
    short_id_list = short_id_list
    return short_id_list

def split_list(alist, wanted_parts):
    """Split a list of intervals in n parts in order to be
    multiprocessed."""
    length = len(alist)
    return [alist[i*length // wanted_parts: (i+1)*length // wanted_parts]
            for i in range(wanted_parts)]

def get_short_url(short_id):
    """Returns a short_url for a given short_id."""
    base_url = 'http://buscatextual.cnpq.br/buscatextual/'\
               'visualizacv.do?id='
    return base_url + str(short_id)

def print_request(request):
    """Print a request state for debugging purposes."""
    for header in request.request.headers:
        print '      {} : {}'.format(header, request.request.headers[header])
    for cookie in request.cookies:
        print cookie

def save(request, file_name, mode):
    """Save a request.content into a file for debugging purposes."""
    temp_file = open(file_name, mode)
    temp_file.write(request.content)
    temp_file.close()

def verify_page(page_req):
    """Given a page request returns a match of which page it belongs to."""
    input_box_id = 'informado'
    cv_page_req_href = 'download'
    not_found = "<html><head><title>Curr\xedculo n\xe3o encontrado!</title>"\
                "</head><body><div style='font-family:Arial;font-size=10pt;"\
                "align:center;color:red;font-weight:bold'>Curr\xedculo n\xe3"\
                "o encontrado</div></body></html>"
    content = page_req.content
    soup = BeautifulSoup(content, 'lxml')
    if soup.find(id=input_box_id):
        return 'CAPTCHA'
    elif soup.find(href=re.compile(cv_page_req_href)):
        return 'CVPAGE'
    else:
        if content == not_found:
            return 'NOTFOUND'

def scrap_long_id(cv_page_req):
    """Given a request from the CVPAGE it scraps and returns a long_id."""
    source = cv_page_req.content
    soup = BeautifulSoup(source, 'lxml')
    link = soup.find(href=re.compile(r'(\d{16})'))
    long_id = re.search(r'(\d{16})', str(link)).group(1)
    return long_id

def crack_captcha(driver):
    """Given a driver inside a captcha page, cracks the captcha and returns
    its value."""
    captcha_locator = 'div_image_captcha'
    element = driver.find_element(By.ID, captcha_locator)
    location = element.location
    size = element.size
    page_ss = 'pageScreenShot_' + current_process().name + '.png'
    captcha_ss = 'captcha_' + current_process().name + '.png'
    driver.get_screenshot_as_file(page_ss)
    image = Image.open(page_ss)
    left = location['x'] + 2
    top = location['y']
    right = location['x'] + size['width']
    bottom = location['y'] + size['height'] - 1
    image = image.crop((left, top, right, bottom))
    image.save(captcha_ss)
    return Captcha(captcha_ss).get_text().upper()

def captcha_page(short_id):
    """Given a short_id, this function returns a request result of the
    captcha_page."""
    short_url = 'http://buscatextual.cnpq.br/buscatextual/download.do?'
    params = {'id' : short_id}
    cap_page_req = requests.get(short_url, params=params)
    return cap_page_req

def captcha_image(short_url):
    """Given a Referer=short_id_url this function returns the resulting request
    of the captcha image, which contains the captcha to be solved and its
    session attributes to be persisted through the requests."""
    captcha_url = 'http://buscatextual.cnpq.br/buscatextual/servlet/captcha?'
    headers = {}
    headers['Referer'] = short_url
    headers['fontSize'] = '10'
    headers['imp'] = 'cnpqrestritos'
    headers['idioma'] = 'PT'
    params = {'metodo' : 'getImagemCaptcha'}
    cap_img_req = requests.get(captcha_url, params=params, headers=headers)
    return cap_img_req

def inform_captcha(cap_img_req, captcha_code):
    """Given a previous session request and a referer."""
    inform_url = 'http://buscatextual.cnpq.br/buscatextual/servlet/captcha?'
    headers = cap_img_req.request.headers
    headers['X-Requested-With'] = 'XMLHttpRequest'
    headers['Referer'] = cap_img_req.request.headers['Referer']
    cookies = cap_img_req.cookies
    params = {'informado' : captcha_code, 'metodo' : 'validaCaptcha'}
    informed_cap_req = requests.get(inform_url, cookies=cookies,
                                    params=params, headers=headers)
    return informed_cap_req

def post_do(inf_cap_req):
    """Given a previous session request this function performs some kind of an
    obscure post validation which allow us to only then visualize the
    curriculum in the next request."""
    post_url = 'http://buscatextual.cnpq.br/buscatextual/visualizacv.do'
    short_id = inf_cap_req.request.headers['Referer'][-10:]
    headers = {}
    headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;'\
                        'q=0.9,*/*;q=0.8'
    headers['Accept-Encoding'] = 'gzip, deflate'
    headers['Accept-Language'] = 'en-US,en;q=0.5'
    headers['Connection'] = 'keep-alive'
    headers['Cookie'] = inf_cap_req.request.headers['Cookie']
    headers['DNT'] = '1'
    headers['Host'] = 'buscatextual.cnpq.br'
    headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; '\
                            'rv:35.0) Gecko/20100101 Firefox/35.0'
    # headers['Referer'] = referer
    headers['Referer'] = inf_cap_req.request.headers['Referer']
    headers['Content-Length'] = '999'
    headers['Cookie'] = inf_cap_req.request.headers['Cookie']
    # cookies = inf_cap_req.cookies   # Necessary.
    files = {'metodo' : (None, 'visualizarCV'), 'id' : (None, short_id),
             'idiomaExibicao' : (None, ''), 'tipo' : (None, ''),
             'informado' : (None, '')}
    requests.post(post_url, headers=headers, files=files)

def cv_view(inf_cap_req):
    """Given a previous session request it gets and returns the cv page."""
    referer = inf_cap_req.request.headers['Referer']
    view_url = referer
    headers = {}
    headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q='\
                        '0.9,*/*;q=0.8'
    headers['Accept-Encoding'] = 'gzip, deflate'
    headers['Accept-Language'] = 'en-US,en;q=0.5'
    headers['Connection'] = 'keep-alive'
    headers['Cookie'] = inf_cap_req.request.headers['Cookie']
    headers['Host'] = 'buscatextual.cnpq.br'
    headers['Referer'] = inf_cap_req.request.headers['Referer']
    cv_request = requests.get(view_url, headers=headers)
    return cv_request

def download_cv(driver, long_id):
    """Given a selenium webdriver and a long_id, it downloads the related xml
    curriculum."""
    pname = current_process().name
    long_url = 'http://buscatextual.cnpq.br/buscatextual/download.do?metodo='\
               'apresentar&idcnpq=' + long_id
    input_locator = 'informado'
    captcha_locator = 'image_captcha'
    while True:
        logging.info('%s-download_cv: Loading %s', pname, long_url)
        driver.get(long_url)
        logging.info('%s-download_cv: Locating captcha element...', pname)
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.ID,
                                                             captcha_locator)))
        logging.info('%s-download_cv: Cracking captcha...', pname)
        code = crack_captcha(driver)
        if len(code) != 4:
            logging.info('%s-download_cv: Wrong captcha length: %s. Trying '\
                         'again...', pname, code)
            continue
        if len(code) == 4:
            logging.info('%s-download_cv: Right captcha: %s', pname, code)
            break
    logging.info('%s-download_cv: Entering captcha: %s', pname, code)
    element = driver.find_element(By.ID, input_locator)
    element.clear()
    element.send_keys(code + '\n')
    logging.info('%s-download_cv: Waiting for download...', pname)
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.invisibility_of_element_located((By.ID,
                                                             captcha_locator)))

def worker(short_id_list, long_id_file):
    """Given a list of short_ids it iterates over them to get the long_id."""
    pname = current_process().name
    logging.info('%s: Started', pname)
    try:
        lattesdriver = LattesDriver()
        display = lattesdriver.get_display()
        driver = lattesdriver.get_driver()
    except WebDriverException, error:
        print error
        sys.exit('Failed to initialize selenium drivers. Calm down, '\
                'sometimes this happens, please try again. If this error '\
                'persists check if the Browser version is compatible with '\
                'selenium.')
    output_file = open(long_id_file, 'a')
    for count, short_id in enumerate(short_id_list):
        while True:
            while True:
                try:
                    logging.info('%s- Getting captcha and session for CVPAGE',
                                 pname)
                    img_req = captcha_image(get_short_url(short_id))
                    break
                except requests.exceptions.Timeout as terror:
                    logging.info('%s-[Loop-%s]=> Timeout: %s\nTrying again...',
                                 pname, count+1, terror)
                    continue
                except requests.exceptions.ConnectionError as cerror:
                    logging.info('%s-[Loop-%s]=> Connection Error: %s\nTrying '
                                 'again...', pname, count+1, cerror)
                    continue
                except requests.exceptions.RequestException as rerror:
                    logging.info('%s-[Loop-%s]=> Request Error: %s\nTrying '
                                 'again...', pname, count+1, rerror)
                    continue
            image_name = 'temp_' + pname + '.png'
            open(image_name, 'wb').write(img_req.content)
            code = Captcha(image_name).get_text().upper()
            if len(code) != 4:
                logging.info('%s- Wrong code length: %s', pname, code)
                continue
            elif len(code) == 4:
                logging.info('%s- Right code length: %s', pname, code)
                try:
                    inf_req = inform_captcha(img_req, code)
                    post_do(inf_req)
                    cv_req = cv_view(inf_req)
                except requests.exceptions.Timeout as terror:
                    logging.info('%s-[Loop-%s]=> Timeout: %s\nTrying again...',
                                 pname, count+1, terror)
                    continue
                except requests.exceptions.ConnectionError as cerror:
                    logging.info('%s-[Loop-%s]=> Connection Error: %s\nTrying '
                                 'again...', pname, count+1, cerror)
                    continue
                except requests.exceptions.RequestException as rerror:
                    logging.info('%s-[Loop-%s]=> Request Error: %s\nTrying '
                                 'again...', pname, count+1, rerror)
                    continue
                if verify_page(cv_req) == 'CVPAGE':
                    logging.info('%s- Inside CVPAGE, scraping long_id', pname)
                    long_id = scrap_long_id(cv_req)
                    logging.info('%s-[%s/%s]=> short_id: %s | long_id: %s',
                                 pname, count+1, len(short_id_list), short_id,
                                 long_id)
                    output_file.write(short_id + ' | ' + long_id + '\n')
                    output_file.flush()
                    print '{}-[{}/{}]=> short_id: {} | long_id: {}'.format(
                        pname, count+1, len(short_id_list), short_id, long_id)
                    while True:
                        try:
                            logging.info('%s- Downloading the CV for long_id:'\
                                         ' %s', pname, long_id)
                            download_cv(driver, long_id)
                            logging.info('%s- Download finished!', pname)
                            break
                        except Exception, derror:
                            print derror
                            logging.info('%s- Download failed. Trying again',
                                         pname)
                            continue
                    break
                elif verify_page(cv_req) == 'NOTFOUND':
                    logging.info('%s-[%s/%s]=> short_id: %s | long_id: '\
                                 'NOTFOUND', pname, count+1,
                                 len(short_id_list), short_id)
                    output_file.write(short_id + ' | NOTFOUND\n')
                    output_file.flush()
                    print '{}-[{}/{}]=> short_id: {} | NOTFOUND'.format(
                        pname, count+1, len(short_id_list), short_id)
                    break
    driver.close()
    display.stop()

def main(workers, i_file, o_file):
    """Main function, which controls the workflow of the program."""
    short_id_file = i_file
    long_id_file = o_file
    cores = workers
    short_id_list = short_ids(short_id_file)
    splited_lists = split_list(short_id_list, cores)
    for splited_list in range(len(splited_lists)):
        temp = (splited_lists[splited_list], long_id_file)
        process = Process(target=worker, args=temp)
        process.start()


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('-w', '--worker', dest='cores', required=True,
                        type=int, help='number of workers to split the task.')
    PARSER.add_argument('-i', '--input', dest='short_id_file', required=True,
                        type=str, help='ShortIds file as input.')
    PARSER.add_argument('-o', '--output', dest='long_id_file', required=True,
                        type=str, help='LongIDs output file.')
    ARGS = PARSER.parse_args()
    main(ARGS.cores, ARGS.short_id_file, ARGS.long_id_file)
