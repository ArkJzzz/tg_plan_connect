#!/usr/bin/python3
__author__ = 'ArkJzzz (arkjzzz@gmail.com)'

# Import
import os
import logging
import textwrap
import requests
import datetime
import sys

import telegram
from telegram import ParseMode
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import ConversationHandler
from bs4 import BeautifulSoup
from selenium import webdriver
from dotenv import load_dotenv

import moncms_parser
import sqlite_helpers
import ext_helpers


logger = logging.getLogger('plan_connect_bot')

REMINDING_TIME_HOUR = 8
REMINDING_TIME_MINUTE = 0

REMINDING_TIME_HOUR = REMINDING_TIME_HOUR - 3, # MSK



def add_user_to_db(update, context):
    chat_id = update.message.chat_id
    logger.debug(context.args)
    admin_chat_id = os.getenv('ADMIN_CHAT_ID')

    if int(chat_id) == int(admin_chat_id):
        try:
            tg_id, moncms_worker_id, = context.args[:2]
            worker_name = ' '.join(context.args[2:])
            logger.debug(f'{tg_id}, {moncms_worker_id}, {worker_name}')
            sqlite_helpers.add_worker_to_db(
                    tg_id=tg_id,
                    moncms_worker_id=moncms_worker_id,
                    worker_name=worker_name,
                )
            successfull_message = f'''
                В базу успешно добавлен пользователь:
                ({tg_id}, {moncms_worker_id}, {worker_name})
            '''
            update.message.reply_text(
                    text = textwrap.dedent(successfull_message),
                )
        except Exception as err:
            logger.debug(err)
            error_message = '''
                Usage:
                /add_user <tg_id> <moncms_worker_id> <worker full name>
            '''
            update.message.reply_text(
                    text = textwrap.dedent(error_message),
                )


def del_user_from_db(update, context):
    chat_id = update.message.chat_id
    logger.debug(context.args)
    admin_chat_id = os.getenv('ADMIN_CHAT_ID')

    if int(chat_id) == int(admin_chat_id):
        try:
            tg_id = int(context.args[0])
            logger.debug(tg_id)
            sqlite_helpers.del_worker_from_db(tg_id)
            successfull_message = f'Пользователь {tg_id} удален'
            update.message.reply_text(
                    text = textwrap.dedent(successfull_message),
                )
        except Exception as err:
            logger.debug(err)
            error_message = '''
                Usage:
                /del_user <tg_id>
            '''
            update.message.reply_text(
                    text = textwrap.dedent(error_message),
                )





def send_work_tasks(context):
    logger.debug('send_work_task')
    user_chat_id = context.job.context

    exits_links = moncms_parser.get_exits_links(
            date_from=None, 
            date_to=None,
        )

    user_moncms_id = sqlite_helpers.get_user_moncms_id(user_chat_id)

    for link in exits_links:
        plan_connect_data = moncms_parser.get_plan_connect_data(link)
        workers = plan_connect_data['workers']
        if user_moncms_id in workers:
            task = ext_helpers.get_formated_task(plan_connect_data)

            logger.debug(task)

            context.bot.send_message(
                chat_id=user_chat_id,
                text=task,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
    context.bot.send_message(
        chat_id=user_chat_id,
        text='На этом пока что все.',
    )


def check_autorization(tg_id):
    authorized_tg_ids = sqlite_helpers.get_tg_ids()
    logger.debug(authorized_tg_ids)

    if tg_id in authorized_tg_ids:
        return True


def start(update, context):
    user_chat_id = update.message.chat_id
    
    if check_autorization(user_chat_id):
        welcome_message = '''
                Теперь ты будешь получать назначенные задания сюда
            '''
        update.message.reply_text(
            text=textwrap.dedent(welcome_message),
        )

        context.job_queue.run_once(
            callback=send_work_tasks, 
            when=3,
            context=user_chat_id
        )

        reminding_time = datetime.time(
                REMINDING_TIME_HOUR, 
                REMINDING_TIME_MINUTE,
            )

        context.job_queue.run_daily(
            callback=send_work_tasks, 
            time=reminding_time,
            days=(0, 1, 2, 3, 4),
            context=user_chat_id
        )

    else:
        not_autorized_message = '''
                Для использования бота необходима авторизация: 
                1. Необходимо написать боту @userinfobot;
                2. Переслать его ответ пользователю @ArkJzzz;
                3. Ждать дальнейших инструкций.
            '''
        update.message.reply_text(
            text=textwrap.dedent(not_autorized_message),
        )


def error_handler(update, context):
    message = f'''\
            Exception while handling an update:
            {context.error}
        '''
    logger.error(message, exc_info=context.error)

    context.bot.send_message(
        chat_id=os.getenv('ADMIN_CHAT_ID'), 
        text=textwrap.dedent(message),
    )


def main():
    formatter = logging.Formatter(
            fmt='%(asctime)s %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%b-%d %H:%M:%S (%Z)',
            style='%',
        )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(f'{__file__}.log')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)

    moncms_parser_logger = logging.getLogger('moncms_parser')
    moncms_parser_logger.addHandler(console_handler)
    moncms_parser_logger.setLevel(logging.DEBUG)

    ext_helpers_logger = logging.getLogger('ext_helpers')
    ext_helpers_logger.addHandler(console_handler)
    ext_helpers_logger.setLevel(logging.DEBUG)

    sqlite_helpers_logger = logging.getLogger('sqlite_helpers')
    sqlite_helpers_logger.addHandler(console_handler)
    sqlite_helpers_logger.setLevel(logging.DEBUG)

    load_dotenv()
    telegram_token = os.getenv('TELEGRAM_TOKEN')

    updater = Updater(
        token=telegram_token,
        use_context=True, 
    )
    

    start_handler = CommandHandler('start', start)
    add_user_handler = CommandHandler('add_user', add_user_to_db)
    del_user_handler = CommandHandler('del_user', del_user_from_db)


    dispatcher = updater.dispatcher
    job_queue = updater.job_queue

    dispatcher.add_error_handler(error_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(add_user_handler)
    dispatcher.add_handler(del_user_handler)


    try:
        logger.debug('Запускаем бота')
        updater.start_polling()

    except telegram.error.NetworkError:
        logger.error('Не могу подключиться к telegram')
    except Exception  as err:
        logger.error('Бот упал с ошибкой:')
        logger.error(err)
        logger.debug(err, exc_info=True)

    updater.idle()
    logger.info('Бот остановлен') 




if __name__ == '__main__':
    main()

