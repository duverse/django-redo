Django ReDo
=============

Easy use!

**Django ReDo** is a very lightweight django library which allows to easily add asynchronous
tasks execution functionality. Library requires configured Redis server.


Installation
------------

    pip install Django-ReDo


**Usage**

    from django_redo import task
    
    # Registering new task
    @task.define()
    def some_async_function(hello):
        # some code...
        print(f'Hello {hello}')
    
    # This operation will schedule task to execute this function.
    some_async_function('world')
    
    # Or to run it directly without scheduling
    some_async_function.call('world')
    
Then we need to run worker, which will execute scheduled tasks.

    python manage.py redo
    
Django ReDo completely compatible with the **@staticmethods** and **functions**. It's
useful, when you need to group some async tasks into class.


**Configuring django**

Simply add django_redo to installed apps of your django project settings.

    INSTALLED_APPS = [
        ...
        'django_redo',
        ...
    ]
    
Then configure specific settings for django redo:


|OPTION|TYPE|DEFAULT|COMMENT|
|---|---|---|---|
|REDO_QUEUE_POLL|Float|0.05|Interval to poll redis tasks queue|
|REDO_QUEUE_THREADS|Int|1|How much queue worker threads should be registered|
|REDO_QUEUE_DBS|Dict|{}|*Redis server settings|

*Redis server settings can be specified in two ways:

**IPv Connection:**

    REDO_QUEUE_DBS = {
        "default": {
            "DB": 0,
            "PASSWORD": "******",
            "HOST": "127.0.0.1",
            "PORT": 6379,
            "THREADS": 1
        }
    }
    
**UNIX-Socket Connection:**

    REDO_QUEUE_DBS = {
        "default": {
            "DB": 0,
            "PASSWORD": "******",
            "USOCK": "/tmp/redis.sock",
            "THREADS": 1
        }
    }
    
Using different queues
----------------------

Django ReDo allows you to use as many queues as you want. To make it possible, you need
to configure few more queues at **REDO_QUEUE_DBS**.

**For example**

    REDO_QUEUE_DBS = {
        "fast": {
            "DB": 0,
            "PASSWORD": "******",
            "USOCK": "/tmp/redis.sock",
            "THREADS": 1
        },
        "long": {
            "DB": 1,
            "PASSWORD": "******",
            "USOCK": "/tmp/redis.sock",
            "THREADS": 2
        },
        "default": {
            "DB": 0,
            "PASSWORD": "******",
            "HOST": "127.0.0.1",
            "PORT": 6379,
            "THREADS": 1
        }
    }
    
As you understand, you need to run specific workers for each queue.

    python manage.py redo --thread 1 --queue long
    python manage.py redo --thread 2 --queue long
    python manage.py redo --thread 1 --queue fast
    python manage.py redo --thread 1
    
Last row runs default queue worker. And to schedule any task to specific queue - 
simply provide it to **define** decorator:

    from django_redo import task
    
    # Registering new task to specific queue
    @task.define('long')
    def some_async_function(hello):
        # some code...
        print(f'Hello {hello}')
        
        
Multi-threads example
---------------------

If you have a lot of heavy tasks which will be scheduled and should be executed as parallel
as it's possible - you just need to update **THREADS** option for your specific redis database
and run same number of workers.

    REDO_QUEUE_DBS = {
        "default": {
            "DB": 0,
            "PASSWORD": "******",
            "HOST": "127.0.0.1",
            "PORT": 6379,
            "THREADS": 4
        }
    }

And 4 workers for the 4 threads:

    python manage.py redo --thread 1 --queue default
    python manage.py redo --thread 2 --queue default
    python manage.py redo --thread 3 --queue default
    python manage.py redo --thread 4 --queue default
    
    
Making simpler with the supervisor
--------------------------------------

You can manage workers using supervisor tool. It's an easy way to add it to a system
startup and get a really useful managing tool. Here is an example of configuration
for 10 threads:


**/etc/supervisor/conf.d/redo.conf**

    [program:queue_worker]
    numprocs = 10
    numprocs_start = 1
    process_name = redo_worker_%(process_num)s
    command=/project/.env/bin/python /project/manage.py redo --thread %(process_num)s --queue default
    autostart=true
    autorestart=true
    user=www-data
    stdout_logfile=/project/redo.worker.log
    stderr_logfile=/project/redo.worker.err.log