#!/usr/bin/python3
__author__ = 'ArkJzzz (arkjzzz@gmail.com)'


import os
import logging
import sqlite3


logger = logging.getLogger('sqlite_helpers')


DB_NAME = 'plan_connect.db'


def add_worker_to_db(tg_id, moncms_worker_id, worker_name):
    db_connection = sqlite3.connect(DB_NAME)
    with db_connection:
        cursor = db_connection.cursor()
        user = (tg_id, moncms_worker_id, worker_name)

        cursor.execute('INSERT INTO workers VALUES(?, ?, ?);', user)
        logger.debug(f'в таблицу "workers" добавлена запись {user}')

        cursor.execute('SELECT * FROM workers;')
        all_results = cursor.fetchall()
        logger.info(f'Все записи:\n{all_results}')

        db_connection.commit()


def del_worker_from_db(tg_id):
    db_connection = sqlite3.connect(DB_NAME)
    with db_connection:
        cursor = db_connection.cursor()
        tg_id = (int(tg_id), )
        cursor.execute('DELETE FROM workers WHERE tg_id=?;', tg_id)
        logger.debug(f'из таблицы "workers" удалена запись {tg_id}')

        cursor.execute('SELECT * FROM workers;')
        all_results = cursor.fetchall()
        logger.info(f'Все записи:\n{all_results}')

        db_connection.commit()


def get_tg_ids():
    logger.debug('get_tg_ids')
    db_connection = sqlite3.connect(DB_NAME)
    with db_connection:
        cursor = db_connection.cursor()
        cursor.execute('SELECT tg_id FROM workers;')
        all_results = cursor.fetchall()
        db_connection.commit()

    tg_ids = [tg_id[0] for tg_id in all_results]

    return tg_ids


def get_user_moncms_id(tg_id):
    logger.debug('get_user_moncms_id')
    db_connection = sqlite3.connect(DB_NAME)
    with db_connection:
        cursor = db_connection.cursor()
        tg_id = (int(tg_id), )
        cursor.execute('SELECT moncms_id FROM workers WHERE tg_id=?;', tg_id)
        result = cursor.fetchone()
        db_connection.commit()

    return int(result[0])


if __name__ == '__main__':
    logger.error('Этот скрипт не предназначен для запуска напрямую')
