# coding: utf-8
# from operator import itemgetter
import os.path
import sys
from pathlib import Path
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings


from vtimecore.models import Record, User


def parse_sheet(path):
    with open(path) as f:
        content = [x.strip() for x in f.readlines()
                   if not x.strip().startswith('#')]

    # 2014-06-04,11:30,13:20,rnd-ui,RT:276445,"Initial training"
    for line in content:
        if line.count(',') < 5:
            continue

        date, start, end, queue, rt, comment = line.split(',', 5)
        start_date = datetime.strptime('{} {}'.format(date, start),
                                       '%Y-%m-%d %H:%M')
        end_date = datetime.strptime('{} {}'.format(date, end),
                                     '%Y-%m-%d %H:%M')
        ticket = int(rt.split(':')[-1])
        comment = comment.strip("'").strip('"')

        yield ticket, start_date, end_date, comment


def parse_timesheets(*args):
    if args[0]:
        directory = args[0][0]
    else:
        directory = settings.SHEETS_DIR
    files = sorted(str(f) for f in Path(directory).iterdir()
                   if f.is_file() and not f.parts[-1].startswith('.'))

    for path in files:
        username = os.path.split(path)[-1]
        if args[0]:
            print('processing ' + username)
        mtime = datetime.fromtimestamp(os.path.getmtime(path))

        user, created = User.objects.get_or_create(
            username=username, defaults={'file_modified': mtime})

        if created or user.file_modified != mtime:
            user.file_modified = mtime
            user.save()

            records = []
            for ticket, start_date, end_date, comment in parse_sheet(path):
                rec = Record(
                    username=username,
                    start_date=start_date,
                    end_date=end_date,
                    ticket=ticket,
                    comment=comment
                )
                records.append(rec)

            Record.objects.bulk_create(records)


class Command(BaseCommand):
    def handle(self, *args, **options):
        parse_timesheets(args)
