#!/usr/bin/python3
__author__ = 'ArkJzzz (arkjzzz@gmail.com)'


import os
import logging
import sqlite3


logger = logging.getLogger('init_db')

          

def main():

    formatter = logging.Formatter(
            fmt='%(asctime)s %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%b-%d %H:%M:%S (%Z)',
            style='%',
        )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)


    db_connection = sqlite3.connect('plan_connect.db')
    logger.info('the "plan_connect.db" database is used')
    with db_connection:
        cursor = db_connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS workers')

        cursor.execute('''CREATE TABLE IF NOT EXISTS workers (
                tg_id INT PRIMARY KEY, 
                moncms_id INT, 
                name TEXT);
            ''')
        db_connection.commit()

        logger.info('created table "workers"')


if __name__ == '__main__':
    main()
