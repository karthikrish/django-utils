import datetime
import logging
import time

from django.contrib.auth.models import User

from djutils.queue.bin.consumer import QueueDaemon
from djutils.queue.decorators import crontab, queue_command, periodic_command
from djutils.queue.queue import QueueCommand, PeriodicQueueCommand, QueueException, invoker
from djutils.queue.registry import registry
from djutils.test import TestCase


class SilentQueueDaemon(QueueDaemon):
    def get_logger(self):
        return logging.getLogger('djutils.tests.queue.logger')


class UserCommand(QueueCommand):
    def execute(self):
        user, old_email, new_email = self.data
        user.email = new_email
        user.save()


@queue_command
def user_command(user, data):
    user.email = data
    user.save()


class QueueTest(TestCase):
    def setUp(self):
        self.dummy = User.objects.create_user('username', 'user@example.com', 'password')
        invoker.flush()

    def test_basic_processing(self):
 
        # make sure UserCommand got registered
        self.assertTrue(str(UserCommand) in registry)
        self.assertEqual(registry._registry[str(UserCommand)], UserCommand)

        # create a command
        command = UserCommand((self.dummy, self.dummy.email, 'nobody@example.com'))

        # enqueueing the command won't execute it - it just hangs out
        invoker.enqueue(command)

        # did the message get enqueued?
        self.assertEqual(len(invoker.queue), 1)

        # dequeueing loads from the queue, creates a command and executes it
        invoker.dequeue()

        # make sure the command's execute() method got called
        dummy = User.objects.get(username='username')
        self.assertEqual(dummy.email, 'nobody@example.com')

    def test_decorated_function(self):
        user_command(self.dummy, 'decor@ted.com')
        self.assertEqual(len(invoker.queue), 1)

        # the user's email address hasn't changed yet
        dummy = User.objects.get(username='username')
        self.assertEqual(dummy.email, 'user@example.com')

        # dequeue
        invoker.dequeue()

        # make sure that the command was executed
        dummy = User.objects.get(username='username')
        self.assertEqual(dummy.email, 'decor@ted.com')
        self.assertEqual(len(invoker.queue), 0)
    
    def test_daemon_run(self):
        class Options(dict):
            def __getattr__(self, name):
                return self[name]
        
        daemon = SilentQueueDaemon(Options(
            pidfile='',
            logfile='',
            delay=.1,
            backoff=2,
            max_delay=.4,
            no_periodic=False,
        ))
        
        start = time.time()
        daemon.process_message()
        end = time.time()
        
        self.assertTrue(.09 < end - start < .11)
        
        start = time.time()
        daemon.process_message()
        end = time.time()
        
        self.assertTrue(.19 < end - start < .21)
        
        user_command(self.dummy, 'decor@ted.com')
        
        dummy = User.objects.get(username='username')
        self.assertEqual(dummy.email, 'user@example.com')
        
        daemon.process_message()
        
        dummy = User.objects.get(username='username')
        self.assertEqual(dummy.email, 'decor@ted.com')
        
        self.assertEqual(daemon.delay, .1)
    
    def test_crontab_month(self):
        # validates the following months, 1, 4, 7, 8, 9
        valids = [1, 4, 7, 8, 9]
        validate_m = crontab(month='1,4,*/6,8-9')
        
        for x in xrange(1, 13):
            res = validate_m(datetime.datetime(2011, x, 1))
            self.assertEqual(res, x in valids)
    
    def test_crontab_day(self):
        # validates the following days
        valids = [1, 4, 7, 8, 9, 13, 19, 25, 31]
        validate_d = crontab(day='*/6,1,4,8-9')
        
        for x in xrange(1, 32):
            res = validate_d(datetime.datetime(2011, 1, x))
            self.assertEqual(res, x in valids)
    
    def test_crontab_hour(self):
        # validates the following hours
        valids = [0, 1, 4, 6, 8, 9, 12, 18]
        validate_h = crontab(hour='8-9,*/6,1,4')
        
        for x in xrange(24):
            res = validate_h(datetime.datetime(2011, 1, 1, x))
            self.assertEqual(res, x in valids)
    
    def test_crontab_minute(self):
        # validates the following minutes
        valids = [0, 1, 4, 6, 8, 9, 12, 18, 24, 30, 36, 42, 48, 54]
        validate_m = crontab(minute='4,8-9,*/6,1')
        
        for x in xrange(60):
            res = validate_m(datetime.datetime(2011, 1, 1, 1, x))
            self.assertEqual(res, x in valids)
    
    def test_crontab_day_of_week(self):
        # validates the following days of week
        # jan, 1, 2011 is a saturday
        valids = [2, 4, 9, 11, 16, 18, 23, 25, 30]
        validate_dow = crontab(day_of_week='0,2')
        
        for x in xrange(1, 32):
            res = validate_dow(datetime.datetime(2011, 1, x))
            self.assertEqual(res, x in valids)
    
    def test_crontab_all_together(self):
        # jan 1, 2011 is a saturday
        # may 1, 2011 is a sunday
        validate = crontab(
            month='1,5',
            day='1,4,7',
            day_of_week='0,6',
            hour='*/4',
            minute='1-5,10-15,50'
        )
        
        self.assertTrue(validate(datetime.datetime(2011, 5, 1, 4, 11)))
        self.assertTrue(validate(datetime.datetime(2011, 5, 7, 20, 50)))
        self.assertTrue(validate(datetime.datetime(2011, 1, 1, 0, 1)))
        
        # fails validation on month
        self.assertFalse(validate(datetime.datetime(2011, 6, 4, 4, 11)))
        
        # fails validation on day
        self.assertFalse(validate(datetime.datetime(2011, 1, 6, 4, 11)))
        
        # fails validation on day_of_week
        self.assertFalse(validate(datetime.datetime(2011, 1, 4, 4, 11)))
        
        # fails validation on hour
        self.assertFalse(validate(datetime.datetime(2011, 1, 1, 1, 11)))
        
        # fails validation on minute
        self.assertFalse(validate(datetime.datetime(2011, 1, 1, 4, 6)))
