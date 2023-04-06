# global utils non-business logic functions, e.g. response normalization, data enrichment, etc.
import os
import time
from logging.handlers import TimedRotatingFileHandler
import traceback
import asyncio
from types import CoroutineType


class SafeRotatingFileHandler(TimedRotatingFileHandler):
    # 참고 : https://ko.n4zc.com/article/programming/python/hr8m47f3.html
    def __init__(self, filename: str, when="h", interval=1, backup_count=0, encoding=None, delay=False, utc=False):
        log_dir = "/".join(filename.split("/")[:-1])
        if not os.path.exists(log_dir):
            try:
                os.mkdir(log_dir)
            except Exception:
                print(traceback.format_exc())
        TimedRotatingFileHandler.__init__(self, filename, when, interval, backup_count, encoding, delay, utc)

    """
    Override doRollover
    lines commanded by "##" is changed by cc
    """

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens. However, you want the file to be named for the
        start of the interval, not the current time. If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
            Override,  1. if dfn not exist then do rename
                2. _open with "a" model
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        current_time = int(time.time())
        dst_now = time.localtime(current_time)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            time_tuple = time.gmtime(t)
        else:
            time_tuple = time.localtime(t)
            dst_then = time_tuple[-1]
            if dst_now != dst_then:
                if dst_now:
                    addend = 3600
                else:
                    addend = -3600
                time_tuple = time.localtime(t + addend)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, time_tuple)
        # if os.path.exists(dfn):
        #     os.remove(dfn)

        # Issue 18940: A file may not have been created if delay is True.
        # if os.path.exists(self.baseFilename):
        if not os.path.exists(dfn) and os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, dfn)
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.mode = "a"
            self.stream = self._open()
        new_rollover_at = self.computeRollover(current_time)
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == "MIDNIGHT" or self.when.startswith("W")) and not self.utc:
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if dst_now != dst_at_rollover:
                if not dst_now:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                new_rollover_at += addend
        self.rolloverAt = new_rollover_at


_is_pending_ = True
graceful_shutdown_task_names = set()


def create_async_task(coro: CoroutineType, is_graceful_shutdown: bool, name: str = None):
    ta = asyncio.create_task(coro, name=name)
    if is_graceful_shutdown == True:
        graceful_shutdown_task_names.add(ta.get_name())


async def graceful_shutdown():
    global _is_pending_
    _is_pending_ = False

    for ta in asyncio.all_tasks():
        if ta.get_name() in graceful_shutdown_task_names:
            while not ta.done():
                await asyncio.sleep(0.5)

    await asyncio.sleep(5)


def is_pending():
    return _is_pending_
