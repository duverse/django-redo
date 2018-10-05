# -*- coding: utf-8 -*-
import time
import json
import redis
import importlib

from django_redo.settings import Settings


class Task(object):
    """
    Task representation
    """
    def __init__(self, fn, *args, **kwargs):
        """
        Initialize task
        :param fn:
        :param args:
        :param kwargs:
        """
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        """
        :return str:
        """
        fn = self.serialize_function(self.fn)
        return '{}{}{}(*{}, **{})'.format(
            fn['m'],
            '.'.join([''] + fn['n']) if fn['n'] else '',
            '.' + fn['f'],
            self.args,
            self.kwargs
        )

    def __repr__(self):
        """
        :return str:
        """
        return str(self)

    def __call__(self, *args, **kwargs):
        """
        Call function
        :return any:
        """
        return self.fn(*(args or self.args), **(kwargs or self.kwargs))

    def serialize(self):
        """
        Serialize task to an json object
        :return str:
        """
        return json.dumps({
            'f': self.serialize_function(self.fn),
            'a': self.args,
            'k': self.kwargs
        })

    @classmethod
    def load(cls, task):
        """
        Loads task from serialized value
        :param task:
        :return Task:
        """
        task = json.loads(task)
        return Task(cls.load_function(task['f']), *task['a'], **task['k'])

    @classmethod
    def load_function(cls, data):
        """
        Returns function that is ready to be called
        :param dict data:
        :return callable:
        """
        mdl = importlib.import_module(data['m'])
        ns = mdl
        while data['n']:
            ns = getattr(ns, data['n'].pop())
        fn = getattr(ns, data['f'])
        if isinstance(fn, Decorator):
            fn = fn.fn
        return fn

    @classmethod
    def serialize_function(cls, fn):
        """
        Returns serialized function object
        :param callable fn:
        :return dict:
        """
        ns = []
        mdl = fn.__module__
        name = fn.__name__

        if '.' in fn.__qualname__:
            ns = fn.__qualname__.split('.')[:-1]
        return {
            'f': name,
            'm': mdl,
            'n': ns
        }


class RedisQueue(object):
    """
    Queue task manager
    """
    __cache__ = {}

    def __init__(self, channel, conf):
        """
        Redis queue
        :param channel:
        :param conf:
        """
        self._database = conf
        self._channel_name = channel
        self._pubsub = None
        self._thread = 1
        self._last_thread = None

        self.redis = self._redis_connect(conf)

    def __call__(self, thread):
        """
        Enable specific thread
        :param thread:
        :return:
        """
        if 1 > thread > int(self._database.get('THREADS', 1)):
            raise ValueError('Invalid number of thread were provided.')
        self._thread = thread
        return self

    def __enter__(self):
        """
        Creates pubsub connection
        :return:
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Closes pubsub connection
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        if self._pubsub is not None:
            try:
                self._pubsub.close()
            except Exception as e:
                self._pubsub = None

    def __iter__(self):
        """
        Iterates queue
        :return:
        """
        with self:
            self.pubsub.subscribe(self._channel_name + ':{}'.format(self._thread))
            try:
                while True:
                    msg = self.pubsub.get_message()
                    if msg is None:
                        time.sleep(Settings.get('QUEUE_POLL', 0.05))
                        continue

                    if msg['type'] != 'message':
                        time.sleep(Settings.get('QUEUE_POLL', 0.05))
                        continue

                    try:
                        yield Task.load(msg['data'])
                    except Exception as e:
                        yield e

            except Exception as e:
                self.pubsub.unsubscribe()
                raise e

    @property
    def pubsub(self):
        """
        Returns pubsub singleton
        :return:
        """
        if not self._pubsub:
            self._pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        return self._pubsub

    @property
    def next_thread(self):
        """
        Returns next thread to publish
        :return:
        """
        ths = int(self._database.get('THREADS', 1))
        if ths == 1:
            return 1
        if self._last_thread is None:
            self._last_thread = 1
            return self._last_thread
        if ths > self._last_thread:
            self._last_thread += 1
        elif ths == self._last_thread:
            self._last_thread = 1
        return self._last_thread

    def schedule(self, task):
        """
        Queues task
        :param Task task:
        :return Task:
        """
        self.redis.publish('{}:{}'.format(self._channel_name, self.next_thread), task.serialize())
        return task

    def _proxy_task(self, message, callback):
        """
        Process task
        :param message:
        :param callback:
        :return:
        """

    @classmethod
    def _redis_connect(cls, conf):
        """
        Creates connection to redis
        :param conf:
        :return:
        """
        if 'unix_socket_path' in conf:
            return redis.Redis(
                db=conf.get('DB', 0),
                password=conf.get('PASSWORD'),
                unix_socket_path=conf['USOCK']
            )
        return redis.Redis(
            db=conf.get('DB', 0),
            host=conf.get('HOST', '127.0.0.1'),
            port=conf.get('PORT', 6379),
            password=conf.get('PASSWORD')
        )

    @classmethod
    def get_instance(cls, name='default', thread=1):
        """
        Returns singleton instance
        :param name:
        :param thread:
        :return RedisQueue:
        """
        if name not in Settings.get('QUEUE_DBS', {}):
            raise KeyError('Invalid queue provided "{}"'.format(name))

        if name not in cls.__cache__:
            cls.__cache__[name] = RedisQueue(name, Settings.get('QUEUE_DBS')[name])
        return cls.__cache__[name](thread)


class Decorator(object):
    def __init__(self, fn, _queue='default', *args, **kwargs):
        self.queue = RedisQueue.get_instance(_queue)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        self.args = (args or self.args)
        self.kwargs = (kwargs or self.kwargs)
        self.queue.schedule(self.task)
        return self

    @property
    def task(self):
        return Task(self.fn, *self.args, **self.kwargs)

    def call(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


def define(q='default'):
    def options(fn):
        def _wrap(*args, **kwargs):
            return Decorator(fn, q, *args, **kwargs)
        return _wrap()
    return options
