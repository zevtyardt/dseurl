#!usr/bin/python2.7

import requests
import multiprocessing.pool
import sys
import re
import os
import urlparse
import logging
import argparse
import time

logging.basicConfig(format='\r%(message)s', level=logging.INFO)
reload(sys)
sys.setdefaultencoding('utf-8')

ENGINE = {
    'google': ('https://www.google.com/search?q={query}', 'start', '0', True),
    'bing': ('https://www.bing.com/search?q={query}', 'first', '1', True),
    'yahoo': ('https://search.yahoo.com/search?p={query}', 'b', '1', True),
    'duckduckgo': ('https://www.duckduckgo.com/?q={query}', None, None, False),
    'startpage': ('https://www.startpage.com/do/search?q={query}', None, None, False),
    'yandex': ('https://yandex.ru/yandsearch?text={query}', None, None, False),
    'baidu': ('https://www.baidu.com/s?wd={query}', 'pn', '0', True),
    'ecosia': ('https://www.ecosia.org/search?q={query}', None, None, False),
    'goodreads': ('https://www.goodreads.com/search?q={query}', None, None, False),
    'givero': ('https://www.givero.com/search?q={query}', None, None, False),
    'dogpile': ('http://results.dogpile.com/search/web?q={query}', None, None, False),
    'aol': ('https://search.aol.com/aol/search?q={query}', None, None, False),
    'ask': ('http://www.search.ask.com/web?q={query}', None, None, False),
    'webcrawler': ('http://www.webcrawler.com/serp?q={query}', None, None, False),
    'info': ('http://www.info.com/serp?q={query}', None, None, False),
    'infospace': ('http://search.infospace.com/search/web?q={query}', None, None, False),
    'gigablast': ('https://www.gigablast.com/search?q={query}', 's', '0', True),
    'hotbot': ('https://www.hotbot.com/web/search?q={query}', None, None, False),
    'metacrawler': ('http://www.metacrawler.com/serp?q={query}', 'page', None, False),
    'lycos': ('http://search.lycos.com/web/?q={query}', None, None, False),
    'mojeek': ('https://www.mojeek.com/search?q={query}', 's', '1', False),
    'qwant': ('https://www.qwant.com/?q={query}', None, None, False),
    'sogou': ('https://wap.sogou.com/web/searchList.jsp?keyword={query}', None, None, False),
    'swisscows': ('https://swisscows.com/web?query={query}', 'offset', '0', True),
    }

BLACKLIST = [
    'twitter.com', 'microsoft.com', 'facebook.com', 'fb.com', 'instagram.com' # netloc
    ] # XXX: You can add regex pattern to the list or only netloc from the url
BLACKLIST += [_[0] for _ in ENGINE.items()]

engine_, fuzz = 0, False
rev = []

def get_url(items):
    global engine_, global_urls, fuzz, rev
    url_base, page, add, minone, name = items
    if page:
        url_base += '&%s={}%s' % (page, add if add else '')
    proxy = {'https': arg.proxy, 'http': arg.proxy} if arg.proxy else None
    eng_ = False
    page_int = arg.page if page else 1
    for num in range(1, page_int + 1):
        page = num
        if minone:
            page -= 1
        temp = []
        try:
            r = requests.get(url_base.format(page),
                headers={'User-Agent': arg.useragent}, timeout=arg.timeout,
                proxies=proxy)
        except Exception as e:
            logging.info('[CRITICAL] %s:%s: %s', name, num, e)
            return
        if re.search(r'(?:re)?chaptcha(?:.min.js)?', r.text):
            logging.info('[CAPTCHA] %s:%s: our system has detected it as a bot', name, num)
        else:
            urls = [_[1] for _ in re.findall(r'<a.*?href=(?P<quote>["\'])(.*?)(?P=quote)', r.text)]
            for url in urls:
                if url.startswith('/url?q='):
                    url = url[7:]
                parse = urlparse.urlparse(url)
                if parse.scheme and parse.netloc:
                    if url not in rev and len(url.split('/')) > 4 and not re.search(r'|'.join(BLACKLIST), url):
                        with open(os.path.join(arg.dir, arg.file), 'a') as f:
                            f.write(url + '\n')
                        temp.append(url)
            if temp:
                logging.info('[%s:%s] -> %s url(s)', name.upper(), num, len(temp))
                if arg.print_:
                    logging.info('')
                    for url in temp:
                        logging.info('- %s', url)
                    logging.info('-' * 25)
                fuzz = True
                rev += temp
        if temp:
            if not eng_:
                engine_ += 1
                eng_ = True

def _ArgumentParser():
    cpu_count = multiprocessing.pool.cpu_count()
    parser = argparse.ArgumentParser(description='website list grabber from many search engine', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('query', nargs='*', help='query to be searched')
    parser.add_argument('-p', metavar='PAGE', dest='page', help='number of pages to be taken (default 1)', default=1, type=int)
    parser.add_argument('-t', metavar='THREAD', dest='pool', help='number of threads (default %s)' % cpu_count, default=cpu_count, type=int)
    parser.add_argument('-e', metavar='NAME', dest='engine', help='search engine to be used (default all)', default='all')
    parser.add_argument('-u', metavar='AGENT', dest='useragent', help='specify a custom user agent', default='Mozilla/5.0 (X11; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0')
    parser.add_argument('-i', metavar='TIME', dest='timeout', help="time before giving up, in seconds (default 15)", default=15, type=int)
    parser.add_argument('-x', metavar='PROXY', dest='proxy', help="Use the specified HTTP/HTTPS proxy.")
    parser.add_argument('-d', metavar='DIR', dest='dir', help='output directory (default $HOME/dse)', default=os.path.join(os.environ['HOME'], 'dse'))
    parser.add_argument('-f', metavar='file', dest='file', help='output filename (default urls.txt)', default='urls.txt')
    parser.add_argument('-b', metavar='BLACKLIST', action='append', dest='blacklist', help='add regex pattern to the blacklist\nor only netloc from the url')
    parser.add_argument('-q', '--print', action='store_true', dest='print_', help='print url on terminal screen')
    parser.add_argument('-l', '--list', action='store_true', help='print all supported search engines')
    parser.add_argument('-V', '--verbose', action='store_true', help='verbose mode')
    return parser.parse_args()

def print_banner():
    logging.info('''\x1b[32;1m
.-.  .-. .-.
|  ) `-. |-
`-'  `-' `-'  url seekers [zvtyrdt.id]
        \x1b[0m''')

def print_info(kwargs):
    add_ = {'timeout': 'seconds', 'pool': 'threads', 'page': 'pages'}
    kwargs['path'] = os.path.join(arg.dir, arg.file)
    for q in sorted(kwargs.keys()):
        key, item = q, kwargs[q]
        if item and key not in ('dir', 'file', 'list', 'verbose', 'print_'):
            if key == 'engine':
                if item == 'all':
                    item = ENGINE.keys()
                else:
                    item = [item]
            elif key == 'query':
                item = "'{}'".format(item)
            elif key == 'proxy':
                item_split = item.split(':')
                if len(item_split) == 2:
                    item = 'host: {}, port: {}'.format(*item_split)
            elif add_.get(key):
                item = '{} {}'.format(item, add_[key])
            logging.info('[SET] %s: %s', key.upper(), item)
    logging.info('-' * 25)

def print_list():
    baseurl = '{0.scheme}://{0.netloc}'
    lenght = [len(str(len(ENGINE))),
              max([len(_) for _ in ENGINE.keys()]),
              max([len(baseurl.format(urlparse.urlparse(_[1][0]))) for _ in ENGINE.items()])]
    if lenght[0] < 4:
        lenght[0] = 4
    table = '| {0:^%s} | {1:<%s} | {2:<%s} |' % (lenght[0], lenght[1], lenght[2])
    startend = '+-%s-+-%s-+-%s-+' % ('-' * lenght[0], '-' * lenght[1], '-' * lenght[2])

    # display on the terminal
    logging.info('[NONE] print all supported search engines\n')
    logging.info(startend)
    logging.info(table.replace('<', '^').format('NUM', 'NAME', 'WEBSITE'))
    logging.info(startend)
    for num, (name, (url, _, __, ___)) in enumerate(ENGINE.items(), start=1):
        logging.info(table.replace('^', '>').format(str(num) + '.', name,
            baseurl.format(urlparse.urlparse(url))))
    logging.info(startend + '\n')

def main():
    global arg, path, ENGINE, BLACKLIST, rev
    print_banner()
    arg = _ArgumentParser()
    if arg.list:
        sys.exit(print_list())
    if not arg.query:
        sys.exit('[FALSE] what are you looking for?\n')
    if arg.engine not in ENGINE.keys() + ['all']:
        sys.exit('[FALSE] search engine \'%s\' not supported\n        type --list to display all supported search engines\n' % arg.engine)
    if arg.blacklist:
        BLACKLIST += arg.blacklist
    arg.query = ' '.join(arg.query)
    if arg.verbose:
        print_info(arg.__dict__)
    else:
        logging.info('[BEGIN] starting @ %s', time.strftime('%c'))
        logging.info('-' * 25)
    p = multiprocessing.pool.ThreadPool(arg.pool)
    if not os.path.isdir(arg.dir):
        os.mkdir(arg.dir)
    try:
        if arg.engine != 'all':
            ENGINE = {arg.engine: ENGINE[arg.engine]}
        urls_ = [(ENGINE[name][0].format(query=arg.query), ENGINE[name][1], ENGINE[name][2], ENGINE[name][3], name) for name in ENGINE]
        p.map_async(get_url, urls_).get(9999)
        if rev:
            if not arg.print_:
                logging.info('-' * 25)
            sys.exit('[FINISH] got %s urls from %s search engine(s), saved on \'%s/urls.txt\'\n' % (len(rev), engine_, arg.dir))
        else:
            sys.exit('[FINISH] skipped, no url found\n')
    except KeyboardInterrupt:
        if fuzz:
            if not arg.print_:
                logging.info('\r' + ('-' * 25))
        sys.exit('\r[ERROR] user interrupt\n')

if __name__ == '__main__':
    main()
