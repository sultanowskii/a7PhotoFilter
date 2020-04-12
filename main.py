from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler

from requests import request

from data import db_session
from data.users import User
from data.images import Image
from data.rooms import Room


def start(update, context):
    update.message.reply_text(
        "Привет! Пока я в разработке!")


def help(update, context):
    update.message.reply_text(
        "Извини, но пока я ничего не умею 😥")   #   we can copy emojis right from telegram!


def echo(update, context):
    update.message.reply_text(update.message.text)


def main():
    updater = Updater('', use_context=True)

    dp = updater.dispatcher
    text_handler = MessageHandler(Filters.text, echo)

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(text_handler)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
