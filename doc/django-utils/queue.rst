Queue
=====

A simple task queue and consumer to make processing tasks out-of-band painless.
Ideal for sending email, checking items for spam, generating thumbnails, etc.

The :mod:`Queue` module is divided up into several components, but for
almost all use-cases, you will only use the :func:`queue_command` decorator
found in :mod:`djutils.queue.decorators`


Executing tasks out-of-process
------------------------------

.. py:module:: djutils.queue.decorators

For the simple case, you need only write a function, decorate it with the
:func:`queue_command` decorator and call it as you normally would.  Instead
of executing immediately and potentially blocking, the function will be
enqueued and return immediately afterwards.

The :class:`QueueDaemon` consumer will pick it up and execute it in a separate
process::

    ### app/views.py ###
    from django.http import HttpResponse
    
    from djutils.queue.decorators import queue_command


    @queue_command
    def churn_data(model_instance, some_data, another_value):
        # this function will do some expensive processing, and so
        # should happen outside the request/response cycle.
        
        important_results = model_instance.process_data(some_value, another_value)
        model_instance.propogate_results(important_results)

    def data_processing_view(request, some_val, another_val):
        # assume we load up an object based on some parameter passed in
        # to the view.  also, the view gives us a payload of data.  we
        # want the object to churn that data in the background using the
        # function above:
        churn_data(my_object, request.POST['payload'], another_val)
        return HttpResponse('Churning in background task added to queue')


When the consumer picks up the message, it will churn your data!

.. warning:: You can pass anything in to the decorated function *as long as it is pickle-able*.

.. warning:: Your decorated functions must be loaded into memory by the consumer -
    to ensure that this happens it is good practice to put all :func:`queue_command`
    decorated functions in a module named :mod:`commands.py` so the autodiscovery
    bits will pick them up.


Autodiscovery
-------------

The :mod:`djutils.queue.registry` stores references to all :class:`QueueCommand`
classes (this includes any function decorated with :func:`queue_command`).  The
consumer needs to "discover" your commands in order to process them, so it is
recommended that you put all your code that needs to be processed via the Queue
in files named :mod:`commands.py`, much like django's admin processes files
named :mod:`admin.py`.

To manually discover commands, execute::

    >>> from djutils import queue; queue.autodiscover()


Consuming Messages
------------------

.. py:module:: djutils.queue.bin.consumer

The :mod:`djutils.queue.bin.consumer` module contains the daemon that will
consume your queue.  This is a "proper" linux daemon, and is based on the
python code found in `this blog post <http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/>`_.

To run the consumer, you will need to ensure that two environment variables
are properly set:

    * PYTHONPATH: a list of directories in which to find python packages
    * DJANGO_SETTINGS_MODULE: the location of the settings file your django project uses

Example assuming you use virtualenv::

    # assume your cwd is the root dir of virtualenv
    export DJANGO_SETTINGS_MODULE=mysite.settings
    ./bin/python ./src/djutils/djutils/queue/bin/consumer.py start -l ./logs/queue.log -p ./run/queue.pid
    
    -- stopping --
    
    ./bin/python ./src/djutils/djutils/queue/bin/consumer.py stop -l ./logs/queue.log -p ./run/queue.pid

Example running as root::

    sudo su
    export PYTHONPATH=/path/to/site/:/path/to/djutils/:$PYTHONPATH
    export DJANGO_SETTINGS_MODULE=mysite.settings
    python djutils/bin/consumer.py start
    
    -- stopping --
    
    python djutils/bin/consumer.py stop


Backends
--------

.. py:module:: djutils.queue.backends.base

Currently I've only written two backends, the :class:`djutils.queue.backends.database.DatabaseQueue`
which stores messages in the db using django's ORM and the `djutils.queue.backends.redis_backend.RedisQueue`
whish uses `redis <http://redis.io>`_ to store messages.  I plan on adding additional
backends, but if you'd like to write your own there are just a few methods that
need to be implemented.


    .. py:class:: class BaseQueue(object)
    
        .. py:method:: __init__(self, name, connection)

            Initialize the Queue - this happens once when the module is loaded
    
        .. py:method:: write(self, data)

            Push 'data' onto the queue
        
        .. py:method:: read(self)

            Pop data from the queue.  An empty queue should not raise an Exception!
        
        .. py:method:: flush(self)

            Delete everything from the queue
    
        .. py:method:: __len__(self)
        
            Number of items in the queue


.. py:module:: djutils.queue.backends.database

.. py:class:: class DatabaseQueue(BaseQueue)

    ::

        QUEUE_BACKEND = 'djutils.queue.backends.database.DatabaseQeueue'
        QUEUE_CONNECTION = '' # <-- no connection needed as it uses django's ORM

.. py:module:: djutils.queue.backends.redis_backend

.. py:class:: class RedisQueue(BaseQueue)

    ::

        QUEUE_BACKEND = 'djutils.queue.backends.redis_backend.RedisQueue'
        QUEUE_CONNECTION = '10.0.0.75:6379:0' # host, port, database-number
