Django ReDo
=============

Easy use!

**Django Pepper** is a very lightweight django library which allows to easily add asynchronous
tasks execution functionality. Library requires configured Redis server.


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
    
Django Pepper completely compatible with the **@staticmethods** and **functions**. It's
useful, when you need to group some async tasks into class.