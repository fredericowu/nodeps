#from telegram.ext import Updater
#from telegram.ext import CommandHandler
#from telegram.ext import MessageHandler, Filters
import os
import logging
import telebot
import time
from django.utils import timezone

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot:
    token = None
    connection = None

    #@classmethod
    #def send_message(cls, to, message):
    #    return cls.bot.send_message(to, message)

    def __init__(self, token=None):
        if not TelegramBot.token:
            TelegramBot.token = token

        if not TelegramBot.token:
            TelegramBot.token = os.environ.get("TELEGRAM_TOKEN")

        if not TelegramBot.token:
            raise Exception("Telegram Bot needs a token")

        connection = telebot.TeleBot(TelegramBot.token)
        TelegramBot.connection = connection

        # self.start_tcpserver()

        # import logging
        # telebot.logger.setLevel(logging.DEBUG)

        # def cleanup():
        #    print "Limpando Django_ChatAPI"
        #    self.zapuser.stop_running()

        # atexit.register(cleanup)

        @connection.message_handler(func=lambda message: True)
        def on_message_received(message):
            print("aqui")
            print(message)
            TelegramBot.connection.send_message(message.from_user.id, "you said: "+message.text)
            """
            from apps.whatsapp.models import Mensagem, Contato, Grupo, Midia

            chat_id = message.chat.id

            contato = Contato().get_or_add(message.from_user.id, self.zapuser, message.from_user.first_name,
                                           message.from_user.last_name)
            grupo = None
            # Reply to the message
            # self.bot.sendMessage(chat_id=chat_id, text=update.message.text)

            # print "----"
            # print update.message.chat_id
            # print update.message.chat_type
            # print update.message['chat']['type']

            m = Mensagem()

            m.direcao = 2
            if message.chat.type == 'private':
                m.tipo = 1
            else:
                grupo = Grupo().get_or_add([message.chat.id, message.chat.title], self.zapuser)

                m.tipo = 2
                m.grupo = grupo

            m.chat_id = chat_id
            m.contato = contato
            m.zapuser = self.zapuser
            m.mensagem = message.text
            m.mensagem_id = message.message_id
            m.servidor_recebeu = datetime.datetime.fromtimestamp(int(message.date))

            if message.photo:
                photo = message.photo
                largest = photo[len(photo) - 1]

                midia = Midia()
                midia.tipo_midia = 1
                midia.hash = largest.file_id
                midia.width = largest.width
                midia.height = largest.height
                midia.size = largest.file_size
                # midia.save()

                m.midia = midia

            m.save()
            CommandBOT(self.zapuser, m).parse()
            """

    def loop(self):
        print("start poll")
        #time.sleep(10)
        TelegramBot.connection.polling()

        """
        while True:
            time.sleep(1)
            TelegramBot.bot.get_updates(long_polling_timeout=3)

            print("pooling..")
        """

            # if self.send_messages:
            #    print "deu sendmessages"
            #    self.sendMessages()

        # self.bot.polling(False, 1, 1)
        # self.bot.__retrieve_updates(1)
        print("end poll")


    """
    def connect(self):
        # self.zapuser.is_logado = False
        # self.zapuser.save()

        self.last_connect_time = timezone.now()
        self.onLogado()

    def reconnect(self):
        # self.api.restart()
        self.connect()
    
    def onLogado(self, event=None):
        from apps.whatsapp.models import Mensagem
        self.zapuser.is_logado = True
        self.zapuser.qtd_ultimo_login_erro = 0
        self.zapuser.ultimo_login_sucesso = timezone.now()
        self.zapuser.save()

        ""
        # reseta os envios pendurados
        msgs = Mensagem.objects.filter( zapuser = self.zapuser, status_envio = 2)
        for m in msgs:
            m.status_envio = 1
            m.save()

        ""
        self.sendMessages()

    def onLoginFailed(self, event):
        print "Falhou LOGIN ", event[0], event[1]
        self.zapuser.qtd_ultimo_login_erro = self.zapuser.qtd_ultimo_login_erro + 1
        self.zapuser.ultimo_login_erro = timezone.now()

        if self.zapuser.qtd_ultimo_login_erro >= 5:
            self.zapuser.ativo = False

        self.zapuser.save()

        if not self.zapuser.ativo:
            print "Numero de tentativas maximas atingidas"
            exit()

    def onDeslogado(self, event):
        # self.zapuser.is_logado = False
        # self.zapuser.save()
        self.reconnect()

    def run(self):
        # se nao ok, aguardar um tempo tentar novamente até dar o numero maximo de tentativas e desativar
        print "Iniciando Numero", self.zapuser.numero, os.getpid()
        self.zapuser.set_pid(os.getpid())
        self.connect()
        self.loop()
        # self.zapuser.stop_running()
    """


    """
    def sendMessages(self):
        from django.db import connection
        connection.close()

        # self.zapuser.do_sendMessages()

        from apps.whatsapp.models import Mensagem
        interface = Django_TelegramAPI(self.zapuser, False)
        for m in Mensagem.objects.filter(direcao=1, status_envio=1, zapuser=self.zapuser).order_by('pk'):
            m.status_envio = 2
            m.enviada = True
            m.save()

            # process_sendMessage.delay(interface, m)
            bg = False

            if m.midia:
                if m.midia.xv:
                    if m.midia.xv.telegram_file_id == "" and m.midia.xv.telegram_file_id_original == "":
                        bg = True

            if bg:
                process_sendMessage.delay(interface, m)
            else:
                process_sendMessage(interface, m)
    """


"""
class TelegramBot:
    updater = None
    bot = None
    token = None
    messages = []
    pool_size = 100
    chats = {}

    def __init__(self, token=None):

        if not TelegramBot.token:
            TelegramBot.token = token

        if not TelegramBot.token:
            TelegramBot.token = os.environ.get("TELEGRAM_TOKEN")

        if not TelegramBot.token:
            raise Exception("Telegram Bot needs a token")

        if TelegramBot.updater is None:
            logger.info("Starting Telegram Bot")
            TelegramBot.updater = Updater(token=TelegramBot.token)
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

        #self.updater = TelegramBot.updater
        #self.bot = TelegramBot.bot

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
"""


