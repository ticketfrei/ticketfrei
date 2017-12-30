#!/usr/bin/env python3

import os
import datetime

class Log(object):

    def __init__(self, logpath):

        # initialize logging
        if logpath:
            self.logpath = logpath
        else:
            self.logpath = os.path.join("logs", str(datetime.datetime.now()))
        print("Path of logfile: " + self.logpath)

    def log(self, message):
        """
        Writing an error message & sometimes a traceback to a logfile in logs/
        and prints it.

        :param message: (string) Log message to be displayed
        """
        time = str(datetime.datetime.now())
        line = "[" + time + "] " + message + "\n"
        with open(self.logpath, 'a') as f:
            try:
                f.write(line)
            except UnicodeEncodeError:
                self.log("Failed to save log message due to UTF-8 error. ")
        print(line, end="")

