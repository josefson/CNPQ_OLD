# -*- coding: utf-8 -*-
"""
This file is responsible to download the curriculum xml
"""
import glob
import requests
from captcha import Captcha
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


def captcha_page(session, long_id):
    captcha_url = 'http://buscatextual.cnpq.br/buscatextual/servlet/captcha?'\
                  'metodo=getImagemCaptcha'
    headers = {}
    headers['Accept'] = 'image/png,image/*;q=0.8,*/*;q=0.5'
    headers['Accept-Encoding'] = 'gzip, deflate'
    headers['Accept-Language'] = 'en-US,en;q=0.5'
    headers['Connection'] = 'keep-alive'
    headers['DNT'] = '1'
    headers['Host'] = 'buscatextual.cnpq.br'
    headers['Referer'] = 'http://buscatextual.cnpq.br/buscatextual/download.'\
                         'do?metodo=apresentar&idcnpq=' + long_id
    img_name = 'cap_page.png'
    cap_req = session.get(captcha_url, headers=headers)
    open('cap_page.png', 'wb').write(cap_req.content)
    code = Captcha(img_name).get_text().upper()
    return code


def inform_captcha(session, code, long_id):
    headers = {}
    headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
    headers['Accept-Encoding'] = 'gzip, deflate'
    headers['Accept-Language'] = 'en-US,en;q=0.5'
    headers['Connection'] = 'keep-alive'
    headers['DNT'] = '1'
    headers['Host'] = 'buscatextual.cnpq.br'
    headers['Referer'] = 'http://buscatextual.cnpq.br/buscatextual/download.'\
                         'do?metodo=apresentar&idcnpq=' + long_id
    headers['X-Requested-With'] = 'XMLHttpRequest'
    inform_captcha_url = 'http://buscatextual.cnpq.br/buscatextual/servlet/'\
                         'captcha?informado=' + code + '&metodo=validaCaptcha'
    inf_cap_req = session.get(inform_captcha_url, headers=headers) 
    open('inf_cap.html', 'w').write(inf_cap_req.content)
    return inf_cap_req


def post_do(session, long_id):
    headers = {}
    headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;'\
                        'q=0.9,*/*;q=0.8'
    headers['Accept-Encoding'] = 'gzip, deflate'
    headers['Accept-Language'] = 'en-US,en;q=0.5'
    headers['Connection'] = 'keep-alive'
    headers['DNT'] = '1'
    headers['Host'] = 'buscatextual.cnpq.br'
    headers['Referer'] = 'http://buscatextual.cnpq.br/buscatextual/download.'\
                         'do?metodo=apresentar&idcnpq=' + long_id
    post_url = 'http://buscatextual.cnpq.br/buscatextual/download.do'
    files = {'metodo': (None, 'captchaValido'), 'idcnpq': (None, long_id),
             'informado': (None, '')}
    r = session.post(post_url, files=files, headers=headers)
    name = long_id + '.zip'
    if glob.glob(name) == []:
        open(long_id + '.zip', 'w').write(r.content)


def inform_captcha2(session, code, short_id):
    headers = {}
    headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
    headers['Accept-Encoding'] = 'gzip, deflate'
    headers['Accept-Language'] = 'en-US,en;q=0.5'
    headers['Connection'] = 'keep-alive'
    headers['DNT'] = '1'
    headers['Host'] = 'buscatextual.cnpq.br'
    headers['Referer'] = 'http://buscatextual.cnpq.br/buscatextual/'\
                         'visualizacv.do?id=' + short_id
    headers['X-Requested-With'] = 'XMLHttpRequest'
    inform_captcha_url = 'http://buscatextual.cnpq.br/buscatextual/servlet/'\
                         'captcha?informado=' + code + '&id=' + short_id + \
                         '&metodo=validaCaptcha'
    inf_cap_req = session.get(inform_captcha_url, headers=headers) 
    open(short_id + 'inf_cap.html', 'w').write(inf_cap_req.content)
    return inf_cap_req


def post_do2(session, short_id):
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
    post_url = 'http://buscatextual.cnpq.br/buscatextual/visualizacv.do'
    files = {'metodo': (None, 'captchaValido'), 'id': (None, short_id),
             'idiomaExibicao': (None, ''), 'tipo': (None, ''),
             'informado': (None, '')}
    r = session.post(post_url, files=files, headers=headers)
    open(short_id + '.html', 'w').write(r.content)


l = []
l.append('4493552623803659')
l.append('0751456439777100')
l.append('1356405803334452')
l.append('7903439648501971')
l.append('3754103763121724')
l.append('2713462421161479')
l.append('8310168572964653')
l.append('0069394390396243')
l.append('1024601314143406')
l.append('1024601314143406')

s = []
s.append('K4220227Z6')
s.append('K4779608J7')
s.append('K4723010U3')
s.append('K4493898Y9')
s.append('K8789234Y8')
s.append('K8715722A4')
s.append('K8774768P7')
s.append('K8761067J9')
s.append('K4848408P6')
s.append('K4429599A8')

# for i in l:
#     session = requests.Session()
#     code = captcha_page(session, i)
#     print code
#     r = inform_captcha(session, code, i)
#     post_do(session, i)

for i in s:
    session = requests.Session()
    code = captcha_page(session, i)
    print code
    inform_captcha2(session, code, i)
    post_do2(session, i)
