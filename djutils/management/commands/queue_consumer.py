import os
import time
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from djutils.queue import autodiscover, Invoker, QueueException, QUEUE_NAME

LOCK_DIR = getattr(settings, 'QUEUE_LOCK_DIR', '/var/lock/')


# load all command classes into the Invoker's registry
autodiscover()

class Command(BaseCommand):
    help = "Consume queue messages."

    option_list = BaseCommand.option_list + (
        make_option('--delay', '-d', dest='delay', default=0.1,
            help='Default interval between invoking, in seconds - default = 0.1'),
        make_option('--queue', '-q', dest='queue_name', default=QUEUE_NAME,
            help='The name of the queue to read messages from.'),
        make_option('--backoff', '-b', dest='backoff', default=1.15,
            help='Backoff factor when no message found - default = 1.15'),
        make_option('--max', '-m', dest='max_delay', default=60,
            help='Maximum time to wait, in seconds - default = 60'),
        )

    @property
    def lock_filename(self):
        return os.path.join(LOCK_DIR, self.queue_name)

    def acquire_lock(self):
        if os.path.exists(self.lock_filename):
            return False
        fh = open(self.lock_filename, 'w')
        fh.close()
        return True

    def release_lock(self):
        if os.path.exists(self.lock_filename):
            os.remove(self.lock_filename)
            return True
        return False
    
    def initialize_options(self, options):
        self.queue_name = options.get('queue_name')
        self.default_delay = float(options.get('delay'))
        self.max_delay = float(options.get('max_delay'))
        self.backoff_factor = float(options.get('backoff'))

        if self.backoff_factor < 1.0:
            raise CommandError, 'backoff must be greater than or equal to 1'
        
        # initialize delay
        self.delay = self.default_delay

    def run_loop(self, invoker):
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

    def handle(self, *args, **options):
        self.initialize_options(options)

        if not self.acquire_lock():
            raise CommandError, 'lock file %s found, exiting' % self.lock_filename

        invoker = Invoker(queue_name=self.queue_name)
        try:
            self.run_loop(invoker)
        finally:
            if not self.release_lock():
                raise CommandError, 'unable to release lock file %s' % self.lock_filename
