# -*- coding: utf-8 -*-
"""
This file is responsible to download the curriculum xml
"""
import re
import os
import sys
import glob
import logging
import requests
import argparse
from PIL import Image
from captcha import Captcha
from bs4 import BeautifulSoup
from util import getUserAgent
from driver import LattesDriver
from selenium.webdriver.common.by import By
from multiprocessing import Process, current_process
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException


LOG_FILENAME = 'log.txt'
FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, filename=LOG_FILENAME, level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


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


def cleanup(pnumber):
    """This function will clean temporary files created by a process, given a
    process number."""
    trash = glob.glob('*' + str(pnumber) + '.png')
    if trash:
        for i in trash:
            os.remove(i)


def get_short_url(short_id):
    """Returns a short_url for a given short_id."""
    base_url = 'http://buscatextual.cnpq.br/buscatextual/'\
               'visualizacv.do?id='
    return base_url + str(short_id)


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
            logging.info('%s-download_cv: Wrong captcha length: %s. Trying '
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
    os.nice(-20)
    pname = current_process().name
    logging.info('%s: Started', pname)
    try:
        lattesdriver = LattesDriver()
        display = lattesdriver.get_display()
        driver = lattesdriver.get_driver()
    except WebDriverException, error:
        print error
        sys.exit('Failed to initialize selenium drivers. Calm down, '
                 'sometimes this happens, please try again. If this error '
                 'persists check if the Browser version is compatible with '
                 'selenium.')
    output_file = open(long_id_file, 'a')
    for count, short_id in enumerate(short_id_list):
        while True:
            try:
                logging.info('%s- Getting CVPAGE for shortid: %s',
                             pname, short_id)
                headers = {}
                headers['User-Agent'] = getUserAgent()
                cv_req = requests.get(get_short_url(short_id), headers=headers)
                page = verify_page(cv_req)
                if page == 'CVPAGE':
                    logging.info('%s- Inside CVPAGE, scraping long_id', pname)
                    long_id = scrap_long_id(cv_req)
                    logging.info('%s-[%s/%s]=> short_id: %s | long_id: %s',
                                 pname, count+1, len(short_id_list), short_id,
                                 long_id)
                    output_file.write(short_id + ' | ' + long_id + '\n')
                    output_file.flush()
                    # print '{}-[{}/{}]=> short_id: {} | long_id: {}'.format(
                    #     pname, count+1, len(short_id_list), short_id,
                    #     long_id)
                    while True:
                        try:
                            logging.info('%s- Downloading the CV for long_id:'
                                         ' %s', pname, long_id)
                            download_cv(driver, long_id)
                            logging.info('%s- Download finished!', pname)
                            break
                        except Exception, derror:
                            logging.info('%s- Download failed. Trying again',
                                         pname)
                            continue
                    break
                elif page == 'NOTFOUND':
                    logging.info('%s-[%s/%s]=> short_id: %s | long_id: '
                                 'NOTFOUND', pname, count+1,
                                 len(short_id_list), short_id)
                    output_file.write(short_id + ' | NOTFOUND\n')
                    output_file.flush()
                    print '{}-[{}/{}]=> short_id: {} | NOTFOUND'.format(
                        pname, count+1, len(short_id_list), short_id)
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
    driver.close()
    display.stop()
    cleanup(pname[-1])


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
    os.nice(-20)
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('-w', '--worker', dest='cores', required=True,
                        type=int, help='number of workers to split the task.')
    PARSER.add_argument('-i', '--input', dest='short_id_file', required=True,
                        type=str, help='ShortIds file as input.')
    PARSER.add_argument('-o', '--output', dest='long_id_file', required=True,
                        type=str, help='LongIDs output file.')
    ARGS = PARSER.parse_args()
    main(ARGS.cores, ARGS.short_id_file, ARGS.long_id_file)
