from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from wiki.models import *
from wiki.utils.scraper import updateRanking, scrapeEventsYear


class Command(BaseCommand):
    help = "Updates databases by scraping fmbworldtour website"

    def handle(self, *args, **options):
        scrapeEventsYear(year=datetime.now().year)
        updateRanking()
        data = AppData.objects.get(id=1)
        data.lastUpdate = datetime.now()
        data.save()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated data')
        )
