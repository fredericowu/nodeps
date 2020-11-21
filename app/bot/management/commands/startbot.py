from django.core.management.base import BaseCommand, CommandError
from bot.connector.telegrambot import TelegramBot


class Command(BaseCommand):
    help = 'Start BOT'

    """
    def add_arguments(self, parser):
        parser.add_argument('poll_ids', nargs='+', type=int)
    """

    def handle(self, *args, **options):
        print("Okay")
        TelegramBot()


