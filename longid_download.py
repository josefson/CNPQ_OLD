# -*- coding: utf-8 -*-
"""
This file is responsible to download the curriculum xml
"""
import re
import requests
from PIL import Image
from captcha import Captcha
from bs4 import BeautifulSoup
from driver import LattesDriver
from selenium.webdriver.common.by import By
from multiprocessing import Process, current_process
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


CORES = 2
SHORT_ID_FILE = 'short_ids.csv'   # Input file.
LONG_ID_FILE = 'long_ids.csv'   # Output file.

def short_ids(short_id_file):
    """This function expects a short_id file and returns a list with all
    short_ids."""
    short_id_list = []
    with open(short_id_file) as data_file:
        for line in data_file:
            short_id_list.append(line.strip('\n'))
    data_file.close()
    short_id_list = short_id_list
    return short_id_list

def split_list(alist, CORES):
    """Split a list of intervals in n parts in order to be
    multiprocessed."""
    wanted_parts = CORES
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
    not_found = '<title>Currículo não encontrado!</title>'
    content = page_req.content
    soup = BeautifulSoup(content, 'lxml')
    if soup.find(id=input_box_id):
        return 'CAPTCHA'
    elif soup.find(href=re.compile(cv_page_req_href)):
        return 'CVPAGE'
    else:
        title = soup.find('title').encode('utf-8')
        if title == not_found:
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
    # pname = current_process().name
    long_url = 'http://buscatextual.cnpq.br/buscatextual/download.do?metodo='\
               'apresentar&idcnpq=' + long_id
    input_locator = 'informado'
    captcha_locator = 'image_captcha'
    while True:
        # print '{}download_cv: loading long_url'.format(pname)
        driver.get(long_url)
        # print '{}download_cv: waiting for it to load...'.format(pname)
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.ID,
                                                             captcha_locator)))
        # print '{}download_cv: cracking captcha...'.format(pname)
        code = crack_captcha(driver)
        if len(code) != 4:
            # print '{}download_cv: wrong captcha: {}'.format(pname, code)
            continue
        if len(code) == 4:
            # print '{}download_cv: captcha: {}'.format(pname, code)
            break
    # print '{}download_cv: entering captcha: {}'.format(pname, code)
    element = driver.find_element(By.ID, input_locator)
    element.clear()
    element.send_keys(code + '\n')
    # print '{}download_cv: waiting for download...'.format(pname)
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.invisibility_of_element_located((By.ID,
                                                             captcha_locator)))

def worker(short_id_list):
    """Given a list of short_ids it iterates over them to get the long_id."""
    driver = LattesDriver().get_driver()
    pname = current_process().name
    output_file = open(LONG_ID_FILE, 'w')
    for count, short_id in enumerate(short_id_list):
        while True:
            img_req = captcha_image(get_short_url(short_id))
            image_name = 'temp_' + pname + '.png'
            open(image_name, 'wb').write(img_req.content)
            code = Captcha(image_name).get_text().upper()
            if len(code) != 4:
                # print '{}worker: code != 4: {}'.format(pname, code)
                continue
            elif len(code) == 4:
                # print '{}worker: code == 4: {}'.format(pname, code)
                inf_req = inform_captcha(img_req, code)
                post_do(inf_req)
                cv_req = cv_view(inf_req)
                if verify_page(cv_req) == 'CVPAGE':
                    # print '{}worker: inside CVPAGE, getting long_id'.format(pname)
                    long_id = scrap_long_id(cv_req)
                    print '{}-[{}/{}]=> short_id: {}  |  long_id: {}'.format(
                        pname, count+1, len(short_id_list), short_id, long_id)
                    output_file.write(short_id + ' | ' + long_id + '\n')
                    # print '{}worker: Downloading the cv for long_id: {}'.format(pname, long_id)
                    download_cv(driver, long_id)
                    break
                elif verify_page(cv_req) == 'NOTFOUND':
                    print '{}-[{}/{}]=> short_id: {}  |  long_id: NOTFOUND'.format(
                        pname, count+1, len(short_id_list), short_id)
                    output_file.write(short_id + ' | NOTFOUND\n')
                    break
    driver.close()

def main():
    """Main function, which controls the workflow of the program."""
    short_id_list = short_ids(SHORT_ID_FILE)
    splited_lists = split_list(short_id_list[0:100], CORES)
    for splited_list in range(len(splited_lists)):
        temp = (splited_lists[splited_list],)
        process = Process(target=worker, args=temp)
        process.start()


if __name__ == '__main__':
    main()
