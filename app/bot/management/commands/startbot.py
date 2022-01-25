from django.core.management.base import BaseCommand, CommandError
from bot.connector.telegrambot import TelegramBot
from requests.exceptions import ReadTimeout
import time


class Command(BaseCommand):
    help = 'Start BOT'

    """
    def add_arguments(self, parser):
        parser.add_argument('poll_ids', nargs='+', type=int)
    """

    def handle(self, *args, **options):
        print("Okay")

        while True:
            print("Starting Bot...")
            try:
                bot = TelegramBot()
                bot.loop()
            except ReadTimeout:
                print("Will reconnect...")
            time.sleep(5*60)


