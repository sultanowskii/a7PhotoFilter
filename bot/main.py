from telegram.ext import (CommandHandler, ConversationHandler, Updater, MessageHandler, Filters, StringCommandHandler)
from telegram import InputMediaPhoto, ParseMode

from requests import post, get, delete, put

import config
from data.users import User
from data import db_session

import base64
from io import BytesIO
from werkzeug import exceptions
import logging

logging.basicConfig(
    filename='logs.log',
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

db_session.global_init("db/users.sqlite")

current_rooms = dict()
current_room = dict()
current_images = dict()
current_image = dict()
updater = None


def start(update, context):
    session = db_session.create_session()
    chat_id = update.message.chat_id
    user = session.query(User).filter(User.chat_id == chat_id).first()
    if not user:
        name = update.message.chat.first_name
        lastname = update.message.chat.last_name
        answer = post(f'{config.API_ADDRESS}/api/users', json={'name': name, 'lastname': lastname}).json()
        if 'success' in answer.keys():
            user = User(name=name, lastname=lastname, chat_id=chat_id, mainid=answer.get('id'))
            session.add(user)
            session.commit()
            logging.info(f'New user registered: {chat_id} {lastname} {name}')
            update.message.reply_text(f"Привет, {name}! 👋\n"
                                      f" 📷Я помогу тебе наложить фильтр на твое фото.\n"
                                      f"Помощь по командам - /help.\n"
                                      f"А для того, чтобы наложить фильтр на твое фото, пришли мне его! "
                                      f"(ограничение по размеру файла: 300кб)")
        else:
            err = answer.get('error')
            update.message.reply_text(f'Ошибка сервера! {err}')
    else:
        name = user.name
        update.message.reply_text(f"Привет, {name}! 👋\n"
                                  f" 📷 Я помогу тебе наложить фильтр на твое фото.\n"
                                  f"Помощь по командам - /help.\n"
                                  f" А для того, чтобы наложить фильтр на твое фото, пришли мне его! "
                                  f"(ограничение по размеру файла: 300кб)")


def help(update, context):
    update.message.reply_text(
        "  Я помогу наложить фильтр на фото.\n"
        "Чтобы начать, просто пришли его мне!\n\n"
        "❗️ <b>Ограничение на размер одного фото - 300кб</b>\n\n"
        "   Так же, вы можете создать и управлять <i>комнатами</i>\n"
        "Комната - особое хранилище, куда вы можете загрузить ваши фотографии, и поделиться ими, добавив туда своих "
        "друзей!\n\n"
        "✏️Список доступных команд:\n"
        "  /rooms - открыть список своих комнат\n"
        "  /help - получить помощь (это сообщение)\n\n"
        "👨‍💻 Разработчики: @a7ult, @gabidullin_kamil\n"
        "Github (a7ult): https://github.com/sultanowskii/a7PhotoFilter", parse_mode=ParseMode.HTML)


def rooms(update, context):
    session = db_session.create_session()
    user_id = session.query(User).filter(User.chat_id == str(update.message.chat_id)).first().mainid
    user = get(f'{config.API_ADDRESS}/api/users/{user_id}').json()
    if user.get('error'):
        logging.error(f'During /rooms API\'s sent error: {user.get("error")}')
        update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                  'скоро все наладится!')
        return
    rooms = user['User'].get('rooms')
    global current_rooms
    text = '<b>Ваши комнаты</b>:\n'
    current_rooms[update.message.chat_id] = []
    for i in range(len(rooms)):
        room = get(f'{config.API_ADDRESS}/api/rooms/{rooms[i]}').json()
        if not room or room.get('error'):
            logging.error(f'During /rooms API\'s sent error: {room.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return
        text += f" <b>{i + 1}</b>: " + room['Room'].get('name') + '\n'
        current_rooms[update.message.chat_id].append(room)
    update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return 1


def command_rooms(update, context):  # 1st in Covnersation
    command = update.message.text
    if command == '🖍Добавить комнату':
        update.message.reply_text('📝Введите название комнаты:')
        return 2
    elif command == '🚪Войти в комнату':
        update.message.reply_text('🔢Введите номер комнаты:')
        return 3
    elif command == '📩Добавиться в комнату':
        update.message.reply_text('📧 Введите код комнаты:')
        return 4
    else:
        session = db_session.create_session()
        username = ''
        chat_id = update.message.chat_id
        try:
            username = session.query(User).filter(User.chat_id == chat_id).first().name + ', '
        except:
            logging.warning(f'Unregistered user entered dialog. Chat_id: {chat_id}')
        update.message.reply_text(f'Извини, {username}я тебя не понял.\n\nНапиши /help, если тебе нужна помощь!')
        return ConversationHandler.END


def add_room(update, context):  # 2nd in Conversation
    name = update.message.text
    session = db_session.create_session()
    user_id = session.query(User).filter(User.chat_id == str(update.message.chat_id)).first().mainid
    answer = post(f'{config.API_ADDRESS}/api/rooms', json={'name': name, 'user_id': str(user_id)}).json()
    if not answer or answer.get('error'):
        logging.error(f'During /rooms API\'s sent error: {answer.get("error")}')
        update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                  'скоро все наладится!')
        return
    else:
        update.message.reply_text('Комната успешно создана!')


def room(update, context):  # 3rd in Conversation
    global current_room
    global current_rooms
    global current_image
    global current_images
    num = update.message.text
    curr_id = update.message.chat_id
    if num not in list(str(i) for i in range(1, len(current_rooms[curr_id] + 1))):
        update.message.reply_text(f'Введите номер комнаты.')
        return 3
    current_room[curr_id] = int(num) - 1
    room = current_rooms[curr_id][current_room[curr_id]]['Room']
    name = room.get('name')
    text = f'Комната \"{name}\":\n'
    images = room.get('images')
    current_images[update.message.chat_id] = []
    for i in range(len(images)):
        image = get(f'{config.API_ADDRESS}/api/images/{images[i]}').json()
        if not image or image.get('error'):
            logging.error(f'During /rooms API\'s sent error: {image.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return 1
        text += f" <b>{i + 1}</b>: " + image['Image'].get('name') + '\n'
        current_images[update.message.chat_id].append(image)
    update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return 5


def add_user_to_room(update, context):  # 4th in Conversation
    rid, name = update.message.text.split('*')
    rid = int(rid)
    session = db_session.create_session()
    userid = session.query(User).filter(User.chat_id == update.message.chat_id).first().id
    answer = put(f'{config.API_ADDRESS}/api/rooms/{rid}', json={'users_id': userid}).json()
    if answer.get('success'):
        updater.bot.send_message(update.message.chat_id, f'✅Вы были успешно добавлены в комнату \"{name}\"')
        return 1
    elif answer.get('error') == exceptions.Forbidden:
        updater.bot.send_message(update.message.chat_id, f'🏚Эта комната переполнена!')
    else:
        logging.error(f'During /rooms API\'s sent error: {answer.get("error")}')
        update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                  'скоро все наладится!')
        return 4


def command_room(update, context):  # 5th in Conversation
    command = update.message.text
    userid = update.message.chat_id
    if command == '❌Удалить комнату':
        update.message.reply_text('Вы уверены?')
        return 6
    elif command == '📣Пригласить людей':
        room = current_rooms[userid][current_room[userid]]['Room']
        rid = room.get('id')
        name = room.get('name')
        code = f'{rid}*{name}'
        update.message.reply_text(f'Ваш друг должен ввести этот код: '
                                  f'<code>{code}</code>\nво вкладке "Добавиться в комнату"', parse_mode=ParseMode.HTML)
        return 7
    elif command == '🌄Открыть изображение':
        update.message.reply_text('🔢Введите номер изображения:')
        return 8
    else:
        session = db_session.create_session()
        username = ''
        chat_id = update.message.chat_id
        try:
            username = session.query(User).filter(User.chat_id == chat_id).first().name + ', '
        except:
            logging.warning(f'Unregistered user entered dialog. Chat_id: {chat_id}')
        update.message.reply_text(f'Извини, {username}я тебя не понял.\n\nНапиши /help, если тебе нужна помощь!')
        return ConversationHandler.END


def delete_room(update, context):  # 6th in covnersation
    answer = update.message.text
    if answer == '✅Да' or answer.lower() == 'да':
        global current_rooms
        global current_room
        userid = update.message.chat_id
        rid = current_rooms[userid][current_room[userid]]['Room']['id']
        answer = delete(f'{config.API_ADDRESS}/api/rooms/{rid}').json()
        if not answer:
            logging.error(f'During /rooms API\'s sent error: {answer.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return 6
        update.message.reply_text('Комната была успешно удалена!')
    return 1


def invite_to_room(update, context):  # 7th in Conversation
    return 3  # в command_room мы просто должны сделать клавиатуру с одной кнопкой - "↩️Назад"


def image(update, context):  # 8th in Conversation
    global current_image
    global current_images
    num = update.message.text
    userid = update.message.chat_id
    if num not in list(str(i) for i in range(1, len(current_images[userid]) + 1)):
        update.message.reply_text(f'Введите номер изображения.')
        return 8
    current_image[userid] = int(num) - 1
    image = current_images[update.message.chat_id][current_image[update.message.chat_id]].get('Image').get('data')
    file = base64.b64decode(image)
    updater.bot.sendPhoto(update.message.chat_id, BytesIO(file))
    return 9


def command_image(update, context):  # 9th in Conversation
    command = update.message.text
    if command == '🗑Удалить картинку':
        update.message.reply_text('Вы уверены?')
        return 10
    else:
        session = db_session.create_session()
        username = ''
        chat_id = update.message.chat_id
        try:
            username = session.query(User).filter(User.chat_id == chat_id).first().name + ', '
        except:
            logging.warning(f'Unregistered user entered dialog. Chat_id: {chat_id}')
        update.message.reply_text(f'Извини, {username}я тебя не понял.\n\nНапиши /help, если тебе нужна помощь!')
        return ConversationHandler.END


def delete_image(update, context):  # 10th in Conversation
    answer = update.message.text
    if answer == '✅Да' or answer.lower() == 'да':
        global current_image
        global current_images
        userid = update.message.chat_id
        iid = current_images[userid][current_image[userid]]['Image'].get('id')
        answer = delete(f'{config.API_ADDRESS}/api/images/{iid}').json()
        if not answer or answer.get('error'):
            logging.error(f'During /rooms API\'s sent error: {answer.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return 10
        update.message.reply_text('Изображение было успешно удалено!')
    return 3


def home(update, context):
    return ConversationHandler.END


def main():
    global updater
    updater = Updater(config.TOKEN, use_context=True)

    dp = updater.dispatcher

    rooms_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('rooms', rooms)],

        states={
            1: [MessageHandler(Filters.text, command_rooms)],
            2: [MessageHandler(Filters.text, add_room)],
            3: [MessageHandler(Filters.text, room)],
            4: [MessageHandler(Filters.text, add_user_to_room)],
            5: [MessageHandler(Filters.text, command_room)],
            6: [MessageHandler(Filters.text, delete_room)],
            7: [MessageHandler(Filters.text, invite_to_room)],
            8: [MessageHandler(Filters.text, image)],
            9: [MessageHandler(Filters.text, command_image)],
            10: [MessageHandler(Filters.text, delete_image)]
        },

        fallbacks=[CommandHandler('home', home)]

    )
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(rooms_conv_handler)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
