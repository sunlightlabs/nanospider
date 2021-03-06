if __name__ == "__main__":
    import sys

    if '-g' in sys.argv:
        from ghost_spider import GhostSpider as Spider
    else:
        from gevent import monkey
        monkey.patch_all()
        from spider import Spider

    s = Spider(sys.argv[1], sys.argv[1] + ".db", workers=4, retry_attempts=2)
    s.crawl()
