from spider import Spider

from lxml import etree
import html5lib

import url as moz_url

import traceback, urlparse, threading, Queue

from multiprocessing import JoinableQueue, Event, Process

def is_html(response):
    if not response:
        return False
    return 'html' in response.headers.get('Content-Type', 'text/html').lower()

class GhostSpider(Spider):
    crawl_requires_gevent = False
    queue_class = JoinableQueue

    def _scrape_page(self, url, ghost):
        uurl = url.utf8()

        print "Scraping %s..." % uurl
        page, resources = ghost.open(uurl)
        ghost.wait_for_page_loaded()

        if is_html(page):
            parsed = html5lib.parse(str(page.content), treebuilder='lxml', namespaceHTMLElements=False)

            links = parsed.xpath("//a[@href]")
            for link in links:
                new_link = moz_url.parse(urlparse.urljoin(url.utf8(), link.attrib['href']))
                new_link._fragment = None
                new_link._userinfo = None
                self._add_to_queue(new_link.canonical())

        # mark this one as processed
        with self._scraper.cache_storage._conn as conn:
            conn.execute("UPDATE seen SET processed = 1 WHERE key = ?", (uurl,))

    def _crawl_worker(self):
        from ghost import Ghost
        ghost = Ghost()
        while True:
            item = self._queue.get()
            try:
                self._scrape_page(item, ghost)
            except:
                traceback.print_exc()
            finally:
                self._queue.task_done()

    def crawl(self):
        for i in range(self._worker_count):
            worker = Process(target=self._crawl_worker)
            self._workers.append(worker)
            worker.start()

        # initialize after spawn for the MP version because weird stuff seems to happen if we make any requests before spawning
        self._initialize_crawl()
        self._queue.join()

        # clean up workers
        for worker in self._workers:
            worker.terminate()

        self._workers = []
