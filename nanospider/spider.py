from gevent import monkey, queue, pool, spawn
monkey.patch_all()

import requests, traceback, url
from lxml import etree

from scrapelib import Scraper
from scrapelib.cache import SQLiteCache

class SpiderScraper(Scraper):
    def __init__(self, cache_path, allowed_hosts=(), requests_per_minute=0, **kwargs):
        kwargs['requests_per_minute'] = requests_per_minute
        super(SpiderScraper, self).__init__(**kwargs)

        self.cache_storage = SQLiteCache(cache_path)
        self._allowed_hosts = set(allowed_hosts)

    def should_cache_response(self, response):
        return response.status_code == 200 and \
            url.parse(response.url)._host in self._allowed_hosts and \
            'html' in response.headers.get('content-type', 'text/html').lower()

class Spider(object):
    def __init__(self, domain, cache_path, workers=2):
        self.domain = domain
        self._queue = queue.JoinableQueue()
        self._seen = set()
        self._workers = []
        self._worker_count = workers
        self._allowed_hosts = set()

        self._allowed_hosts.add(domain)
        self._add_to_queue(url.parse("http://%s/" % domain))

        self._scraper = SpiderScraper(cache_path, self._allowed_hosts)

    def _add_to_queue(self, url):
        uurl = url.utf8()
        if uurl not in self._seen and url._host in self._allowed_hosts:
            self._seen.add(uurl)
            self._queue.put(url)

    def _scrape_page(self, url):
        print "Scraping %s..." % url.utf8()
        req = self._scraper.get(url.utf8())
        parsed = etree.HTML(req.content)
        
        links = parsed.xpath("//a[@href]")
        for link in links:
            new_link = url.relative(link.attrib['href'])
            new_link._fragment = None
            self._add_to_queue(new_link.canonical())

    def _crawl_worker(self):
        while True:
            item = self._queue.get()
            try:
                self._scrape_page(item)
            except:
                traceback.print_tb()
            finally:
                self._queue.task_done()

    def crawl(self):
        for i in range(self._worker_count):
            self._workers.append(spawn(self._crawl_worker))
        self._queue.join()

if __name__ == "__main__":
    import sys
    s = Spider(sys.argv[1], sys.argv[1] + ".db")
    s.crawl()