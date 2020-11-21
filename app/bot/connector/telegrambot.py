from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import os
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot:
    updater = None
    bot = None
    token = None
    messages = []
    pool_size = 100
    chats = {}

    def __init__(self, token=None):
        if not self.token:
            if not TelegramBot.token:
                TelegramBot.token = token

            if not TelegramBot.token:
                TelegramBot.token = os.environ.get("TELEGRAM_TOKEN")

            self.token = TelegramBot.token

        if not self.token:
            raise Exception("Telegram Bot needs a token")

        if TelegramBot.updater is None:
            logger.info("Starting Telegram Bot")
            TelegramBot.updater = Updater(token=self.token)
            TelegramBot.bot = TelegramBot.updater.bot

            handlers = {
                CommandHandler: [
                    ('start', TelegramBot.start),
                ],
                MessageHandler: [
                    (Filters.text, TelegramBot.echo),
                    (Filters.text, TelegramBot.__received_message),
                ],
            }

            for handler_type in handlers:
                group = 0
                for handler in handlers[handler_type]:
                    handler_func = handler_type(*handler)
                    TelegramBot.updater.dispatcher.add_handler(handler_func, group)
                    group += 1

            TelegramBot.updater.start_polling()

        self.updater = TelegramBot.updater
        self.bot = TelegramBot.bot

    @classmethod
    def get_chat_id(cls, to):
        chat_id = None
        try:
            # check if it is an ID
            chat_id = str(int(to))
        except ValueError:
            to = to.replace("@", "")
            chats = cls.chats
            chat_ids = list(filter(lambda a: True if chats[a]['username'] == to else False, chats))
            if chat_ids:
                chat_id = chat_ids[0]

        return chat_id if chat_id else None

    @classmethod
    def send_message(cls, to, message):
        chat_id = cls.get_chat_id(to)
        if chat_id:
            cls.bot.send_message(chat_id=chat_id, text=message)
            cls.log_message("out", message, chat_id)
            result = True

        else:
            result = False

        return result

    def clean_messages(self, in_out=None):
        if in_out is None:
            self.__class__.messages = []
        else:
            self.__class__.messages = list(filter(lambda a: a[0] != in_out, self.__class__.messages))

    def get_messages(self, in_out=None):
        if in_out is None:
            messages = list(self.__class__.messages)
        else:
            messages = list(filter(lambda a: a[0] == in_out, self.__class__.messages))

        self.clean_messages(in_out)
        return messages

    @classmethod
    def start(cls, bot, update):
        msg = "Hi, to know about me go to https://github.com/fredericowu/nodeps"
        cls.send_message(bot.message.chat_id, msg)

    @classmethod
    def echo(cls, bot, update):
        msg = "You said: {0}".format(bot.message.text)
        cls.send_message(bot.message.chat_id, msg)

    @classmethod
    def __received_message(cls, bot, update):
        user = bot.message.from_user
        logger.info('You talk with user {} and his user ID: {} '.format(user['username'], user['id']))
        cls.chats[user['id']] = user
        cls.log_message("in", bot.message.text)

    @classmethod
    def log_message(cls, in_out, message, chat_id=None):
        # TODO Let's not waste memory until we get a database
        if len(cls.messages) >= cls.pool_size:
            cls.messages.pop(0)

        cls.messages.append([in_out, message, chat_id])



