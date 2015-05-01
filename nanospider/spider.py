from gevent import monkey, queue, pool, spawn
monkey.patch_all()

import requests, traceback, sqlite3, itertools
import url as moz_url
from lxml import etree

from scrapelib import Scraper
from scrapelib.cache import SQLiteCache

def is_html(response):
    return 'html' in response.headers.get('content-type', 'text/html').lower()

class SpiderScraper(Scraper):
    def __init__(self, cache_path, allowed_hosts=(), requests_per_minute=0, **kwargs):
        kwargs['requests_per_minute'] = requests_per_minute
        super(SpiderScraper, self).__init__(**kwargs)

        self.cache_storage = SQLiteCache(cache_path)
        self.cache_write_only = False
        self._allowed_hosts = set(allowed_hosts)

    def should_cache_response(self, response):
        return response.status_code == 200 and \
            moz_url.parse(response.url)._host in self._allowed_hosts and \
            is_html(response)

class Spider(object):
    def __init__(self, domain, cache_path, workers=2, try_sitemap=True, **kwargs):
        self.domain = domain
        self._queue = queue.JoinableQueue()
        self._workers = []
        self._worker_count = workers
        self._allowed_hosts = set()

        self._allowed_hosts.add(domain)

        self._scraper = SpiderScraper(cache_path, self._allowed_hosts, **kwargs)
        self._build_table()
        self._resume_queue()

        self._add_to_queue(moz_url.parse("http://%s/" % domain))

    def _build_table(self):
        self._scraper.cache_storage._conn.execute("""CREATE TABLE IF NOT EXISTS seen
                (key text UNIQUE, processed integer)""")

    def _add_to_queue(self, url):
        uurl = url.utf8()

        if url._host in self._allowed_hosts:
            # insert it into sqlite, or not
            try:
                with self._scraper.cache_storage._conn as conn:
                    conn.execute("INSERT INTO seen values (?, 0)", (uurl,))
                self._queue.put(url)
            except sqlite3.IntegrityError:
                # we've already seen this one
                pass

    def _resume_queue(self):
        # if there's already stuff in the database, repopulate from the queue
        for row in self._scraper.cache_storage._conn.execute("SELECT * FROM seen WHERE processed = 0"):
            self._queue.put(moz_url.parse(row[0]))

    def _scrape_page(self, url):
        uurl = url.utf8()

        print "Scraping %s..." % uurl
        response = self._scraper.get(uurl)

        if is_html(response):
            parsed = etree.HTML(response.content)

            links = parsed.xpath("//a[@href]")
            for link in links:
                new_link = url.relative(link.attrib['href'])
                new_link._fragment = None
                self._add_to_queue(new_link.canonical())

        # mark this one as processed
        with self._scraper.cache_storage._conn as conn:
            conn.execute("UPDATE seen SET processed = 1 WHERE key = ?", (uurl,))

    def _crawl_worker(self):
        while True:
            item = self._queue.get()
            try:
                self._scrape_page(item)
            except:
                traceback.print_exc()
            finally:
                self._queue.task_done()

    def crawl(self):
        for i in range(self._worker_count):
            self._workers.append(spawn(self._crawl_worker))
        self._queue.join()

        # clean up workers
        for worker in self._workers:
            worker.kill()

        self._workers = []

    @property
    def urls(self):
        return itertools.imap(
            lambda r: r[0],
            self._scraper.cache_storage._conn.execute("SELECT key FROM cache WHERE status = 200")
        )

    # proxy the scraper's get for convenience
    def get(self, *args, **kwargs):
        return self._scraper.get(*args, **kwargs)

if __name__ == "__main__":
    import sys
    s = Spider(sys.argv[1], sys.argv[1] + ".db", workers=4)
    s.crawl()