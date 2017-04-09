# coding=utf-8
from pytg.sender import Sender
from pytg.receiver import Receiver
from pytg.utils import coroutine
from collections import deque
from time import time, sleep
from getopt import getopt
import sys
import datetime as dt
import re
import _thread
import random

# username игрового бота
bot_username = 'ChatWarsBot'

stock_bot = 'WarChatsEquip_bot'

# ваш username или username человека, который может отправлять запросы этому скрипту
admin_username = ''

# username бота и/или человека, которые будут отправлять приказы
order_usernames = ''

# имя замка
castle_name = 'blue'

captcha_bot = 'ChatWarsCaptchaBot'

# хост чтоб слушать telegram-cli
host = 'localhost'

# порт по которому слушать
port = 1338

opts, args = getopt(sys.argv[1:], 'a:o:c:s:h:p', ['admin=', 'order=', 'castle=', 'socket=', 'host=', 'port='])

for opt, arg in opts:
    if opt in ('-a', '--admin'):
        admin_username = arg
    elif opt in ('-o', '--order'):
        order_usernames = arg.split(',')
    elif opt in ('-c', '--castle'):
        castle_name = arg
    elif opt in ('-s', '--socket'):
        socket_path = arg
    elif opt in ('-h', '--host'):
        host = arg
    elif opt in ('-p', '--port'):
        port = int(arg)

orders = {
    'red': '🇮🇲',
    'black': '🇬🇵',
    'white': '🇨🇾',
    'yellow': '🇻🇦',
    'blue': '🇪🇺',
    'lesnoi_fort': '🌲Лесной форт',
    'les': '🌲Лес',
    'gorni_fort': '⛰Горный форт',
    'gora': '⛰',
    'cover': '🛡 Защита',
    'attack': '⚔ Атака',
    'cover_symbol': '🛡',
    'hero': '🏅Герой',
    'corovan': '/go',
    'peshera': '🕸Пещера',
    'taverna': '🍺Взять кружку эля'
}

captcha_answers = {
    'watermelon_n_cherry': '🍉🍒',
    'bread_n_cheese': '🍞🧀',
    'cheese': '🧀',
    'pizza': '🍕',
    'hotdog': '🌭',
    'eggplant_n_carrot': '🍆🥕',
    'dog': '🐕',
    'horse': '🐎',
    'goat': '🐐',
    'cat': '🐈',
    'pig': '🐖',
    'squirrel': '🐿'
}

states_map = {
    'relax': '🛌Отдых',
    'defense': '🛡Защита',
    'attack': '⚔Атака',
    'arena': '📯На арене',
    'les': '🌲В лесу',
    'peshera': '🕸В пещере',
    'taverna': '🍺Пьешь в таверне'
}

arena_cover = ['🛡головы', '🛡корпуса', '🛡ног']
arena_attack = ['🗡в голову', '🗡по корпусу', '🗡по ногам']
# поменять blue на red, black, white, yellow в зависимости от вашего замка
castle = orders[castle_name]
# текущий приказ на атаку/защиту, по умолчанию всегда защита, трогать не нужно
current_order = {'time': 0, 'order': castle}

sender = Sender(host=host, port=port)
action_list = deque([])
log_list = deque([], maxlen=30)
get_info_diff = 360
hero_message_id = 0
last_captcha_id = 0

enabled_list = {
    'bot': True,
    'arena': True,
    'taverna': True,
    'les': True,
    'peshera': False,
    'corovan': True,
    'order': True,
    'auto_def': True,
    'donate': False,
    'sell': True
}

last_time = {
    'info': time() - 60*60,
    'arena': time() - 60*60,
    'sell': time() - 60*60
}

@coroutine
def work_with_message(receiver):
    while True:
        msg = (yield)
        try:
            if msg['event'] == 'message' and 'text' in msg and msg['peer'] is not None \
                    and int(time()+1) - int(msg['date']) < 5:
                parse_text(msg['text'], msg['sender']['username'], msg['id'])
        except Exception as err:
            log('Ошибка coroutine: {0}'.format(err))


def queue_worker():
    global get_info_diff
    global last_time
    sender.dialog_list()
    sleep(3)
    while True:
        try:

            if time() - last_time['info'] > get_info_diff:
                last_time['info'] = time()
                get_info_diff = random.randint(400, 600)
                if enabled_list['bot']:
                    send_msg(bot_username, orders['hero'])
                continue

            if len(action_list):
                log('Отправляем ' + action_list[0])
                send_msg(bot_username, action_list.popleft())
            sleep_time = random.randint(2, 6)
            sleep(sleep_time)
        except Exception as err:
            log('Ошибка очереди: {0}'.format(err))


def parse_text(text, username, message_id):
    global last_time
    global hero_message_id
    global enabled_list
    global last_captcha_id
    if username == bot_username:
        log('Получили сообщение от бота. Проверяем условия')

        if "На выходе из замка охрана никого не пропускает" in text:
            with open('captcha.txt', 'a+') as f:
                f.seek(0)
                for line in f:
                    if text in line:
                        break
                else:
                    f.write(text + '\n' + '-' * 8 + '\n')

            action_list.clear()
            last_captcha_id = message_id
            fwd(captcha_bot, message_id)
            enabled_list['bot'] = False

        elif 'Не умничай!' in text or 'Ты долго думал, аж вспотел от напряжения' in text or 'Не шути со стражниками' in text:
            send_msg(admin_username, "Командир, у нас проблемы с капчой! #captcha " + '|'.join(captcha_answers.keys()))
            enabled_list['bot'] = False
            if last_captcha_id != 0:
                fwd(admin_username, last_captcha_id)
            else:
                send_msg(admin_username, 'Капча не найдена?')

        elif 'Ты слишком устал, возвращайся когда отдохнешь.' in text:
            send_msg(admin_username, "Не угадали с капчей, вырубаю бота")
            enabled_list['bot'] = False

        elif 'Ты ответил правильно' in text:
            enabled_list['bot'] = True

        if enabled_list['bot']:
            if enabled_list['corovan'] and text.find(' /go') != -1:
                action_list.append(orders['corovan'])

            elif text.find('Сражаться можно не чаще чем один раз в час.') != -1:
                last_time['arena'] = time() - 15 * 60
                last_time['info'] = time()
                action_list.append(orders['hero'])

            elif text.find('[невозможно выполнить данную операцию]') != -1 and enabled_list['sell']:
                enabled_list['sell'] = False
                send_msg(admin_username, 'Закончились нитки :(')

            elif text.find('Битва пяти замков через') != -1:
                last_time['info'] = time()
                hero_message_id = message_id
                m = re.search('Битва пяти замков через(?: ([0-9]+)ч){0,1}(?: ([0-9]+)){0,1}', text)
                state = re.search('Состояние:\\n(.*)\\n', text)
                if not m.group(1):
                    if m.group(2) and int(m.group(2)) <= 30:
                        if enabled_list['auto_def'] and time() - current_order['time'] > 3600:
                            if enabled_list['donate']:
                                gold = int(re.search('💰([0-9]+)', text).group(1))
                                log('Донат {0} золота в казну замка'.format(gold))
                                action_list.append('/donate {0}'.format(gold))
                            update_order(castle)
                        return
                if states_map['relax'] not in state.group(1) and states_map['defense'] not in state.group(1) and \
                                states_map['attack'] not in state.group(1):
                    return

                log('Времени достаточно')
                gold = int(re.search('💰([0-9]+)', text).group(1))
                endurance = int(re.search('Выносливость: ([0-9]+)', text).group(1))
                log('Золото: {0}, выносливость: {1}'.format(gold, endurance))

                if text.find('/level_up') != -1 and '/level_up' not in action_list:
                    damage = int(re.search('Атака: ([0-9]+)', text).group(1))
                    defence = int(re.search('Защита: ([0-9]+)', text).group(1))
                    action_list.append('/level_up')
                    log('level_up')
                    if damage > defence:
                        action_list.append('+1 ⚔Атака')
                    else:
                        action_list.append('+1 🛡Защита')

                if enabled_list['peshera'] and endurance >= 2 and orders['peshera'] not in action_list:
                    action_list.append(orders['peshera'])

                elif enabled_list['les'] and endurance >= 1 and orders['les'] not in action_list:
                    action_list.append(orders['les'])

                elif enabled_list['arena'] and '🔎Поиск соперника' not in action_list and time() - last_time['arena'] > 3600:
                    if gold >= 5:
                        action_list.append('🔎Поиск соперника')
                    elif enabled_list['sell'] and time() - last_time['sell'] > 3000:
                        action_list.append('/s_101 ' + str((6 - gold) // 2))
                        last_time['sell'] = time()
                        action_list.append('🔎Поиск соперника')

                elif enabled_list['taverna'] and gold >= 20 and orders['taverna'] not in action_list and \
                        (dt.datetime.now().time() >= dt.time(19) or dt.datetime.now().time() < dt.time(6)):
                    action_list.append(orders['taverna'])

            elif enabled_list['arena'] and text.find('выбери точку атаки и точку защиты') != -1:
                last_time['arena'] = time()
                attack_chosen = arena_attack[random.randint(0, 2)]
                cover_chosen = arena_cover[random.randint(0, 2)]
                log('Атака: {0}, Защита: {1}'.format(attack_chosen, cover_chosen))
                action_list.append(attack_chosen)
                action_list.append(cover_chosen)

            elif text.find('Победил воин') != -1:
                fwd('BlueOysterBot', message_id)

            elif text.find('Содержимое склада') != -1:
                fwd(stock_bot, message_id)

            elif "Хорошо!" not in text and "Хороший план" not in text and "5 минут" not in text and \
                            "Ты сейчас занят" not in text and "Ветер завывает" not in text and \
                            "Соперник найден" not in text and "Синий замок" not in text and \
                            "Синего замка" not in text and "Общение внутри замка" not in text and \
                            "Победил воин" not in text and not re.findall(r'\bнанес\b(.*)\bудар\b', text):
                with open('taverna.txt', 'a+') as f:
                    f.seek(0)
                    for line in f:
                        if text[0:8] in line:
                            break
                    else:
                        f.write(text + '\n')
                action_list.append(orders['hero'])
                last_time['info'] = time()

    elif username == 'ChatWarsCaptchaBot':
        if len(text) <= 4 and text in captcha_answers.values():
            sleep(3)
            action_list.clear()
            action_list.append(text)
            enabled_list['bot'] = True

    else:
        if enabled_list['bot'] and enabled_list['order'] and username in order_usernames:
            if text.find(orders['red']) != -1:
                update_order(orders['red'])
            elif text.find(orders['black']) != -1:
                update_order(orders['black'])
            elif text.find(orders['white']) != -1:
                update_order(orders['white'])
            elif text.find(orders['yellow']) != -1:
                update_order(orders['yellow'])
            elif text.find(orders['blue']) != -1:
                update_order(orders['blue'])
            elif text.find('🌲') != -1:
                update_order(orders['lesnoi_fort'])
            elif text.find('⛰') != -1:
                update_order(orders['gorni_fort'])
            elif text.find('🛡') != -1:
                update_order(castle)

                # send_msg(admin_username, 'Получили команду ' + current_order['order'] + ' от ' + username)
        if username == "Telegram":
            fwd(admin_username, message_id)

        if username == admin_username:
            if text == '#help':
                send_msg(admin_username, '\n'.join([
                    '#enable_bot - Включить бота',
                    '#disable_bot - Выключить бота',
                    '#enable_arena - Включить арену',
                    '#disable_arena - Выключить арену',
                    '#disable_taverna - Выключить таверну',
                    '#enable_taverna - Включить таверну',
                    '#enable_sell - Включить продажу ниток',
                    '#disable_sell - Выключить продажу ниток',
                    '#enable_les - Включить лес',
                    '#disable_les - Выключить лес',
                    '#enable_peshera - Включить пещеры',
                    '#disable_peshera - Выключить пещеры',
                    '#enable_corovan - Включить корован',
                    '#disable_corovan - Выключить корован',
                    '#enable_order - Включить приказы',
                    '#disable_order - Выключить приказы',
                    '#enable_auto_def - Включить авто деф',
                    '#disable_auto_def - Выключить авто деф',
                    '#enable_donate - Включить донат',
                    '#disable_donate - Выключить донат',
                    '#update_stock - обновить сток',
                    '#status - Получить статус',
                    '#hero - Получить информацию о герое',
                    '#push_order - Добавить приказ ({0})'.format(','.join(orders)),
                    '#order - Дебаг, последняя команда защиты/атаки замка',
                    '#log - Дебаг, последние 30 сообщений из лога',
                    '#time - Дебаг, текущее время',
                    '#last_time[...] - Дебаг, последняя битва на арене',
                    '#get_info_diff - Дебаг, последняя разница между запросами информации о герое',
                    '#ping - Дебаг, проверить жив ли бот',
                ]))

            # Вкл/выкл бота
            elif text == '#enable_bot':
                enabled_list['bot'] = True
                send_msg(admin_username, 'Бот успешно включен')
            elif text == '#disable_bot':
                enabled_list['bot'] = False
                send_msg(admin_username, 'Бот успешно выключен')

            elif text == '#enable_sell':
                enabled_list['sell'] = True
                send_msg(admin_username, 'Продажа ниток влючена')
            elif text == '#disable_sell':
                enabled_list['sell'] = False
                send_msg(admin_username, 'Продажа ниток выключена')

            # Вкл/выкл арены
            elif text == '#enable_arena':
                enabled_list['arena'] = True
                send_msg(admin_username, 'Арена успешно включена')
            elif text == '#disable_arena':
                enabled_list['arena'] = False
                send_msg(admin_username, 'Арена успешно выключена')

            # Вкл/выкл таверны
            elif text == '#enable_taverna':
                enabled_list['taverna'] = True
                send_msg(admin_username, 'Таверна успешно включена')
            elif text == '#disable_taverna':
                enabled_list['taverna'] = False
                send_msg(admin_username, 'Таверна успешно выключена')

            # Вкл/выкл леса
            elif text == '#enable_les':
                enabled_list['les'] = True
                send_msg(admin_username, 'Лес успешно включен')
            elif text == '#disable_les':
                enabled_list['les'] = False
                send_msg(admin_username, 'Лес успешно выключен')

            # Вкл/выкл пещеры
            elif text == '#enable_peshera':
                enabled_list['peshera'] = True
                send_msg(admin_username, 'Пещера успешно включена')
            elif text == '#disable_peshera':
                enabled_list['peshera'] = False
                send_msg(admin_username, 'Пещера успешно выключена')

            # Вкл/выкл корована
            elif text == '#enable_corovan':
                enabled_list['corovan'] = True
                send_msg(admin_username, 'Корованы успешно включены')
            elif text == '#disable_corovan':
                enabled_list['corovan'] = False
                send_msg(admin_username, 'Корованы успешно выключены')

            # Вкл/выкл команд
            elif text == '#enable_order':
                enabled_list['order'] = True
                send_msg(admin_username, 'Приказы успешно включены')
            elif text == '#disable_order':
                enabled_list['order'] = False
                send_msg(admin_username, 'Приказы успешно выключены')

            # Вкл/выкл авто деф
            elif text == '#enable_auto_def':
                enabled_list['auto_def'] = True
                send_msg(admin_username, 'Авто деф успешно включен')
            elif text == '#disable_auto_def':
                enabled_list['auto_def'] = False
                send_msg(admin_username, 'Авто деф успешно выключен')

            # Вкл/выкл авто донат
            elif text == '#enable_donate':
                enabled_list['donate'] = True
                send_msg(admin_username, 'Донат успешно включен')
            elif text == '#disable_donate':
                enabled_list['donate'] = False
                send_msg(admin_username, 'Донат успешно выключен')

            elif text == '#update_stock':
                action_list.append('/stock')

            # Получить статус
            elif text == '#status':
                send_msg(admin_username, '\n'.join([
                    'Бот включен: {0}',
                    'Арена включена: {1}',
                    'Лес включен: {2}',
                    'Пещера включена: {3}',
                    'Корованы включены: {4}',
                    'Приказы включены: {5}',
                    'Авто деф включен: {6}',
                    'Донат включен: {7}',
                    'Таверна включена: {8}',
                    'Продажа ниток: {9}',
                ]).format(enabled_list['bot'], enabled_list['arena'], enabled_list['les'], enabled_list['peshera'], enabled_list['corovan'], enabled_list['order'],
                          enabled_list['auto_def'], enabled_list['donate'], enabled_list['taverna'], enabled_list['sell']))

            # Информация о герое
            elif text == '#hero':
                if hero_message_id == 0:
                    send_msg(admin_username, 'Информация о герое пока еще недоступна')
                else:
                    fwd(admin_username, hero_message_id)

            # Получить лог
            elif text == '#log':
                send_msg(admin_username, '\n'.join(log_list))
                log_list.clear()

            elif text == '#last_time':
                send_msg(admin_username, str(dt.datetime.fromtimestamp(last_time['arena']).time()))

            elif text == '#order':
                text_date = str(dt.datetime.fromtimestamp(current_order['time']).time())
                send_msg(admin_username, current_order['order'] + ' ' + text_date)

            elif text == '#time':
                text_date = str(dt.datetime.now().time())
                send_msg(admin_username, text_date)

            elif text == '#ping':
                send_msg(admin_username, '#pong')

            elif text == '#get_info_diff':
                send_msg(admin_username, str(get_info_diff))

            elif text.startswith('#push_order'):
                command = text.split(' ')[1]
                if command in orders:
                    update_order(orders[command])
                    send_msg(admin_username, 'Команда ' + command + ' применена')
                else:
                    send_msg(admin_username, 'Команда ' + command + ' не распознана')

            elif text.startswith('#captcha'):
                command = text.split(' ')[1]
                if command in captcha_answers:
                    action_list.clear()
                    action_list.append(captcha_answers[command])
                    enabled_list['bot'] = True
                    send_msg(admin_username, 'Команда ' + command + ' применена')
                else:
                    send_msg(admin_username, 'Команда ' + command + ' не распознана')


def send_msg(to, message):
    sender.mark_read('@' + to)
    sender.send_msg('@' + to, message)


def fwd(to, message_id):
    sender.fwd('@' + to, message_id)


def update_order(order):
    current_order['order'] = order
    current_order['time'] = time()
    if order == castle:
        action_list.append(orders['cover'])
    else:
        action_list.append(orders['attack'])
    action_list.append(order)


def log(text):
    message = '{0:%Y-%m-%d %H:%M:%S}'.format(dt.datetime.now()) + ' ' + text
    print(message)
    log_list.append(message)


if __name__ == '__main__':
    receiver = Receiver(port=port)
    receiver.start()
    _thread.start_new_thread(queue_worker, ())
    receiver.message(work_with_message(receiver))
    receiver.stop()
