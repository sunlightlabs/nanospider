from gevent import monkey, queue, pool, spawn
monkey.patch_all()

import requests, traceback, url
from lxml import etree

class Spider(object):
    def __init__(self, domain):
        self.domain = domain
        self._queue = queue.JoinableQueue()
        self._seen = set()
        self._workers = []
        self._allowed_hosts = set()

        self._allowed_hosts.add(domain)
        self._add_to_queue(url.parse("http://%s/" % domain))

    def _add_to_queue(self, url):
        uurl = url.utf8()
        if uurl not in self._seen and url._host in self._allowed_hosts:
            self._seen.add(uurl)
            self._queue.put(url)

    def _scrape_page(self, url):
        print "Scraping %s..." % url.utf8()
        req = requests.get(url.utf8())
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
        for i in range(2):
            self._workers.append(spawn(self._crawl_worker))
        self._queue.join()

if __name__ == "__main__":
    import sys
    s = Spider(sys.argv[1])
    s.crawl()