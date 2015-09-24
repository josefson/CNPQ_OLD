# -*- coding: utf-8 -*-
"""
This file is responsible to download the curriculum xml
"""
import re
import os
import glob
import logging
import requests
import argparse
from captcha import Captcha
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from multiprocessing import Process, current_process


LOG_FILENAME = 'log.txt'
FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
USER_AGENT = UserAgent(cache=False)
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


def get_long_url(long_id):
    """Returns a long_url for a given long_id."""
    base_url = 'http://buscatextual.cnpq.br/buscatextual/download.do?metodo='\
               'apresentar&idcnpq='
    return base_url + str(long_id)


def captcha_page(session, referer, pname):
    """Takes a Session and long_id and retrieves a captcha.png file to be
    processed. Returning the cracked code for its caller."""
    captcha_url = 'http://buscatextual.cnpq.br/buscatextual/servlet/captcha?'\
                  'metodo=getImagemCaptcha'
    headers = {}
    headers['Accept'] = 'image/png,image/*;q=0.8,*/*;q=0.5'
    headers['Accept-Encoding'] = 'gzip, deflate'
    headers['Accept-Language'] = 'en-US,en;q=0.5'
    headers['Connection'] = 'keep-alive'
    headers['DNT'] = '1'
    headers['Host'] = 'buscatextual.cnpq.br'
    headers['Referer'] = referer
    headers['User-Agent'] = USER_AGENT.random
    img_name = 'captcha_' + current_process().name + '.png'
    while True:
        try:
            logging.info('%s-captcha_page: Getting captcha page.', pname)
            req = session.get(captcha_url, headers=headers)
        except requests.exceptions.Timeout as terror:
            logging.info('%s-captcha_page: Timeout: %s\nTrying again...',
                         pname, terror)
            continue
        except requests.exceptions.ConnectionError as cerror:
            logging.info('%s-captcha_page: Connection Error: %s\nTrying '
                         'again...', pname, cerror)
            continue
        except requests.exceptions.RequestException as rerror:
            logging.info('%s-captcha_page: Request Error: %s\nTrying '
                         'again...', pname, rerror)
            continue
        open(img_name, 'wb').write(req.content)
        code = Captcha(img_name).get_text().upper()
        if len(code) == 4:
            logging.info('%s-captcha_page: Right captcha length: %s',
                         pname, code)
            return code


def inform_captcha(session, url, referer, pname):
    """Takes a Session, a lon."" and a cracked captcha code, it informs the
    code to the server in order to get a success response."""
    expected_content = '{"estado":"sucesso"}\r\n'
    headers = {}
    headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
    headers['Accept-Encoding'] = 'gzip, deflate'
    headers['Accept-Language'] = 'en-US,en;q=0.5'
    headers['Connection'] = 'keep-alive'
    headers['DNT'] = '1'
    headers['Host'] = 'buscatextual.cnpq.br'
    headers['Referer'] = referer
    headers['User-Agent'] = USER_AGENT.random
    headers['X-Requested-With'] = 'XMLHttpRequest'
    while True:
        try:
            logging.info('%s-inform_captcha: Informing captcha for '
                         'download.', pname)
            req = session.get(url, headers=headers)
        except requests.exceptions.Timeout as terror:
            logging.info('%s-inform_captcha: Timeout: %s\nTrying '
                         'again...', pname, terror)
            continue
        except requests.exceptions.ConnectionError as cerror:
            logging.info('%s-inform_captcha: Connection Error: '
                         '%s\nTrying again...', pname, cerror)
            continue
        except requests.exceptions.RequestException as rerror:
            logging.info('%s-inform_captcha: Request Error: %s\n'
                         'Trying again...', pname, rerror)
            continue
        if req.content == expected_content:
            logging.info('%s-inform_captcha: Captcha informed with '
                         'sucess.', pname)
            return True
        else:
            logging.info('%s-inform_captcha: Captcha informed was '
                         'wrong.', pname)
            return False


def post_cv(session, short_id, pname):
    """This function is responsible to get the CVPAGE."""
    post_url = 'http://buscatextual.cnpq.br/buscatextual/visualizacv.do'
    headers = {}
    headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;'\
                        'q=0.9,*/*;q=0.8'
    headers['Accept-Encoding'] = 'gzip, deflate'
    headers['Accept-Language'] = 'en-US,en;q=0.5'
    headers['Connection'] = 'keep-alive'
    headers['DNT'] = '1'
    headers['Host'] = 'buscatextual.cnpq.br'
    headers['Referer'] = 'http://buscatextual.cnpq.br/buscatextual/'\
                         'visualizacv.do?id=' + short_id
    headers['User-Agent'] = USER_AGENT.random
    files = {'metodo': (None, 'captchaValido'), 'id': (None, short_id),
             'idiomaExibicao': (None, ''), 'tipo': (None, ''),
             'informado': (None, '')}
    while True:
        try:
            req = session.post(post_url, files=files, headers=headers)
            logging.info('%s-post_cv: Getting CVPAGE...', pname)
            return req
        except requests.exceptions.Timeout as terror:
            logging.info('%s-post_cv: Timeout: %s\nTrying again...',
                         pname, terror)
            continue
        except requests.exceptions.ConnectionError as cerror:
            logging.info('%s-post_cv: Connection Error: %s\nTrying '
                         'again...', pname, cerror)
            continue
        except requests.exceptions.RequestException as rerror:
            logging.info('%s-post_cv: Request Error: %s\nTrying '
                         'again...', pname, rerror)
            continue


def post_download(session, long_id, pname):
    """This method is responsible for downloading the curriculum zip file."""
    post_url = 'http://buscatextual.cnpq.br/buscatextual/download.do'
    referer = 'http://buscatextual.cnpq.br/buscatextual/download.do?metodo='\
              'apresentar&idcnpq=' + long_id
    headers = {}
    headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;'\
                        'q=0.9,*/*;q=0.8'
    headers['Accept-Encoding'] = 'gzip, deflate'
    headers['Accept-Language'] = 'en-US,en;q=0.5'
    headers['Connection'] = 'keep-alive'
    headers['DNT'] = '1'
    headers['Host'] = 'buscatextual.cnpq.br'
    headers['Referer'] = referer
    headers['User-Agent'] = USER_AGENT.random
    files = {'metodo': (None, 'captchaValido'), 'idcnpq': (None, long_id),
             'informado': (None, '')}
    while True:
        try:
            req = session.post(post_url, files=files, headers=headers)
            logging.info('%s-post_download: Downloading...', pname)
        except requests.exceptions.Timeout as terror:
            logging.info('%s-post_download: Timeout: %s\nTrying again...',
                         pname, terror)
            continue
        except requests.exceptions.ConnectionError as cerror:
            logging.info('%s-post_download: Connection Error: %s\nTrying '
                         'again...', pname, cerror)
            continue
        except requests.exceptions.RequestException as rerror:
            logging.info('%s-post_download: Request Error: %s\nTrying '
                         'again...', pname, rerror)
            continue
        zip_name = 'xmls/' + long_id + '.zip'
        open(zip_name, 'w').write(req.content)
        if glob.glob('xmls/' + long_id + '*') != []:
            logging.info('%s-post_download: Download in file-system.', pname)
            break
        else:
            logging.info('%s-post_download: Download not in file-system. '
                         'Trying again...', pname)
            continue


def download_curriculum(long_id, pname):
    """This function is responsible for organize the download multi-step
    requesting. And also to remove complexity of the worker function."""
    session = requests.Session()
    while True:
        referer = get_long_url(long_id)
        code = captcha_page(session, referer, pname)
        inform_url = 'http://buscatextual.cnpq.br/buscatextual/servlet/'\
                     'captcha?informado=' + code + '&metodo=validaCaptcha'
        if inform_captcha(session, inform_url, referer, pname) is True:
            break
    post_download(session, long_id, pname)


def get_cv_page(short_id, pname):
    """This function control the workflux of how to get to the CVPAGE.
    Returning a CVPAGE request object"""
    session = requests.Session()
    while True:
        referer = get_short_url(short_id)
        code = captcha_page(session, referer, pname)
        inform_url = 'http://buscatextual.cnpq.br/buscatextual/servlet/'\
                     'captcha?informado=' + code + '&id=' + short_id + \
                     '&metodo=validaCaptcha'
        if inform_captcha(session, inform_url, referer, pname) is True:
            req = post_cv(session, short_id, pname)
            return req


def verify_page(page_req):
    """Given a page request returns a match of which page it belongs to."""
    input_box_id = 'informado'
    cv_page_req_href = 'download'
    not_found_match = "<html><head><title>Curr\xedculo n\xe3o encontrado!"\
                      "</title></head><body><div style='font-family:Arial;"\
                      "font-size=10pt;align:center;color:red;font-weight:"\
                      "bold'>Curr\xedculo n\xe3o encontrado</div></body>"\
                      "</html>"
    content = page_req.content
    soup = BeautifulSoup(content, 'lxml')
    if soup.find(id=input_box_id):
        return 'CAPTCHA'
    elif soup.find(href=re.compile(cv_page_req_href)):
        return 'CVPAGE'
    else:
        if content == not_found_match:
            return 'NOTFOUND'


def scrap_long_id(cv_page_req):
    """Given a request from the CVPAGE it scraps and returns a long_id."""
    source = cv_page_req.content
    soup = BeautifulSoup(source, 'lxml')
    link = soup.find(href=re.compile(r'(\d{16})'))
    if link is None:
        return 'NOTFOUND'
    else:
        long_id = re.search(r'(\d{16})', str(link)).group(1)
        return long_id


def not_found(output_file, pname, loop_count, total_count, short_id):
    """This method does things when a NOTFOUND page is found."""
    logging.info('%s-[%s/%s]=> short_id: %s | long_id: NOTFOUND', pname,
                 loop_count+1, total_count, short_id)
    output_file.write(short_id + ' | NOTFOUND\n')
    output_file.flush()
    print '{}-[{}/{}]=> short_id: {} | NOTFOUND'.format(
        pname, loop_count+1, total_count, short_id)


def worker(short_id_list, long_id_file, nice, verbose):
    """Given a list of short_ids it iterates over them to get the long_id."""
    if nice is True:
        os.nice(20)
    pname = current_process().name
    logging.info('%s: Started', pname)
    output_file = open(long_id_file, 'a')
    for count, short_id in enumerate(short_id_list):
        while True:
            try:
                logging.info('%s- Getting CVPAGE for short_id: %s',
                             pname, short_id)
                cv_req = get_cv_page(short_id, pname)
                page = verify_page(cv_req)
                if page == 'CVPAGE':
                    logging.info('%s- Inside CVPAGE, scraping long_id', pname)
                    if scrap_long_id(cv_req) == 'NOTFOUND':
                        logging.info('%s- Inside CVPAGE, NO long_id!!', pname)
                        not_found(output_file, pname, count,
                                  len(short_id_list), short_id)
                        break
                    else:
                        long_id = scrap_long_id(cv_req)
                        logging.info('%s-[%s/%s]=> short_id: %s | long_id: %s',
                                     pname, count+1, len(short_id_list),
                                     short_id, long_id)
                        output_file.write(short_id + ' | ' + long_id + '\n')
                        output_file.flush()
                        if verbose is True:
                            print '{}-[{}/{}]=> short_id: {} | long_id: {}'.\
                                    format(pname, count+1, len(short_id_list),
                                           short_id, long_id)
                    while True:
                        try:
                            logging.info('%s- Downloading the CV for long_id:'
                                         ' %s', pname, long_id)
                            download_curriculum(long_id, pname)
                            logging.info('%s- Download finished!', pname)
                            break
                        except:
                            logging.info('%s- Download failed. '
                                         'Trying again...', pname)
                            continue
                    break
                if page == 'NOTFOUND':
                    not_found(output_file, pname, count, len(short_id_list),
                              short_id)
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
    cleanup(pname[-1])


def main(workers, i_file, o_file, nice, verbose):
    """Main function, which controls the workflow of the program."""
    short_id_file = i_file
    long_id_file = o_file
    cores = workers
    short_id_list = short_ids(short_id_file)
    splited_lists = split_list(short_id_list, cores)
    for splited_list in range(len(splited_lists)):
        temp = (splited_lists[splited_list], long_id_file, nice, verbose)
        process = Process(target=worker, args=temp)
        process.start()

if __name__ == '__main__':
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('-w', '--worker', dest='cores', required=True,
                        type=int, help='Required: Number of workers to split '
                        'the task into processes. This is done in order to '
                        'get a higher cpu time.')
    PARSER.add_argument('-i', '--input', dest='short_id_file', required=True,
                        type=str, help='Required: A input file filled with '
                        'short_ids separated by new-line-characters.')
    PARSER.add_argument('-o', '--output', dest='long_id_file', required=True,
                        type=str, help='Required: A output file to be writen '
                        'with long_idsa. Since long_ids are the Primary Keys'
                        ', those could be useful in the future.')
    PARSER.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        default=False, help='Optional: Allow you to see the '
                        'scrap/download progress.')
    PARSER.add_argument('-n', '--nice', dest='nice', action='store_true',
                        default=False, help='Optional: This sets the workers'
                        ' with the highest niceness/cpu-priiority possible.')
    ARGS = PARSER.parse_args()
    if ARGS.nice is True:
        os.nice(20)
    main(ARGS.cores, ARGS.short_id_file, ARGS.long_id_file, ARGS.nice,
         ARGS.verbose)
