from datetime import datetime
import shutil

from django.core.management.base import BaseCommand, CommandError
from wiki.models import *
from wiki.utils.scraper import updateRanking, scrapeEventsYear


class Command(BaseCommand):
    help = "Updates databases by scraping fmbworldtour website"

    def handle(self, *args, **options):
        shutil.copy2('wiki/static/wiki/db.sqlite3', 'wiki/static/wiki/backup.sqlite3')
        scrapeEventsYear(year=datetime.now().year)
        updateRanking()
        data = AppData.objects.get(id=1)
        data.lastUpdate = datetime.now()
        data.save()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated data')
        )
