import datetime
import logging
import os
import shutil
import sys
import time
from logging.handlers import TimedRotatingFileHandler


class CustomFormatter(logging.Formatter):
    grey = "\x1b[37m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    green = "\x1b[1;32m"
    blue = "\x1b[1;34m"
    light_blue = "\x1b[1;36m"
    purple = "\x1b[1;35m"

    frmt = f'%(asctime)s:' \
           f'#T' \
           f'[#lvlshort]:' \
           f'[%(filename)s:%(lineno)s:%(funcName)s()] %(message)s'

    frmt_info = f'{green}%(asctime)s:{reset}' \
                f'[#lvlshort]:' \
                f'{light_blue}[%(filename)s:%(lineno)s:%(funcName)s()]{reset} %(message)s'
    FORMATS = {
        logging.DEBUG: grey + frmt + reset,
        logging.INFO: frmt_info,
        logging.WARNING: yellow + frmt + reset,
        logging.ERROR: red + frmt + reset,
        logging.CRITICAL: bold_red + frmt + reset
    }

    def __init__(self, use_color: bool):
        super().__init__()
        self.use_color = use_color

    def format(self, record):
        log_fmt: str = self.FORMATS.get(record.levelno) if self.use_color else self.frmt
        s = log_fmt.replace('#lvlshort', f'{record.levelname[:3]}')
        formatter = logging.Formatter(s)
        return formatter.format(record)


class NoPingFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        a = "Response for getUpdates: [200] \"'{\"ok\":true,\"result\":[]}'\""
        b = "Make request: \"getUpdates\" with data: \"{'timeout': 60}\" and files \"None\""
        # print(a != msg, b != msg, sep='\n')
        return a != msg and b != msg


class NewTimedRotatingFileHandler(TimedRotatingFileHandler):

    def __init__(self, filename, **kws):
        TimedRotatingFileHandler.__init__(self, filename, **kws)

    def do_archive(self, current_file, new_file):
        print('<[::archiving log::]>')
        path_ = 'log_archive'
        nf = fr'{make_if_not_exists(path_)}\{os.path.split(new_file)[1]}'
        print(current_file, nf)
        shutil.copy(current_file, nf)
        os.remove(current_file)

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        dfn = self.rotation_filename(self.baseFilename[:-4] + "_" +
                                     time.strftime(self.suffix, timeTuple) + ".log")
        if os.path.exists(dfn):
            os.remove(dfn)
        self.do_archive(self.baseFilename, dfn)
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.stream = self._open()
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt


cnt_logger = logging.getLogger()
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
sf = CustomFormatter(use_color=True)
sh.setFormatter(sf)
# sh.addFilter(NoPingFilter())
cnt_logger.addHandler(sh)

fh = NewTimedRotatingFileHandler(filename=f'cnt_logs.log', when='S', interval=10, encoding='utf-8')
fh.setLevel(logging.DEBUG)
ff = CustomFormatter(use_color=False)

fh.setFormatter(ff)
# fh.addFilter(NoPingFilter())
cnt_logger.addHandler(fh)
cnt_logger.setLevel(logging.DEBUG)


def archive_logs():
    print('<[::archiving log::]>')
    path_ = 'log_archive'
    new_log = f'{make_if_not_exists(path_)}/cnt_logs_STOPED_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'
    shutil.copy('../cnt_logs.log', new_log)


def make_if_not_exists(folder_name):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    return fr'{os.getcwd()}\{folder_name}'
