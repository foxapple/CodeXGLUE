"""
:synopsis: Parent crawler module, which supervises all crawlers.

Contains functions for initializing all subsidiary, threaded crawlers.
"""

import logging
import logging.handlers
import os
import Queue
import sys
import time
from threading import Event

from .crawler import GitHubCrawler, BitbucketCrawler
from .indexer import GitIndexer, GitRepository

__all__ = ["crawl"]

MAX_URL_QUEUE_SIZE = 5e3

def crawl():
    """
    Initialize all crawlers (and indexers).

    Start the:
    1. GitHub crawler, :class:`crawler.GitHubCrawler`.
    2. Bitbucket crawler, :class:`crawler.BitbucketCrawler`.
    3. Git indexer, :class:`bitshift.crawler.indexer.GitIndexer`.
    """

    _configure_logging()
    time.sleep(5)

    repo_clone_queue = Queue.Queue(maxsize=MAX_URL_QUEUE_SIZE)
    run_event = Event()
    run_event.set()
    threads = [GitIndexer(repo_clone_queue, run_event)]

    if sys.argv[1:]:
        names = sys.argv[1:]
        ranks = GitHubCrawler.get_ranks(names)
        for name in names:
            repo = GitRepository("https://github.com/" + name, name, "GitHub",
                                 ranks[name])
            repo_clone_queue.put(repo)
    else:
        threads += [GitHubCrawler(repo_clone_queue, run_event),
                    BitbucketCrawler(repo_clone_queue, run_event)]

    for thread in threads:
        thread.start()

    try:
        while 1:
            time.sleep(0.1)
    except KeyboardInterrupt:
        run_event.clear()
        with repo_clone_queue.mutex:
            repo_clone_queue.queue.clear()
        for thread in threads:
            thread.join()

def _configure_logging():
    # This isn't ideal, since it means the bitshift python package must be kept
    # inside the app, but it works for now:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    log_dir = os.path.join(root, "logs")

    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    formatter = logging.Formatter(
            fmt=("%(asctime)s %(levelname)s %(name)s %(message)s"),
            datefmt="%y-%m-%d %H:%M:%S")

    file_handler = logging.handlers.TimedRotatingFileHandler(
            "%s/%s" % (log_dir, "app.log"), when="H", interval=1,
            backupCount=20)
    stream_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
    root_logger.setLevel(logging.NOTSET)

if __name__ == "__main__":
    crawl()
