#!/usr/bin/env python
import sys
import time
from optparse import OptionParser

from djutils.daemon import Daemon
from djutils.queue.queue import invoker, queue_name


class QueueDaemon(Daemon):
    def __init__(self, options, *args, **kwargs):
        pidfile = options.pidfile or '/var/run/djutils-%s.pid' % queue_name
        self.initialize_options(options)
        super(QueueDaemon, self).__init__(pidfile, *args, **kwargs)
    
    def initialize_options(self, options):
        self.default_delay = float(options.delay)
        self.max_delay = float(options.max_delay)
        self.backoff_factor = float(options.backoff)

        if self.backoff_factor < 1.0:
            raise Exception, 'backoff must be greater than or equal to 1'
        
        # initialize delay
        self.delay = self.default_delay
    
    def run(self):
        while True:
            try:
                result = invoker.dequeue()
            except QueueException:
                # log error
                result = False
            
            if result:
                self.delay = self.default_delay
            else:
                time.sleep(self.delay)
                if self.delay < self.max_delay:
                    self.delay *= self.backoff_factor
                else:
                    self.delay = self.default_delay


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
    
    (options, args) = parser.parse_args()
    
    if not args:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
    
    daemon = QueueDaemon(options)
    daemon.run_simple(args[0])
