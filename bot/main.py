from telegram.ext import (CommandHandler, ConversationHandler, Updater, MessageHandler, Filters, StringCommandHandler)
from telegram import InputMediaPhoto, ParseMode, bot, ReplyKeyboardMarkup, ReplyKeyboardRemove

from requests import post, get, delete, put

import config
from data.users import User
from data import db_session

import base64
from io import BytesIO
from werkzeug import exceptions
import logging
from datetime import datetime

import requests

logging.basicConfig(
    filename='logs.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

db_session.global_init("db/users.sqlite")

is_in_rooms = dict()  # here we storage, if user is in /rooms or not
current_rooms = dict()  # all current user's rooms
current_room = dict()  # local id of current user's room
current_images = dict()  # all current user's images in current room
current_image = dict()  # local id of current user's image
fit_rooms = dict()  # a number of fit rooms (where user can save his image)
loaded_im_id = dict()  # id (on API) of image which user just uploaded
filtered_im_id = dict()  # id (on API) of filtered image which user just uploaded
start_text = '<b>Главная</b>\n\n' \
             ' 🌃 Чтобы приступить к обработке изображения, просто пришли мне его!\n' \
             ' 🏘 Для просмотра своих комнат напиши /rooms\n' \
             ' 🤔 Чтобы получить помощь, используй /help'
updater = None


def home_menu(update):
    global start_text
    is_in_rooms[update.message.chat_id] = False
    reply_keyboard = [['/rooms', '/help']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(start_text, parse_mode=ParseMode.HTML, reply_markup=markup)


def start(update, context):
    is_in_rooms[update.message.chat_id] = False
    reply_keyboard = [['/help']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    session = db_session.create_session()
    chat_id = update.message.chat_id
    user = session.query(User).filter(User.chat_id == chat_id).first()
    if not user:
        name = update.message.chat.first_name
        lastname = update.message.chat.last_name
        response = post(f'{config.API_ADDRESS}/api/users', json={'name': name, 'lastname': lastname}).json()
        if 'success' in response.keys():
            user = User(name=name, lastname=lastname, chat_id=chat_id, mainid=response.get('id'))
            session.add(user)
            session.commit()
            logging.info(f'New user registered: {chat_id} {lastname} {name}')
            update.message.reply_text(f"Привет, {name}! 👋\n"
                                      f" 📷Я помогу тебе наложить фильтр на твое фото.\n"
                                      f"Помощь по командам - /help.\n"
                                      f"А для того, чтобы наложить фильтр на твое фото, пришли мне его! "
                                      f"(ограничение по размеру файла: 500кб)\n\n"
                                      " 😽 Приятного использования!", reply_markup=markup)
        else:
            logging.error(f'During /rooms API\'s sent error: {user.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return home(update, context)
    else:
        name = user.name
        update.message.reply_text(f"Привет, {name}! 👋\n"
                                  f" 📷 Я помогу тебе наложить фильтр на твое фото.\n"
                                  f"Помощь по командам - /help.\n"
                                  f" А для того, чтобы наложить фильтр на твое фото, пришли мне его! "
                                  f"(ограничение по размеру файла: 500кб)\n\n"
                                  "😽 Приятного использования!", reply_markup=markup)


def help(update, context):
    is_in_rooms[update.message.chat_id] = False
    reply_keyboard = [['/rooms', '/help']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        "  Я помогу наложить фильтр на фото.\n"
        "Чтобы начать, просто пришлите его мне!\n\n"
        "Так же, вы можете создать и управлять <i>комнатами</i>\n"
        "<b>Комната</b> - особое хранилище, куда вы можете загрузить ваши фотографии, и поделиться ими, добавив туда "
        "своих друзей!\n\n"
        "❗️Важно\n"
        "   - <b>Отправляйте фаше фото только в главном меню!</b>"
        "   - <b>Отправляйте ваше изображение именно как фото!</b>\n"
        "   - <b>Ограничение на размер одного фото - 500кб</b>\n"
        "   - <b>На загрузку списка комнат и изображений требуется время, спасибо за ваше терпение!</b>\n"
        "   - <b>Поддерживаемые форматы: JPG, PNG, BMP</b>\n"
        "   - <b>Пожалуйста, не отправляйте сообщения слишком быстро! Если вы прислали сообщение, и на него более "
        "минуты нету ответа, напишите разработчикам (ссылки ниже)</b>\n\n"
        "✏️Список доступных команд:\n"
        "  /rooms - открыть список своих комнат\n"
        "  /help - получить помощь (это сообщение)\n\n"
        "👨‍💻 Разработчики: @a7ult, @gabidullin_kamil\n"
        "Github (a7ult): https://github.com/sultanowskii/a7PhotoFilter\n\n"
        " 😽 Приятного использования!", parse_mode=ParseMode.HTML, reply_markup=markup)


def show_rooms(update, context, refresh=True):  # Function to show all users' rooms. 'Refresh' is need or not to
    # update rooms-list (to make it works faster)
    update.message.reply_text('👾Открываю список комнат...')
    text = '🏫<b>Ваши комнаты</b>:\n'
    if refresh:
        session = db_session.create_session()
        user_id = session.query(User).filter(User.chat_id == str(update.message.chat_id)).first().mainid
        user = None
        for k in range(3):
            try:
                user = get(f'{config.API_ADDRESS}/api/users/{user_id}', timeout=3).json()
                break
            except requests.exceptions.ConnectionError:
                if k < 2:
                    continue
                logging.fatal(f'Server is unreachable!')
                update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
                return home(update, context)
        if not user or user.get('error'):
            logging.error(f'During /rooms API\'s sent error: {user.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return home(update, context)
        rooms = user['User'].get('rooms')
        global current_rooms
        current_rooms[update.message.chat_id] = []
        for i in range(len(rooms)):
            room = None
            for k in range(3):
                try:
                    room = get(f'{config.API_ADDRESS}/api/rooms/{rooms[i]}', timeout=3).json()
                    break
                except requests.exceptions.ConnectionError:
                    if k < 2:
                        continue
                    logging.fatal(f'Server is unreachable!')
                    update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, '
                                              '@gabidullin_kamil!')
                    return home(update, context)
            if not room or room.get('error'):
                logging.error(f'During /rooms API\'s sent error: {room.get("error")}')
                update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                          'скоро все наладится!')
                return home(update, context)
            text += f" <b>{i + 1}</b>: " + room['Room'].get('name') + '\n'
            current_rooms[update.message.chat_id].append(room)
    else:
        rooms = current_rooms.get(update.message.chat_id)
        for i in range(len(rooms)):
            text += f" <b>{i + 1}</b>: " + rooms[i]['Room'].get('name') + '\n'
    if len(rooms) == 0:
        reply_keyboard = [['🖍Добавить комнату'],
                          ['📩Добавиться в комнату', '↩️Назад']]
    else:
        reply_keyboard = [['🖍Добавить комнату', '🚪Войти в комнату'],
                          ['📩Добавиться в комнату', '↩️Назад']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    return 1


def show_room(update, context, num=None, refresh=True):  # Function to show user one current room, num is room's local
    # id, refresh is parameter to or not to update images-list (to make it works faster)
    global current_room
    global current_rooms
    global current_image
    global current_images
    if num == None:
        num = update.message.text
    else:
        num = int(num) + 1
    curr_id = update.message.chat_id
    if str(num) not in list(str(i) for i in range(1, len(current_rooms[curr_id]) + 1)):
        update.message.reply_text(f'Введите номер комнаты.')
        return 3
    current_room[curr_id] = int(num) - 1
    room = current_rooms[curr_id][current_room[curr_id]]['Room']
    name = room.get('name')
    text = f'🗃Комната \"{name}\":\n'
    update.message.reply_text('👾Открываю список изображений...')
    if refresh:
        images = room.get('images')
        current_images[update.message.chat_id] = []
        for i in range(len(images)):
            if images[i] == None:
                continue
            image = None
            for k in range(3):
                try:
                    image = get(f'{config.API_ADDRESS}/api/images/{images[i]}', timeout=3).json()
                    break
                except requests.exceptions.ConnectionError:
                    if k < 2:
                        continue
                    logging.fatal(f'Server is unreachable!')
                    update.message.reply_text(
                        '😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
                    return home(update, context)
            if not image or image.get('error'):
                logging.error(f'During /rooms API\'s sent error: {image.get("error")}')
                update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                          'скоро все наладится!')
                return home(update, context)
            text += f" <b>{i + 1}</b>: " + image['Image'].get('name') + '\n'
            current_images[update.message.chat_id].append(image)
    else:
        images = current_images.get(update.message.chat_id)
        for i in range(len(images)):
            text += f" <b>{i + 1}</b>: " + images[i]['Image'].get('name') + '\n'
    reply_keyboard = [['❌Удалить комнату', '📣Пригласить людей'],
                      ['🌄Открыть изображение', '🚶‍♂️Выйти из комнаты'],
                      ['↩️Назад']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    return 5


def rooms(update, context):
    is_in_rooms[update.message.chat_id] = True
    return show_rooms(update, context)


def command_rooms(update, context):  # 1st in Covnersation
    command = update.message.text
    if command == '🖍Добавить комнату':
        update.message.reply_text('📝Введите название комнаты:', reply_markup=ReplyKeyboardRemove())
        return 2
    elif command == '🚪Войти в комнату':
        chat_id = update.message.chat_id
        if len(current_rooms[chat_id]) == 0:
            session = db_session.create_session()
            username = ''
            try:
                username = session.query(User).filter(User.chat_id == chat_id).first().name + ', '
            except:
                logging.warning(f'Unregistered user entered dialog. Chat_id: {chat_id}')
            update.message.reply_text(f'😿Извини, {username}я тебя не понял.\n\nНапиши /help, если тебе нужна помощь!')
            return home(update, context)
        reply_keyboard = []
        rooms_count = len(current_rooms[update.message.chat_id])
        if rooms_count % 3 == 0:
            for i in range(0, int(rooms_count / 3)):
                line = []
                for j in range(1, 4):
                    line.append(str(i * 3 + j))
                reply_keyboard.append(line)
        else:
            for i in range(0, int(rooms_count / 3) + 1):
                line = []
                for j in range(1, 4):
                    if i * 3 + j > rooms_count:
                        break
                    line.append(str(i * 3 + j))
                reply_keyboard.append(line)
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text('🔢Введите номер комнаты.', reply_markup=markup)
        return 3
    elif command == '📩Добавиться в комнату':
        reply_keyboard = [['↩️Назад']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text('📧 Введите код комнаты:', reply_markup=markup)
        return 4
    elif command == '↩️Назад':
        is_in_rooms[update.message.chat_id] = False
        return home(update, context)
    else:
        session = db_session.create_session()
        username = ''
        chat_id = update.message.chat_id
        try:
            username = session.query(User).filter(User.chat_id == chat_id).first().name + ', '
        except:
            logging.warning(f'Unregistered user entered dialog. Chat_id: {chat_id}')
        update.message.reply_text(f'😿Извини, {username}я тебя не понял.\n\nНапиши /help, если тебе нужна помощь!')
        return home(update, context)


def add_room(update, context):  # 2nd in Conversation
    name = update.message.text
    if name == '↩️Назад':
        return show_rooms(update, context, False)
    session = db_session.create_session()
    if len(current_rooms[update.message.chat_id]) < config.ROOM_IMAGE_LIMIT:
        user_id = session.query(User).filter(User.chat_id == str(update.message.chat_id)).first().mainid
        response = None
        for k in range(3):
            try:
                response = post(f'{config.API_ADDRESS}/api/rooms', json={'name': name, 'users_id': str(user_id)},
                                timeout=3).json()
                break
            except requests.exceptions.ConnectionError:
                if k < 2:
                    continue
                logging.fatal(f'Server is unreachable!')
                update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
                return home(update, context)
        if not response or response.get('error'):
            logging.error(f'During /rooms API\'s sent error: {response.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return home(update, context)
        update.message.reply_text('✅Комната успешно создана!')
        logging.info(f'Added new room! ID: {response.get("id")}')
        return show_rooms(update, context)
    else:
        update.message.reply_text('❗️У вас слишком много комнат.')
        return show_rooms(update, context, refresh=False)


def room(update, context):  # 3rd in Conversation
    return show_room(update, context)


def add_user_to_room(update, context):  # 4th in Conversation
    rid = ''
    name = ''
    if update.message.text == '↩️Назад':
        return show_rooms(update, context)
    try:
        rid, name = update.message.text.split('*')
        rid = int(rid)
    except Exception as e:
        reply_keyboard = [['↩️Назад']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text('Введите корректный код!', reply_markup=markup)
        return 4
    session = db_session.create_session()
    userid = session.query(User).filter(User.chat_id == update.message.chat_id).first().mainid
    response = None
    for k in range(3):
        try:
            response = get(f'{config.API_ADDRESS}/api/rooms/{rid}', timeout=3).json()
            break
        except requests.exceptions.ConnectionError:
            if k < 2:
                continue
            logging.fatal(f'Server is unreachable!')
            update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
            return home(update, context)
    if response.get('error') or response.get('Room')['name'] != name:
        reply_keyboard = [['↩️Назад']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("Введите корректный код!", reply_markup=markup)
        return 4
    response = None
    for k in range(3):
        try:
            response = put(f'{config.API_ADDRESS}/api/rooms/{rid}', json={'users_id': userid}, timeout=3).json()
            break
        except requests.exceptions.ConnectionError:
            if k < 2:
                continue
            logging.fatal(f'Server is unreachable!')
            update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
            return home(update, context)
    if not response:
        logging.error(f'During /rooms API\'s sent error: {response.get("error")}')
        update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                  'скоро все наладится!')
        return home(update, context)
    if response.get('error') == exceptions.Forbidden:
        reply_keyboard = [['↩️Назад']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text(f'🏚Эта комната переполнена! Введите другой код.', reply_markup=markup)
        return 4
    elif response.get('error'):
        logging.error(f'During /rooms API\'s sent error: {response.get("error")}')
        update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                  'скоро все наладится!')
        return home(update, context)
    update.message.reply_text(f'✅Вы были успешно добавлены в комнату \"{name}\"')
    return show_rooms(update, context)


def command_room(update, context):  # 5th in Conversation
    global current_room
    global current_rooms
    command = update.message.text
    userid = update.message.chat_id
    if command == '❌Удалить комнату':
        reply_keyboard = [['✅Да', '❌Нет']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text('Вы уверены?', reply_markup=markup)
        return 6
    elif command == '📣Пригласить людей':
        room = current_rooms[userid][current_room[userid]]['Room']
        rid = room.get('id')
        name = room.get('name')
        code = f'{rid}*{name}'
        update.message.reply_text(f'📝Ваш друг должен ввести этот код: \n'
                                  f'<code>{code}</code>\nво вкладке "Добавиться в комнату"', parse_mode=ParseMode.HTML)
        return show_room(update, context, num=current_room[userid], refresh=False)
    elif command == '🌄Открыть изображение':
        global current_images
        if current_images.get(userid):
            reply_keyboard = []
            images_count = len(current_rooms[userid][current_room[userid]]['Room']['images'])
            if images_count % 3 == 0:
                for i in range(0, int(images_count / 3)):
                    line = []
                    for j in range(1, 4):
                        line.append(str(i * 3 + j))
                    reply_keyboard.append(line)
            else:
                for i in range(0, int(images_count / 3) + 1):
                    line = []
                    for j in range(1, 4):
                        if i * 3 + j > images_count:
                            break
                        line.append(str(i * 3 + j))
                    reply_keyboard.append(line)
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            update.message.reply_text('🔢Введите номер изображения.', reply_markup=markup)
            return 7
        else:
            update.message.reply_text('📄Эта комната пуста')
            return show_room(update, context, current_room[userid], False)
    elif command == '↩️Назад':
        return show_rooms(update, context, refresh=False)
    elif command == '🚶‍♂️Выйти из комнаты':
        reply_keyboard = [['✅Да', '❌Нет']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text('Вы уверены?', reply_markup=markup)
        return 10
    else:
        session = db_session.create_session()
        username = ''
        chat_id = update.message.chat_id
        try:
            username = session.query(User).filter(User.chat_id == chat_id).first().name + ', '
        except:
            logging.warning(f'Unregistered user entered dialog. Chat_id: {chat_id}')
        update.message.reply_text(f'😿Извини, {username}я тебя не понял.\n\nНапиши /help, если тебе нужна помощь!')
        return home(update, context)


def delete_room(update, context):  # 6th in covnersation
    answer = update.message.text
    if answer == '✅Да' or answer.lower() == 'да':
        global current_rooms
        global current_room
        userid = update.message.chat_id
        rid = current_rooms[userid][current_room[userid]]['Room']['id']
        response = None
        for k in range(3):
            try:
                response = delete(f'{config.API_ADDRESS}/api/rooms/{rid}', timeout=3).json()
                break
            except requests.exceptions.ConnectionError:
                if k < 2:
                    continue
                logging.fatal(f'Server is unreachable!')
                update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
                return home(update, context)
        if not response or response.get('error'):
            logging.error(f'During /rooms API\'s sent error: {response.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return home(update, context)
        update.message.reply_text('ℹ️Комната была успешно удалена!')
        return show_rooms(update, context)
    return show_rooms(update, context, False)


def image(update, context):  # 7th in Conversation
    global current_image
    global current_images
    num = update.message.text
    userid = update.message.chat_id
    if num not in list(str(i) for i in range(1, len(current_images[userid]) + 1)):
        update.message.reply_text(f'🔢Введите номер изображения.')
        return 7
    current_image[userid] = int(num) - 1
    image = current_images[update.message.chat_id][current_image[update.message.chat_id]].get('Image')
    file = base64.b64decode(image.get('data'))
    name = image.get('name')
    reply_keyboard = [['🗑Удалить картинку', '✍️Изменить название картинки'],
                      ['↩️Назад']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    updater.bot.sendPhoto(update.message.chat_id, BytesIO(file))
    update.message.reply_text(f'🌆Изображение \"{name}\"', reply_markup=markup)
    return 8


def command_image(update, context):  # 8th in Conversation
    command = update.message.text
    if command == '🗑Удалить картинку':
        reply_keyboard = [['✅Да', '❌Нет']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text('Вы уверены?', reply_markup=markup)
        return 9
    elif command == '✍️Изменить название картинки':
        update.message.reply_text('Введите новое название изображения')
        return 11
    elif command == '↩️Назад':
        global current_room
        show_room(update, context, num=current_room[update.message.chat_id], refresh=False)
        return 5
    else:
        session = db_session.create_session()
        username = ''
        chat_id = update.message.chat_id
        try:
            username = session.query(User).filter(User.chat_id == chat_id).first().name + ', '
        except:
            logging.warning(f'Unregistered user entered dialog. Chat_id: {chat_id}')
        update.message.reply_text(f'😿Извини, {username}я тебя не понял.\n\nНапиши /help, если тебе нужна помощь!')
        return home(update, context)


def delete_image(update, context):  # 9th in Conversation
    response = update.message.text
    global current_image
    global current_images
    global current_rooms
    global current_room
    if response == '✅Да' or response.lower() == 'да':
        userid = update.message.chat_id
        iid = current_images[userid][current_image[userid]]['Image'].get('id')
        response = None
        for k in range(3):
            try:
                response = delete(f'{config.API_ADDRESS}/api/images/{iid}', timeout=3).json()
                break
            except requests.exceptions.ConnectionError:
                if k < 2:
                    continue
                logging.fatal(f'Server is unreachable!')
                update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
                return home(update, context)
        rid = current_rooms[userid][current_room[userid]]['Room']['id']
        for k in range(3):
            try:
                current_rooms[userid][current_room[userid]] = get(f'{config.API_ADDRESS}/api/rooms/{rid}',
                                                                  timeout=3).json()
                break
            except requests.exceptions.ConnectionError:
                if k < 2:
                    continue
                logging.fatal(f'Server is unreachable!')
                update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
                return home(update, context)
        current_images[userid][current_image[userid]] = None
        if not response or response.get('error'):
            logging.error(f'During /rooms API\'s sent error: {response.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return home(update, context)
        update.message.reply_text('ℹ️Изображение было успешно удалено!')
        return show_room(update, context, current_room[update.message.chat_id])
    return show_room(update, context, current_room[update.message.chat_id], refresh=False)


def leave_the_room(update, context):  # 10 in Conversation
    ans = update.message.text
    if ans == '✅Да':
        global current_rooms
        global current_room
        room = current_rooms[update.message.chat_id][current_room[update.message.chat_id]].get('Room')
        rid = room.get('id')
        room_name = room.get('name')
        session = db_session.create_session()
        userid = session.query(User).filter(User.chat_id == update.message.chat_id).first().mainid
        response = None
        for k in range(3):
            try:
                response = put(f'{config.API_ADDRESS}/api/rooms/{rid}', json={'users_id': userid,
                                                                              'remove_user': True}, timeout=3).json()
                break
            except requests.exceptions.ConnectionError:
                if k < 2:
                    continue
                logging.fatal(f'Server is unreachable!')
                update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
                return home(update, context)
        if not response or response.get('error'):
            logging.error(f'During /rooms API\'s sent error: {response.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return home(update, context)
        update.message.reply_text(f'✅Вы успешно покинули комнату \"{room_name}\"')
        return show_rooms(update, context)
    else:
        return show_room(update, context, num=current_room[update.message.chat_id])


def change_the_name_of_the_photo(update, context):  # 11 in Conversation
    global current_image
    global current_images
    new_name = update.message.text
    info = current_images[update.message.chat_id][current_image[update.message.chat_id]].get('Image')
    image_id = info.get('id')
    response = None
    for k in range(3):
        try:
            response = put(f'{config.API_ADDRESS}/api/images/{image_id}', json={'name': new_name}, timeout=3).json()
            break
        except requests.exceptions.ConnectionError:
            if k < 2:
                continue
            logging.fatal(f'Server is unreachable!')
            update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
            return home(update, context)
    if not response or response.get('error'):
        logging.error(f'During /rooms API\'s sent error: {response.get("error")}')
        update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                  'скоро все наладится!')
        return home(update, context)
    update.message.reply_text(f'✅Вы были успешно поменяли название изображения. Новое название: \"{new_name}\"')
    return show_room(update, context, num=current_room[update.message.chat_id])


def image_get(update, context):
    if is_in_rooms.get(update.message.chat_id, None) == True:
        update.message.reply_text('Накладывать фильтры можно только в главном меню.')
        return ConversationHandler.END
    global loaded_im_id
    file_info = context.bot.get_file(update.message.photo[-1].file_id)
    mime = file_info.file_path.split('.')[-1].upper()
    file = bytes(file_info.download_as_bytearray())
    base64_data = base64.b64encode(file).decode('utf-8')
    reply_keyboard = [['👽Другой мир 1', '👽Другой мир 2', '⚽️Чёрно-белое 1'],
                      ['🖲 Негатив', '💡Высветление', '🌌Размытие'],
                      ['📈Увеличение резкости', '📉Уменьшение качества', '🔊Добавление шума'],
                      ['🏺Ретро', '⚫️⚪️Чёрно-белое 2', '👽Другой мир 3'], ['👽Другой мир 4']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    text = '🔠<b>Выберите фильтр:</b>\n\n 👽Другой мир 1\n 👽Другой мир 2\n ⚽️Чёрно-белое 1\n 🖲 Негатив\n' \
           ' 💡Высветление \n 🌌Размытие\n 📈Увеличение резкости\n 📉Уменьшение качества\n 🔊Добавление шума\n 🏺Ретро' \
           '\n ⚫️⚪️Чёрно-белое 2\n 👽Другой мир 3\n 👽Другой мир 4'
    now = datetime.now().strftime('%H%M%S-%d%m%Y')
    response = None
    for k in range(3):
        try:
            response = post(f'{config.API_ADDRESS}/api/images',
                            json={'name': now, 'mime': mime, 'image_data': base64_data}, timeout=3)
            break
        except requests.exceptions.ConnectionError:
            if k < 2:
                continue
            logging.fatal(f'Server is unreachable!!')
            update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
            return home(update, context)
    code = response.status_code
    response = response.json()
    if not response or response.get('error'):
        if code == 400:
            logging.warning('Invalid image-data sent to server during /image')
            update.message.reply_text('😿С изображением возникли проблемы, пожалуйста, попробуйте другое!')
            return home(update, context)
        else:
            logging.error(f'During /image API\'s sent error: {response.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
        return home(update, context)
    iid = int(response.get('id'))
    loaded_im_id[update.message.chat_id] = iid
    update.message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    return 1


def choose_filter(update, context):  # 1st in Conversation
    global loaded_im_id
    global filtered_im_id
    filter_type = update.message.text
    fid = 0
    if filter_type == '👽Другой мир 1':
        fid = 1
    elif filter_type == '👽Другой мир 2':
        fid = 2
    elif filter_type == '⚽️Чёрно-белое 1':
        fid = 3
    elif filter_type == '🖲 Негатив':
        fid = 4
    elif filter_type == '💡Высветление':
        fid = 5
    elif filter_type == '🌌Размытие':
        fid = 6
    elif filter_type == '📈Увеличение резкости':
        fid = 7
    elif filter_type == '📉Уменьшение качества':
        fid = 8
    elif filter_type == '🔊Добавление шума':
        fid = 9
    elif filter_type == '🏺Ретро':
        fid = 10
    elif filter_type == '⚫️⚪️Чёрно-белое 2':
        fid = 11
    elif filter_type == '👽Другой мир 3':
        fid = 12
    elif filter_type == '👽Другой мир 4':
        fid = 13
    else:
        update.message.reply_text('Воспользуйтесь кнопками ответа.')
        reply_keyboard = [['👽Другой мир 1', '👽Другой мир 2', '⚽️Чёрно-белое 1'],
                          ['🖲 Негатив', '💡Высветление', '🌌Размытие'],
                          ['📈Увеличение резкости', '📉Уменьшение качества', '🔊Добавление шума'],
                          ['🏺Ретро', '⚫️⚪️Чёрно-белое 2', '👽Другой мир 3'], ['👽Другой мир 4']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text('Выберите фильтр:', reply_markup=markup)
        return 1
    update.message.reply_text('👾Фото обрабатывается...')
    imid = loaded_im_id[update.message.chat_id]
    response = None
    for k in range(3):
        try:
            response = get(f'{config.API_ADDRESS}/api/images/{imid}?action=applyfilter&fid={fid}', timeout=3).json()
            break
        except requests.exceptions.ConnectionError:
            if k < 2:
                continue
            logging.fatal(f'Server is unreachable!')
            update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
            return home(update, context)
    if not response or response.get('error'):
        logging.error(f'During /image API\'s sent error: {response.get("error")}')
        update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                  'скоро все наладится!')
        return home(update, context)
    file = None
    try:
        file = base64.b64decode(response['Image'].get('data'))
    except Exception as e:
        logging.warning(f'During decoding filtered image error happened. Error: {e}')
        update.message.reply_text('😿С изображением возникли проблемы, пожалуйста, попробуйте другое!')
        return home(update, context)
    filtered_im_id[update.message.chat_id] = response['Image']['id']
    updater.bot.sendPhoto(update.message.chat_id, BytesIO(file))
    reply_keyboard = [['✅Да', '❌Нет']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text('Хотите сохранить фотографию?', reply_markup=markup)
    logging.info(f'Added filter {fid} to the image {imid}')
    return 2


def save_image_to_room(update, context):  # 2nd in Conversation
    ans = update.message.text
    if ans.lower() == 'да' or ans == '✅Да':
        global current_rooms
        global fit_rooms
        global filtered_im_id
        session = db_session.create_session()
        user_id = session.query(User).filter(User.chat_id == str(update.message.chat_id)).first().mainid
        user = None
        for k in range(3):
            try:
                user = get(f'{config.API_ADDRESS}/api/users/{user_id}', timeout=3).json()
                break
            except requests.exceptions.ConnectionError:
                if k < 2:
                    continue
                logging.fatal(f'Server is unreachable!')
                update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
                return home(update, context)
        if not user or user.get('error'):
            logging.error(f'During /image API\'s sent error: {user.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return home(update, context)
        update.message.reply_text('👾Открываю список комнат...')
        rooms = user['User'].get('rooms')
        text = '<b>🔢Выберите комнату (здесь показаны только подходящие комнаты)</b>:\n'
        current_rooms[update.message.chat_id] = []
        cnt = 1
        for i in range(len(rooms)):
            room = None
            for k in range(3):
                try:
                    room = get(f'{config.API_ADDRESS}/api/rooms/{rooms[i]}', timeout=3).json()
                    break
                except requests.exceptions.ConnectionError:
                    if k < 2:
                        continue
                    logging.fatal(f'Server is unreachable!')
                    update.message.reply_text(
                        '😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
                    return home(update, context)
            if not room or room.get('error'):
                logging.error(f'During /image API\'s sent error: {room.get("error")}')
                update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного,'
                                          'скоро все наладится!')
                return home(update, context)
            if len(room['Room']['images']) < config.ROOM_IMAGE_LIMIT:
                text += f' <b>{cnt}</b>: ' + room['Room'].get('name') + '\n'
                cnt += 1
                current_rooms[update.message.chat_id].append(room)
        if cnt == 1:
            fit_rooms[update.message.chat_id] = 0
            if len(current_rooms[update.message.chat_id]) < config.USER_ROOM_LIMIT:
                update.message.reply_text("🙅‍♂Простите, нет доступных комнат. Давайте создадим новую! Введите название:")
                return 4
            else:
                update.message.reply_text("🙅‍♂Простите, мы не можем создать еще одну комнату, так как у вас уже есть"
                                          "максимальное количество созданных комнат.")
                return home(update, context)
        else:
            cnt = cnt - 1
            fit_rooms[update.message.chat_id] = cnt
            reply_keyboard = []
            if cnt % 3 == 0:
                for i in range(0, int(cnt / 3)):
                    line = []
                    for j in range(1, 4):
                        line.append(str(i * 3 + j))
                    reply_keyboard.append(line)
            else:
                for i in range(0, int(cnt / 3) + 1):
                    line = []
                    for j in range(1, 4):
                        if i * 3 + j > cnt:
                            break
                        line.append(str(i * 3 + j))
                    reply_keyboard.append(line)
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            update.message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
            return 3
    else:
        iid = filtered_im_id.get(update.message.chat_id)
        response = None
        for k in range(3):
            try:
                response = delete(f'{config.API_ADDRESS}/api/images/{iid}', timeout=3).json()
                break
            except requests.exceptions.ConnectionError:
                if k < 2:
                    continue
                logging.fatal(f'Server is unreachable!')
                update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
                return home(update, context)
        if not response or response.get('error'):
            logging.warning('During delete-request for filtered image error on API happened')
        reply_keyboard = [['✅Да', '❌Нет']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text('Хотите ли вы наложить другой фильтр на загруженное вами фото?', reply_markup=markup)
        return 6


def choose_room(update, context):  # 3rd in Conversation
    global fit_rooms
    global filtered_im_id
    global current_rooms
    num = update.message.text
    if num not in list(str(i) for i in range(1, fit_rooms[update.message.chat_id] + 1)):
        update.message.reply_text(f'🔢Введите номер комнаты')
        return 3
    num = int(num)
    room = current_rooms[update.message.chat_id][num - 1]
    response = None
    for k in range(3):
        try:
            response = put(f'{config.API_ADDRESS}/api/images/{filtered_im_id[update.message.chat_id]}', json={
                'room_id': room['Room']['id']}, timeout=3).json()
            break
        except requests.exceptions.ConnectionError:
            if k < 2:
                continue
            logging.fatal(f'Server is unreachable!')
            update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
            return home(update, context)
    if not response or response.get('error'):
        logging.error(f'During /image API\'s sent error: {response.get("error")}')
        update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                  'скоро все наладится!')
        return home(update, context)
    name = room['Room']['name']
    update.message.reply_text(f'✅Изображение успешно добавлено в комнату {name}')
    update.message.reply_text('🔠Введите название изображения')
    return 5


def add_room_with_image(update, context):  # 4th in Conversation
    global filtered_im_id
    name = update.message.text
    session = db_session.create_session()
    user_id = session.query(User).filter(User.chat_id == str(update.message.chat_id)).first().mainid
    lii = filtered_im_id.get(update.message.chat_id)
    room = None
    for k in range(3):
        try:
            room = post(f'{config.API_ADDRESS}/api/rooms', json={'name': name, 'users_id': str(user_id)},
                        timeout=3).json()
            break
        except requests.exceptions.ConnectionError:
            if k < 2:
                continue
            logging.fatal(f'Server is unreachable!')
            update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
            return home(update, context)
    if not room or room.get('error'):
        logging.error(f'During /image API\'s sent error: {room.get("error")}')
        update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                  'скоро все наладится!')
        return home(update, context)
    else:
        response = None
        for k in range(3):
            try:
                response = put(f'{config.API_ADDRESS}/api/images/{lii}', json={'room_id': room['id']},
                               timeout=3).json()
                break
            except requests.exceptions.ConnectionError:
                if k < 2:
                    continue
                logging.fatal(f'Server is unreachable!')
                update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
                return home(update, context)
        if not response or response.get('error'):
            logging.error(f'During /image API\'s sent error: {response.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return home(update, context)
        update.message.reply_text('✅Комната успешно создана, фото добавлено!')
        update.message.reply_text('🔠Введите название изображения')
        rid = room['id']
        logging.info(f'Added new image with ID {lii} to room with id {rid}')
        return 5


def set_name_to_image(update, context):  # 5th in Conversation
    global filtered_im_id
    name = update.message.text
    fii = filtered_im_id.get(update.message.chat_id)
    response = None
    for k in range(3):
        try:
            response = put(f'{config.API_ADDRESS}/api/images/{fii}', json={'name': name}, timeout=3).json()
            break
        except requests.exceptions.ConnectionError:
            if k < 2:
                continue
            logging.fatal(f'Server is unreachable!')
            update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
            return home(update, context)
    if not response or response.get('error'):
        logging.error(f'During /image API\'s sent error: {response.get("error")}')
        update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                  'скоро все наладится!')
        return home(update, context)
    update.message.reply_text('✅Успешно!')
    reply_keyboard = [['✅Да', '❌Нет']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text('Хотите ли вы наложить другой фильтр на загруженное вами фото?', reply_markup=markup)
    return 6


def continue_editing_photo(update, context):
    answer = update.message.text
    if answer == '✅Да':
        reply_keyboard = [['👽Другой мир 1', '👽Другой мир 2', '⚽️Чёрно-белое 1'],
                          ['🖲 Негатив', '💡Высветление', '🌌Размытие'],
                          ['📈Увеличение резкости', '📉Уменьшение качества', '🔊Добавление шума'],
                          ['🏺Ретро', '⚫️⚪️Чёрно-белое 2', '👽Другой мир 3'], ['👽Другой мир 4']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        text = '🔠<b>Выберите фильтр:</b>\n\n 👽Другой мир 1\n 👽Другой мир 2\n ⚽️Чёрно-белое 1\n 🖲 Негатив\n' \
               ' 💡Высветление \n 🌌Размытие\n 📈Увеличение резкости\n 📉Уменьшение качества\n 🔊Добавление шума\n 🏺Ретро' \
               '\n ⚫️⚪️Чёрно-белое 2\n 👽Другой мир 3\n 👽Другой мир 4'
        update.message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        return 1
    elif answer == '❌Нет':
        iid = loaded_im_id.get(update.message.chat_id)
        response = None
        for k in range(3):
            try:
                response = delete(f'{config.API_ADDRESS}/api/images/{iid}', timeout=3).json()
                break
            except requests.exceptions.ConnectionError:
                if k < 2:
                    continue
                logging.fatal(f'Server is unreachable!')
                update.message.reply_text('😿Сервер недоступен.\n\nСвязь с разработчиками: @a7ult, @gabidullin_kamil')
        return home(update, context)
    else:
        session = db_session.create_session()
        username = ''
        chat_id = update.message.chat_id
        try:
            username = session.query(User).filter(User.chat_id == chat_id).first().name + ', '
        except:
            logging.warning(f'Unregistered user entered dialog. Chat_id: {chat_id}')
        update.message.reply_text(f'😿Извини, {username}я тебя не понял.\n\nНапиши /help, если тебе нужна помощь!')
        return home(update, context)


def home(update, context):
    home_menu(update)
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
            7: [MessageHandler(Filters.text, image)],
            8: [MessageHandler(Filters.text, command_image)],
            9: [MessageHandler(Filters.text, delete_image)],
            10: [MessageHandler(Filters.text, leave_the_room)],
            11: [MessageHandler(Filters.text, change_the_name_of_the_photo)],
        },

        fallbacks=[CommandHandler('home', home)]

    )

    image_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.photo, image_get)],

        states={
            1: [MessageHandler(Filters.text, choose_filter)],
            2: [MessageHandler(Filters.text, save_image_to_room)],
            3: [MessageHandler(Filters.text, choose_room)],
            4: [MessageHandler(Filters.text, add_room_with_image)],
            5: [MessageHandler(Filters.text, set_name_to_image)],
            6: [MessageHandler(Filters.text, continue_editing_photo)]
        },

        fallbacks=[CommandHandler('home', home)]
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(rooms_conv_handler)
    dp.add_handler(image_conv_handler)
    updater.start_polling(poll_interval=3, timeout=15)

    updater.idle()


main()
