import time

from django.contrib.auth.models import User

from djutils.queue import Invoker, QueueCommand, QueueException, queue_command
from djutils.test import TestCase


class UserCommand(QueueCommand):
    def execute(self):
        user, old_email, new_email = self.data
        user.email = new_email
        user.save()

    def undo(self):
        user, old_email, new_email = self.data
        user.email = old_email
        user.save()


@queue_command(queue_name='test-queue')
def user_command(user, data):
    user.email = data
    user.save()

@queue_command
def user_command_no_args(user, data):
    user.email = data
    user.save()


class QueueTest(TestCase):
    def setUp(self):
        self.dummy = User.objects.create_user('username', 'user@example.com', 'password')
        self.invoker = Invoker(queue_name='test-queue')
        self.invoker.flush()
        self.invoker._stack = []

    def test_basic_processing(self):
        # reference locally for clarity
        invoker = self.invoker
        
        # make sure UserCommand got registered
        self.assertTrue(str(UserCommand) in invoker)
        self.assertEqual(invoker._registry[str(UserCommand)], UserCommand)

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

        # check the stack - should now show 1 item having been executed
        self.assertEqual(len(invoker._stack), 1)

    def test_decorated_function(self):
        invoker = self.invoker

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
    
    def test_decorator_no_args(self):
        invoker = user_command_no_args.invoker
        
        user_command_no_args(self.dummy, 'no@args.com')
        self.assertEqual(len(invoker.queue), 1)
        
        # the user's email address hasn't changed yet
        dummy = User.objects.get(username='username')
        self.assertEqual(dummy.email, 'user@example.com')

        # dequeue
        invoker.dequeue()

        # make sure that the command was executed
        dummy = User.objects.get(username='username')
        self.assertEqual(dummy.email, 'no@args.com')
        self.assertEqual(len(invoker.queue), 0)

    def test_stack(self):
        invoker = self.invoker

        # queue up commands, which should be bigger than the invoker's stack size
        size = invoker.stack_size + 10
        stack_size = invoker.stack_size

        # queue them all up
        for x in xrange(1, size):
            command = UserCommand((self.dummy, self.dummy.email, 'email%s@example.com' % x))

            invoker.enqueue(command)

            self.assertEqual(len(invoker.queue), x)

        # dequeue them all, checking to see that the stack correctly reflects
        # the most recently executed commands
        for x in xrange(1, size):
            invoker.dequeue()
            tmp_dummy = User.objects.get(username='username')
            self.assertEqual(tmp_dummy.email, 'email%s@example.com' % x)

            if x < stack_size:
                self.assertEqual(len(invoker._stack), x)
            else:
                self.assertEqual(len(invoker._stack), stack_size)
                stored_email = 'email%s@example.com' % x
                self.assertTrue(stored_email in invoker._stack[stack_size - 1])

    def test_undo(self):
        invoker = self.invoker

        command = UserCommand((self.dummy, self.dummy.email, 'modified_once@none.com'))

        invoker.enqueue(command)
        invoker.dequeue()

        dummy = User.objects.get(username='username')
        self.assertEqual(dummy.email, 'modified_once@none.com')

        command.set_data((self.dummy, dummy.email, 'modified_twice@none.com'))

        invoker.enqueue(command)
        invoker.dequeue()

        dummy = User.objects.get(username='username')
        self.assertEqual(dummy.email, 'modified_twice@none.com')

        invoker.undo()
        
        dummy = User.objects.get(username='username')
        self.assertEqual(dummy.email, 'modified_once@none.com')

        invoker.undo()
        
        dummy = User.objects.get(username='username')
        self.assertEqual(dummy.email, 'user@example.com')

        self.assertRaises(QueueException, invoker.undo)
