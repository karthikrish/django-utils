import logging
import time
import threading

from django.contrib.auth.models import User

from djutils.queue.bin.consumer import QueueDaemon
from djutils.queue.decorators import queue_command
from djutils.queue.queue import QueueCommand, QueueException, invoker
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
