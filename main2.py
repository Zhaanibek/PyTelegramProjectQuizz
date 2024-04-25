# -*- coding: utf-8 -*-

import os
import time
from dotenv import load_dotenv
import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from messages import start_message, help_message, record_message, restart_message, ended_message
from quiz_data import question_list, option_list

load_dotenv()

token = os.environ.get("TOKEN")
bot = telebot.TeleBot(token)


user_states = {}


@bot.message_handler(commands=["start"])
def start_command_handler(message: Message):
    user_states[message.chat.id] = {
        'user_name': message.from_user.first_name,
        'correct_answers': 0,
        'current_question': 0,
        'start_time': None
    }

    bot.send_message(
        chat_id=message.chat.id,
        text=start_message
    )


@bot.message_handler(commands=["help"])
def help_command_handler(message: Message):
    bot.send_message(
        chat_id=message.chat.id,
        text=help_message
    )


@bot.message_handler(commands=["start_quiz"])
def start_quiz_command_handler(message: Message):
    if message.chat.id in user_states:
        user_states[message.chat.id]['start_time'] = time.time()
        ask_question(message.chat.id)
    else:
        bot.send_message(
            chat_id=message.chat.id,
            text=restart_message
        )


def ask_question(chat_id):
    current_question = user_states[chat_id]['current_question']

    if 0 <= current_question < len(question_list):
        question_data = question_list[current_question]
        q_text = f"{current_question + 1}. {question_data['question']}"
        markup = InlineKeyboardMarkup(row_width=2)
        btns = []

        for i, option in enumerate(question_data['options']):
            btn = InlineKeyboardButton(text=option, callback_data=option_list[i])
            btns.append(btn)

        markup.add(*btns)

        bot.send_message(
            chat_id=chat_id,
            text=q_text,
            reply_markup=markup
        )
    else:

        bot.send_message(
            chat_id=chat_id,
            text=ended_message
        )


@bot.callback_query_handler(func=lambda call: call.data in option_list)
def callback_handler(call: CallbackQuery):
    chat_id = call.message.chat.id
    if chat_id in user_states:
        current_question = user_states[chat_id]['current_question']

        old_question_data = question_list[current_question]
        if old_question_data['correct_option'] == call.data:
            user_states[chat_id]['correct_answers'] += 1
            bot.answer_callback_query(callback_query_id=call.id, text="Правильно!")
        else:
            bot.answer_callback_query(callback_query_id=call.id, text="Не правильно!")

        user_states[chat_id]['current_question'] += 1

        if user_states[chat_id]['current_question'] >= len(question_list):
            display_results(chat_id)
            return

        ask_question(chat_id)
    else:
        bot.send_message(
            chat_id=chat_id,
            text=restart_message
        )


def display_results(chat_id):
    correct_answers = user_states[chat_id]['correct_answers']
    start_time = user_states[chat_id]['start_time']

    end_time = time.time()
    elapsed_time = round(end_time - start_time)

    user_name = user_states[chat_id].get('user_name', 'Unknown')

    bot.send_message(
        chat_id=chat_id,
        text=f"Конец!\nПользователь: {user_name}\nПравильных ответов: {correct_answers}\nЗатраченное время:"
             f" {elapsed_time} секунд"
    )

    update_global_stats(chat_id, user_name, correct_answers, elapsed_time)


def update_global_stats(chat_id, user_name, correct_answers, elapsed_time):

    if 'global_stats' not in user_states:
        user_states['global_stats'] = []

    user_states['global_stats'].append({
        'user_id': chat_id,
        'user_name': user_name,
        'correct_answers': correct_answers,
        'elapsed_time': elapsed_time
    })


@bot.message_handler(commands=["record_table"])
def record_table_command_handler(message: Message):
    if 'global_stats' in user_states and user_states['global_stats']:

        sorted_stats = sorted(user_states['global_stats'], key=lambda x: (x['correct_answers'], -x['elapsed_time']),
                              reverse=True)

        table_text = "Таблица лучших результатов:\n"
        for i, user_stat in enumerate(sorted_stats[:10], start=1):
            table_text += (f"{i}. Пользователь {user_stat['user_name']} - Правильных ответов:"
                           f" {user_stat['correct_answers']}, Время: {user_stat['elapsed_time']} сек\n")

        bot.send_message(
            chat_id=message.chat.id,
            text=table_text
        )
    else:
        bot.send_message(
            chat_id=message.chat.id,
            text=record_message
        )


bot.polling()
