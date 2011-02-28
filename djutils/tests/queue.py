from django.contrib.auth.models import User
from django.test import TestCase

from djutils.queue import Invoker, QueueCommand, QueueException, queue_command


class UserCommand(QueueCommand):
    def execute(self):
        receiver, old_email, new_email = self.data
        receiver.email = new_email
        receiver.save()

    def undo(self):
        receiver, old_email, new_email = self.data
        receiver.email = old_email
        receiver.save()


@queue_command
def user_command(receiver, data):
    receiver.email = data
    receiver.save()


class SimpleTest(TestCase):
    def setUp(self):
        self.dummy = User.objects.create_user('username', 'user@example.com', 'password')
        self.invoker = Invoker()
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
        self.dummy = User.objects.get(username='username')
        self.assertEqual(self.dummy.email, 'nobody@example.com')

        # check the stack - should now show 1 item having been executed
        self.assertEqual(len(invoker._stack), 1)

    def test_decorated_function(self):
        invoker = self.invoker

        user_command(self.dummy, 'decor@ted.com')
        self.assertEqual(len(invoker.queue), 1)

        # the user's email address hasn't changed yet
        self.assertEqual(self.dummy.email, 'user@example.com')

        # dequeue
        invoker.dequeue()

        # make sure that the command was executed
        self.dummy = User.objects.get(username='username')
        self.assertEqual(self.dummy.email, 'decor@ted.com')
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

        dummy = User.objects.get(pk=self.dummy.pk)
        self.assertEqual(dummy.email, 'modified_once@none.com')

        command.set_data((self.dummy, dummy.email, 'modified_twice@none.com'))

        invoker.enqueue(command)
        invoker.dequeue()

        dummy = User.objects.get(pk=self.dummy.pk)
        self.assertEqual(dummy.email, 'modified_twice@none.com')

        invoker.undo()
        
        dummy = User.objects.get(pk=self.dummy.pk)
        self.assertEqual(dummy.email, 'modified_once@none.com')

        invoker.undo()
        
        dummy = User.objects.get(pk=self.dummy.pk)
        self.assertEqual(dummy.email, 'user@example.com')

        self.assertRaises(QueueException, invoker.undo)
