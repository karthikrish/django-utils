#!/usr/bin/env python
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler
from optparse import OptionParser

if __name__ == '__main__':
    if not 'DJANGO_SETTINGS_MODULE' in os.environ:
        print 'DJANGO_SETTINGS_MODULE environment variable not set, exiting'
        sys.exit(2)

# avoid importing these if the environment variable is not set
from djutils.daemon import Daemon
from djutils.queue import autodiscover
from djutils.queue.exceptions import QueueException
from djutils.queue.queue import invoker, queue_name


class QueueDaemon(Daemon):
    """
    Queue consumer that runs as a daemon.  Example usage::
    
    To start the consumer (note you must export the settings module):
    
    # export PYTHONPATH=/path/to/code:$PYTHONPATH
    # export DJANGO_SETTINGS_MODULE=mysite.settings
    # python consumer.py start
    
    To stop the consumer:
    
    # python consumer.py stop
    """
    
    def __init__(self, options, *args, **kwargs):
        self.queue_name = queue_name
        
        self.pidfile = options.pidfile or '/var/run/djutils-%s.pid' % self.queue_name
        self.logfile = options.logfile or '/var/log/djutils-%s.log' % self.queue_name
        
        self.initialize_options(options)
        
        # Daemon class takes pidfile as first argument
        super(QueueDaemon, self).__init__(self.pidfile, *args, **kwargs)
    
    def initialize_options(self, options):
        self.default_delay = float(options.delay)
        self.max_delay = float(options.max_delay)
        self.backoff_factor = float(options.backoff)

        if self.backoff_factor < 1.0:
            raise Exception, 'backoff must be greater than or equal to 1'
        
        # initialize delay
        self.delay = self.default_delay
        
        self.logger = self.get_logger()
        self.logger.info('Initializing daemon with options:\npidfile: %s\nlogfile: %s\ndelay: %s\nbackoff: %s' % (
            self.pidfile, self.logfile, self.delay, self.backoff_factor))
    
    def get_logger(self):
        log = logging.getLogger('djutils.queue.logger')
        log.setLevel(logging.DEBUG)
        handler = RotatingFileHandler(self.logfile, maxBytes=1024*1024, backupCount=3)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(message)s"))
        log.addHandler(handler)
        return log
    
    def run(self):
        while True:
            self.process_message()
    
    def process_message(self):
        try:
            result = invoker.dequeue()
        except QueueException:
            # log error
            self.logger.warn('queue exception raised', exc_info=1)
            result = False
        except:
            self.logger.error('exception encountered, exiting', exc_info=1)
            raise
        
        if result:
            self.logger.info('Processed: %s' % result)
            self.delay = self.default_delay
        else:
            if self.delay > self.max_delay:
                self.delay = self.max_delay
            
            self.logger.info('No messages, sleeping for: %s' % self.delay)
            
            time.sleep(self.delay)
            self.delay *= self.backoff_factor


if __name__ == '__main__':    
    parser = OptionParser(usage='%prog [options]')
    parser.add_option('--delay', '-d', dest='delay', default=0.1,
        help='Default interval between invoking, in seconds - default = 0.1')
    parser.add_option('--backoff', '-b', dest='backoff', default=1.15,
        help='Backoff factor when no message found - default = 1.15')
    parser.add_option('--max', '-m', dest='max_delay', default=60,
            help='Maximum time to wait, in seconds - default = 60')
    parser.add_option('--pidfile', '-p', dest='pidfile', default='',
            help='Destination for pid file')
    parser.add_option('--logfile', '-l', dest='logfile', default='',
            help='Destination for log file')
    
    (options, args) = parser.parse_args()
    
    if not args:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
    
    # load up all commands.py modules in the installed apps
    autodiscover()
    
    daemon = QueueDaemon(options)
    daemon.run_simple(args[0])
