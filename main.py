import telebot
import sqlite3
from config import *
from api import *
import schedule
import time
from threading import Thread

bot = telebot.TeleBot(TELEGRAM_API_KEY)
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц 

# Таблица пользователя 
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT
                  )''')
conn.commit()

# Таблица уведомление 
cursor.execute('''CREATE TABLE IF NOT EXISTS user_thresholds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    coin_id INTEGER,
                    top_level REAL,
                    current_lvl REAL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
                  )''')
conn.commit()

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username

    # Создание пользователя в базе данных, если его ещё нет
    cursor.execute('INSERT OR IGNORE INTO users (user_id, first_name, last_name, username) VALUES (?, ?, ?, ?)', 
                   (user_id, first_name, last_name, username))
    conn.commit()

    bot.send_message(message.chat.id, f"Привет, {first_name}!\nДобро пожаловать в бота для отслеживания курса криптовалют")

    coins = get_top_crypto()
    top_coins = coins[:10]
    message_text = "**Для начала давай выберем интересные для вас монеты:**\n" + \
               "\n".join([f"Название: *{coin['name']}*, Стоимость в USD: {coin['quote']['USD']['price']}" for coin in top_coins])

    bot.send_message(message.chat.id, message_text, parse_mode='Markdown')
    bot.send_message(message.chat.id, "Введи название монеты из списка или название любой другой монеты (Для дальнейшего добавления просто отправляйте название монеты)")

    @bot.message_handler(func=lambda message: True)
    def handle_coin_name(message):
        nonlocal user_id, coins

        coin_name = message.text.strip()
        coin_id = get_coin_id_by_name(coin_name, coins)

        if coin_id is not None:
            bot.send_message(message.chat.id, f"Вы выбрали монету {coin_name}. Теперь введите пороговый курс для отслеживания.")
            bot.register_next_step_handler(message, lambda msg: handle_threshold(msg, user_id, coin_id))
        else:
            bot.send_message(message.chat.id, f"Монета с названием {coin_name} не найдена. Попробуйте ещё раз.")

    def handle_threshold(message, user_id, coin_id):
        threshold = message.text.strip()
        coin = get_coin_by_id(coin_id)
        current_lvl = coin['quote']['USD']['price']
        name = coin['name']
        try:
            threshold = float(threshold)
            cursor.execute('INSERT INTO user_thresholds (user_id, coin_id, top_level, current_lvl) VALUES (?, ?, ?, ?)',
                           (user_id, coin_id, threshold, current_lvl))
            conn.commit()
            bot.send_message(message.chat.id, f"Пороговый курс {threshold} для монеты {name} успешно сохранён.")
        except ValueError:
            bot.send_message(message.chat.id, "Пожалуйста, введите числовое значение порогового курса.")

# Функция отправки уведомлений
def check_thresholds():
    cursor.execute('SELECT id, user_id, coin_id, top_level, current_lvl FROM user_thresholds')
    thresholds = cursor.fetchall()

    for id, user_id, coin_id, top_level, current_lvl in thresholds:
        coin = get_coin_by_id(coin_id)
        current_price = coin['quote']['USD']['price']
        name = coin['name']
        should_notify = False
        if current_lvl < top_level and current_price >= top_level:
            should_notify = True
        elif current_lvl > top_level and current_price <= top_level:
            should_notify = True
        if should_notify:
            bot.send_message(user_id, f"Цена монеты {name} достигла порогового значения: {top_level} USD")
            cursor.execute('DELETE FROM user_thresholds WHERE id = ?', (id,))
            conn.commit()



def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    schedule.every(1).minutes.do(check_thresholds)
    Thread(target=schedule_checker).start()
    bot.polling(none_stop=True)

if __name__ == '__main__':
    main()