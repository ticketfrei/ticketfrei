#!/usr/bin/env python3

import os
import datetime
import traceback
import sys
import sendmail


class Logger(object):
    """
    builds log files, writes the log messages.
    If a critical error occurs, handles the bugtracking and error
    messages.
    """

    def __init__(self, config):
        """
        logs everything & sends bugtracking messages.

        :param config: config file
        """
        self.config = config

        # initialize logging
        if config["logging"]["logpath"]:
            self.logpath = os.path.join(self.config["logging"]["logpath"], str(datetime.datetime.now()))
        else:
            self.logpath = os.path.join("logs", str(datetime.datetime.now()))
        print("Path of logfile: " + self.logpath)

        # intialize shutdown contact
        try:
            self.no_shutdown_contact = False
            self.contact = self.config['mail']['contact']
        except KeyError:
            self.no_shutdown_contact = True

    def log(self, message):
        """
        Writing an error message & sometimes a traceback to a logfile in logs/
        and prints it.

        :param message: (string) Logger message to be displayed
        """
        time = str(datetime.datetime.now())
        line = "[" + time + "] " + message + "\n"
        with open(self.logpath, 'a') as f:
            try:
                f.write(line)
            except UnicodeEncodeError:
                message = "Failed to save log message due to UTF-8 error. "
                message = message + self.generate_tb(sys.exc_info())
                self.log(message)
        print(line, end="")

    def generate_tb(self, exc):
        tb = traceback.extract_tb(exc[2])  # returns StackSummary object
        tb = "\n".join(tb.format())  # string of the actual traceback
        message = ("Traceback (most recent call last):\n",
                   tb,
                   exc[0].__name__)  # the type of the Exception
        message = "".join(message)  # concatenate to full traceback message
        return message

    def shutdown(self, tb):
        """ If something breaks, it shuts down the bot and messages the owner.

        :param tb: (string) traceback
        """
        logmessage = "Shit went wrong, closing down.\n" + tb + "\n\n"
        if self.no_shutdown_contact:
            self.log(logmessage)
            return
        logmessage = logmessage + "Sending message to " + self.contact
        self.log(logmessage)
        try:
            mailer = sendmail.Mailer(self.config)
            mailer.send(tb, self.contact, "Ticketfrei Crash Report")
        except:
            self.log("Error while shutdown: " + self.generate_tb(sys.exc_info()))
            print()
