import random
import telebot
from telebot import types
from data import db_session
from data.users import User
from data.images import Image
from data.rooms import Room

bot = telebot.TeleBot('токен')
db_session.global_init("db/filter_bot.sqlite")


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.from_user.id, 'Привет! Пока я в разработке!')


bot.polling(none_stop=True, interval=5)
