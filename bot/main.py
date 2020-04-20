from telegram.ext import (CommandHandler, ConversationHandler, Updater, MessageHandler, Filters, StringCommandHandler)
from telegram import InputMediaPhoto, ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove, PhotoSize

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


def show_rooms(update, context, refresh=True):  # Function to show all users' rooms. 'Refresh' is needing or not to
    # update rooms-list (to make it works faster)
    text = '🏫<b>Ваши комнаты</b>:\n'
    if refresh:
        session = db_session.create_session()
        user_id = session.query(User).filter(User.chat_id == str(update.message.chat_id)).first().mainid
        user = get(f'{config.API_ADDRESS}/api/users/{user_id}').json()
        if user.get('error'):
            logging.error(f'During /rooms API\'s sent error: {user.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return ConversationHandler.END
        rooms = user['User'].get('rooms')
        global current_rooms
        current_rooms[update.message.chat_id] = []
        for i in range(len(rooms)):
            room = get(f'{config.API_ADDRESS}/api/rooms/{rooms[i]}').json()
            if not room or room.get('error'):
                logging.error(f'During /rooms API\'s sent error: {room.get("error")}')
                update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                          'скоро все наладится!')
                return ConversationHandler.END
            text += f" <b>{i + 1}</b>: " + room['Room'].get('name') + '\n'
            current_rooms[update.message.chat_id].append(room)
    else:
        rooms = current_rooms.get(update.message.chat_id)
        for i in range(len(rooms)):
            text += f" <b>{i + 1}</b>: " + rooms[i]['Room'].get('name') + '\n'
    reply_keyboard = [['🖍Добавить комнату', '🚪Войти в комнату'],
                      ['📩Добавиться в комнату', '↩️Назад']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


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
    if refresh:
        images = room.get('images')
        current_images[update.message.chat_id] = []
        for i in range(len(images)):
            if images[i] == None:
                continue
            image = get(f'{config.API_ADDRESS}/api/images/{images[i]}').json()
            if not image or image.get('error'):
                logging.error(f'During /rooms API\'s sent error: {image.get("error")}')
                update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                          'скоро все наладится!')
                return ConversationHandler.END
            text += f" <b>{i + 1}</b>: " + image['Image'].get('name') + '\n'
            current_images[update.message.chat_id].append(image)
    else:
        images = current_images.get(update.message.chat_id)
        for i in range(len(images)):
            text += f" <b>{i + 1}</b>: " + images[i]['Image'].get('name') + '\n'
    reply_keyboard = [['❌Удалить комнату', '📣Пригласить людей'],
                      ['🌄Открыть изображение', '↩️Назад']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


def rooms(update, context):
    show_rooms(update, context)
    return 1


def command_rooms(update, context):  # 1st in Covnersation
    command = update.message.text
    if command == '🖍Добавить комнату':
        update.message.reply_text('📝Введите название комнаты:', reply_markup=ReplyKeyboardRemove())
        return 2
    elif command == '🚪Войти в комнату':
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
        update.message.reply_text('🔢Введите номер комнаты:', reply_markup=markup)
        return 3
    elif command == '📩Добавиться в комнату':
        update.message.reply_text('📧 Введите код комнаты:', reply_markup=ReplyKeyboardRemove())
        return 4
    elif command == '↩️Назад':
        return ConversationHandler.END
    else:
        session = db_session.create_session()
        username = ''
        chat_id = update.message.chat_id
        try:
            username = session.query(User).filter(User.chat_id == chat_id).first().name + ', '
        except:
            logging.warning(f'Unregistered user entered dialog. Chat_id: {chat_id}')
        update.message.reply_text(f'😿Извини, {username}я тебя не понял.\n\nНапиши /help, если тебе нужна помощь!')
        return ConversationHandler.END


def add_room(update, context):  # 2nd in Conversation
    name = update.message.text
    if name == '↩️Назад':
        show_rooms(update, context, False)
        return 1
    session = db_session.create_session()
    if len(current_rooms[update.message.chat_id]) < config.ROOM_IMAGE_LIMIT:
        user_id = session.query(User).filter(User.chat_id == str(update.message.chat_id)).first().mainid
        answer = post(f'{config.API_ADDRESS}/api/rooms', json={'name': name, 'users_id': str(user_id)}).json()
        if not answer or answer.get('error'):
            logging.error(f'During /rooms API\'s sent error: {answer.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return ConversationHandler.END
        else:
            update.message.reply_text('✅Комната успешно создана!')
            show_rooms(update, context)
            return 1
    else:
        update.message.reply_text('❗️У вас слишком много комнат.')
        show_rooms(update, context, refresh=False)
        return 1


def room(update, context):  # 3rd in Conversation
    show_room(update, context)
    return 5


def add_user_to_room(update, context):  # 4th in Conversation
    rid, name = update.message.text.split('*')
    rid = int(rid)
    session = db_session.create_session()
    userid = session.query(User).filter(User.chat_id == update.message.chat_id).first().id
    answer = put(f'{config.API_ADDRESS}/api/rooms/{rid}', json={'users_id': userid}).json()
    if answer.get('success'):
        updater.bot.send_message(update.message.chat_id, f'✅Вы были успешно добавлены в комнату \"{name}\"')
        show_rooms(update, context)
        return 1
    elif answer.get('error') == exceptions.Forbidden:
        updater.bot.send_message(update.message.chat_id, f'🏚Эта комната переполнена!')
    elif answer.get('error') == exceptions.NotFound:
        updater.bot.send_message(update.message.chat_id, f'🏚Эта комната переполнена!')
    else:
        logging.error(f'During /rooms API\'s sent error: {answer.get("error")}')
        update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                  'скоро все наладится!')
        return 4


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
        show_room(update, context, num=current_room[userid], refresh=False)
        return 5
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
            update.message.reply_text('🔢Введите номер изображения:', reply_markup=markup)
            return 7
        else:
            update.message.reply_text('📄Эта комната пуста')
            show_room(update, context, current_room[userid], False)
            return 5
    elif command == '↩️Назад':
        show_rooms(update, context, refresh=False)
        return 1
    else:
        session = db_session.create_session()
        username = ''
        chat_id = update.message.chat_id
        try:
            username = session.query(User).filter(User.chat_id == chat_id).first().name + ', '
        except:
            logging.warning(f'Unregistered user entered dialog. Chat_id: {chat_id}')
        update.message.reply_text(f'😿Извини, {username}я тебя не понял.\n\nНапиши /help, если тебе нужна помощь!')
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
        update.message.reply_text('ℹ️Комната была успешно удалена!')
        show_rooms(update, context)
    else:
        show_rooms(update, context, False)
    return 1


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
    reply_keyboard = [['🗑Удалить картинку', '↩️Назад']]
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
        return ConversationHandler.END


def delete_image(update, context):  # 9th in Conversation
    answer = update.message.text
    global current_image
    global current_images
    global current_rooms
    global current_room
    if answer == '✅Да' or answer.lower() == 'да':
        userid = update.message.chat_id
        iid = current_images[userid][current_image[userid]]['Image'].get('id')
        answer = delete(f'{config.API_ADDRESS}/api/images/{iid}').json()
        rid = current_rooms[userid][current_room[userid]]['Room']['id']
        current_rooms[userid][current_room[userid]] = get(f'{config.API_ADDRESS}/api/rooms/{rid}').json()
        current_images[userid][current_image[userid]] = None
        if not answer or answer.get('error'):
            logging.error(f'During /rooms API\'s sent error: {answer.get("error")}')
            update.message.reply_text('😿Произошла ошибка на сервере.\nРекомендуем вам подождать немного, '
                                      'скоро все наладится!')
            return 9
        update.message.reply_text('ℹ️Изображение было успешно удалено!')
        show_room(update, context, current_room[update.message.chat_id])
    else:
        show_room(update, context, current_room[update.message.chat_id], refresh=False)
    return 5


def image_get(update, context):
    file_info = context.bot.get_file(update.message.photo[0].file_id)
    file = bytes(file_info.download_as_bytearray())
    base64_data = base64.b64encode(file).decode('utf-8')


def choose_filter(update, context):  # 2nd in Conversation
    pass


def save_image_to_room(update, context):  # 3rd in Conversation
    pass


def choose_room(update, context):  # 4th in Context
    pass


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
            7: [MessageHandler(Filters.text, image)],
            8: [MessageHandler(Filters.text, command_image)],
            9: [MessageHandler(Filters.text, delete_image)]
        },

        fallbacks=[CommandHandler('home', home)]

    )

    image_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.photo, image_get)],

        states={
            1: [MessageHandler(Filters.text, choose_filter)],
            2: [MessageHandler(Filters.text, save_image_to_room)],
            3: [MessageHandler(Filters.text, choose_room)]
        },

        fallbacks=[CommandHandler('home', home)]
    )
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(rooms_conv_handler)
    dp.add_handler(image_conv_handler)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
