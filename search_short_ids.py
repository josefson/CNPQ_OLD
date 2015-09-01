# -*- coding: utf-8 -*-
"""
This module holds functions capable of scrap resuling shortIds of a query into
the lattes curriculum database. It is known that we need those shortIds in
order to get the longIds, which we need to get the xml curriculum.
"""
import re
import time
import datetime
import requests
import argparse
from bs4 import BeautifulSoup
from multiprocessing import Process, current_process


INTERVAL = 1000   # results per page.

def split_list(alist, wanted_parts=1):
    """Split a list of intervals in n parts in order to be multiprocessed."""
    length = len(alist)
    return [alist[i*length // wanted_parts: (i+1)*length // wanted_parts]
            for i in range(wanted_parts)]

def search(reg_from, reg_to):
    """Performs a page requests given an interval."""
    url = ('http://buscatextual.cnpq.br/buscatextual/busca.do?metodo='
           'forwardPaginaResultados&registros=' + str(reg_from) + ';' +
           str(reg_to) + '&query=%28+%2Bidx_nacionalidade%3Ae%29+or+%28+'
           '%2Bidx_nacionalidade%3Ab%29&analise=cv&tipoOrdenacao=null&'
           'paginaOrigem=index.do&mostrarScore=false&mostrarBandeira=true'
           '&modoIndAdhoc=null')
    results = requests.get(url)
    return results

def results_total():
    """Returns the total of results inside the search() query. This is used
    in order to multiprocess and create the pagination list."""
    results = search(0, 10)
    soup = BeautifulSoup(results.content, 'lxml')
    return int(str(soup.find('b')).lstrip('<b>').rstrip('</b>'))

def process_people(search_result):
    """Returns a list of tuples."""
    soup = BeautifulSoup(search_result.content, 'lxml')
    links = soup.find_all(href=re.compile('javascript:abreDetalhe'))
    people = []
    for link in links:
        string = str(link)
        left = string.rfind('(') + 1
        right = string.rfind(')')
        data = string[left:right].replace("'", "").split(',')
        data = tuple(data)
        people.append(data)
    return people

def pagination():
    """Returns a list of pages, where page is an interval of registers,
    from/to."""
    total = results_total()
    print 'Total of registers: {}'.format(total)
    pages = range(0, total, INTERVAL)
    return pages

def worker(page_list, short_id_file):
    """This is the function to be multiprocessed. It iterates over a list of
    pagigation values, requesting, scraping the shortIds of each
    result in its html, and writing it inside an external data file."""
    data = open(short_id_file, 'a')
    pname = current_process().name
    start = time.time()
    time_stamp = datetime.datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S')
    print '{}- {}'.format(pname, time_stamp)
    for reg_from in page_list:
        print '{}- Scrapping from {} to {} registers'.format(pname, reg_from, reg_from + INTERVAL)
        researchers = process_people(search(reg_from, INTERVAL))
        for researcher in researchers:
            if len(researcher) > 0:
                data.write('{}\n'.format(researcher[0]))
                data.flush()
    data.close()
    end = time.time()
    time_stamp = datetime.datetime.fromtimestamp(end).strftime('%Y-%m-%d %H:%M:%S')
    print '{}- {}'.format(pname, time_stamp)

def main(workers, o_file):
    """Main function, which controls the workflow of the program."""
    cores = workers
    short_id_file = o_file
    pages = pagination()
    pages_core = split_list(pages, wanted_parts=cores)
    for i in range(len(pages_core)):
        temp = (pages_core[i], short_id_file,)
        process = Process(target=worker, args=temp)
        process.start()


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('-w', '--worker', dest='cores', required=True,
                        type=int, help='number of workers to split the task.')
    PARSER.add_argument('-o', '--output', dest='short_id_file', required=True,
                        type=str, help='ShortIDs output file.')
    ARGS = PARSER.parse_args()
    main(ARGS.cores, ARGS.short_id_file)
