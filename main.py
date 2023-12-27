import os
import random

import telebot
from dotenv import load_dotenv
from telebot import types
from sqlalchemy.orm import sessionmaker

from database import User, engine

load_dotenv()
# Replace 'YOUR_BOT_TOKEN' with your actual bot token
TOKEN = os.environ.get("TOKEN")


class Problem:
    def __init__(self):
        self.first = random.randint(1, 10)
        self.second = random.randint(1, 10)
        self.result = self.first * self.second

    def __str__(self):
        return f"{self.first} x {self.second}"

    def __repr__(self):
        return f"{self.first} x {self.second}"


# Create a telebot instance
bot = telebot.TeleBot(TOKEN)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()


def get_or_create_user(uid: int) -> User:
    existing = session.query(User).filter_by(user_id=uid).first()
    if existing is None:
        db_user = User(user_id=uid, status="user", balance=0.00)
        session.merge(db_user)
        session.commit()
    return existing


def update_balance(user: User):
    user.balance += 0.1
    session.merge(user)
    session.commit()


@bot.message_handler(commands=["start"])
def start_message(message: types.Message):
    user = message.from_user
    get_or_create_user(user.id)
    ns = f", {user.username}" if user.username is not None or user.username != "" else ""
    bot.reply_to(message, f"Привет{ns}! Чтобы начать введи команду /practice")


@bot.message_handler(commands=["practice"])
def practice(message: types.Message):
    uid = message.from_user.id
    user = get_or_create_user(uid)
    problem = Problem()
    user.problem_ans = problem.result
    session.merge(user)
    session.commit()
    markup: types.InlineKeyboardMarkup = types.InlineKeyboardMarkup()
    button_stop: types.InlineKeyboardButton = types.InlineKeyboardButton(text="Остановить",
                                                                         callback_data="stop_practice")
    markup.add(button_stop)
    bot.send_message(uid, f"Сколько будет:\n{problem}", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "stop_practice")
def stop_practice_callback_handler(callback_query: types.CallbackQuery):
    uid = callback_query.from_user.id
    user = get_or_create_user(uid)
    user.problem_ans = -1
    session.merge(user)
    session.commit()
    bot.send_message(uid, f"Ты остановил решение примеров.\n\nВсего решено "
                          f"примеров: {user.total_answered} из них {user.correct_answered} правильно."
                          f"\n\nВ среднем ты ошибаешься {0 if user.total_answered == 0 else (int(user.correct_answered / user.total_answered) - 1) * 10} раз на 10 примеров."
                          f"\n\nТы накопил: {user.balance:.2f}₽\n\nЧтобы продолжить решать примеры нажми /practice")


@bot.message_handler(func=lambda msg: get_or_create_user(msg.from_user.id).problem_ans != -1)
def check_answer(message: types.Message) -> None:
    user_answer: str = message.text
    uid = message.from_user.id
    user = get_or_create_user(uid)
    try:
        user_answer: int = int(user_answer)
        correct_answer: int = user.problem_ans
        user.total_answered += 1
        if user_answer == correct_answer:
            user.correct_answered += 1
            update_balance(user)
            bot.send_message(message.chat.id, f"Правильно! Ты накопил: {user.balance:.2f}₽")
        else:
            bot.reply_to(message, f"Неправильно, ответ был {correct_answer}")
        practice(message)
    except ValueError:
        bot.reply_to(message, "Ты ввел неправильно число.")


@bot.message_handler(commands=["checkout"])
def checkout(message: types.Message):
    uid = message.from_user.id
    user = get_or_create_user(uid)
    if user.status == "admin":
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "Неверное использование команды")
        subject_user = get_or_create_user(int(args[1]))
        if subject_user.balance >= int(args[2]):
            subject_user.balance -= int(args[2])
            session.merge(subject_user)
            session.commit()
        else:
            bot.reply_to(message, "Неверное использование команды")
        bot.reply_to(message, f"Вы обналичили пользователя {subject_user.balance}, сумма: {args[2]}")


@bot.message_handler(commands=["users"])
def checkout(message: types.Message):
    uid = message.from_user.id
    user = get_or_create_user(uid)
    if user.status == "admin":
        users = session.query(User).all()
        response = "UID      BAL   TOT\n"
        for res in users:
            response += f"{res.user_id}\t{res.balance}\t{res.total_answered}\n"
        bot.reply_to(message, response)


bot.polling(none_stop=True)
