from __future__ import unicode_literals

from datetime import timedelta
from dateutil import parser

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.utils.timezone import now

from ...settings import import_from_string
from ...settings import money_rates_settings


class Command(BaseCommand):
    args = '<date_from or "yesterday"> <date_to> <backend_path>'
    help = 'Update rates for configured source'

    def handle(self, *args, **options):
        date_from = date_to = now().date()
        backend_class = money_rates_settings.DEFAULT_BACKEND
        if args:
            # special case for cron to always update average course for previous day
            if len(args) == 1 and args[0] == "yesterday":
                date_from = date_to = now().date() - timedelta(days=1)
            else:
                if len(args) >= 1:
                    try:
                        date_from = parser.parse(args[0]).date()
                    except ValueError:
                        raise CommandError("Cannot parse %s. Unrecognized date format." % args[0])
                if len(args) >= 2:
                    try:
                        date_to = parser.parse(args[1]).date()
                    except ValueError:
                        raise CommandError("Cannot parse %s. Unrecognized date format." % args[1])

                if len(args) >= 3:
                    try:
                        backend_class = import_from_string(args[2], "")
                    except ImportError:
                        raise CommandError("Cannot find custom backend %s. Is it correct?" % args[2])

        try:
            backend = backend_class()
            while date_from <= date_to:
                backend.update_rates(date_from)
                date_from += timedelta(days=1)
        except Exception as e:
            raise CommandError("Error during rate update: %s" % e)

        self.stdout.write('Successfully updated rates for "%s"' % backend_class)
