import logging
import subprocess
import time


async def smi():
    i = 0
    while i < 50:
        i = i + 1
        logging.info(subprocess.call(["nvidia-smi"]))
        time.sleep(0.1)
