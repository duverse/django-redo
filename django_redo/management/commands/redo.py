from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django_redo.task import RedisQueue


class Command(BaseCommand):
    help = 'Executes queued django_redo tasks'

    def add_arguments(self, parser):
        parser.add_argument('thread', type=int, default=1)
        parser.add_argument('queue', nargs='?', type=str, default='default')

    def handle(self, *args, **options):
        channel = options.get('queue')
        thread = options.get('thread')
        with RedisQueue.get_instance(channel, thread) as q:
            self.stdout.write('='*80)
            self.stdout.write('  Listening tasks on {}:TH:{}...'.format(channel, thread))
            for task in q:
                if settings.DEBUG:
                    self.stdout.write('[TASK] {}'.format(task))
                if isinstance(task, Exception):
                    self.stdout.write(self.style.ERROR(' >> {}'.format(task)))
                    continue

                try:
                    result = task()
                    if settings.DEBUG:
                        self.stdout.write(self.style.SUCCESS(' >> {}'.format(str(result))))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(' >> {}'.format(e)))
