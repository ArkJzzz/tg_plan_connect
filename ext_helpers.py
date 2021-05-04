#!/usr/bin/python3
__author__ = 'ArkJzzz (arkjzzz@gmail.com)'


import os
import logging
import requests
import json
import textwrap


logger = logging.getLogger('ext_helpers')




def fetch_coordinates_from_address(place):
    base_url = 'https://geocode-maps.yandex.ru/1.x'
    params = {
        'geocode': place, 
        'apikey': os.getenv('YANDEX_GEOCODER_API_KEY'), # FIXME 
        'sco': 'longlat', 
        'format': 'json',
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    response = response.json()
    places_found = response['response']['GeoObjectCollection']['featureMember']
    if places_found:
        most_relevant = places_found[0]
        return most_relevant['GeoObject']['Point']['pos']


def extract_coordinates(message):
    logger.debug('extract_coordinates')
    
    if message.location:
        logger.debug(f'message.location: {message.location}')
        lon = message.location.longitude
        lat = message.location.latitude
        logger.debug(f'location: lat {lat}, lon {lon}')
        return (lat, lon)

    elif message.text:
        logger.debug(f'message.text: {message.text}')
        location = fetch_coordinates_from_address(message.text)
        if location:
            lon, lat = location.split(' ')
            logger.debug(f'location: lat {lat}, lon {lon}')
            return (lat, lon)


def formatting_for_markdown(text):
    logger.debug('formatting_for_markdown')
    escaped_characters = [
        '[', ']', '(', ')', '~', '`', '>', '#', 
        '+', '-', '=', '|', '{', '}', '.', '!',
    ]
    for character in escaped_characters:
        text = text.replace(character, '\\' + character)

    return text


def check_informative(comment):
    logger.debug('check_informative')
    excluded_comments = (
        'Изменен выезд на включение',
        'Изменен подрядчик',
        'Изменена дата выезда',
        'Изменен инженер',
        'Контактные данные клиента изменены',
        'Изменен статус',
        'Акт подписан',
        'Статус настройки оборудования',
    )

    for excluded_comment in excluded_comments:
        if excluded_comment in comment:
            return False

    return True



def get_formated_task(plan_connect_data):
    logger.debug('get_formated_task')
    plan_connect_id = plan_connect_data['plan_connect_id']
    contract_no = plan_connect_data['contract_no']
    client_name = plan_connect_data['client_name']
    connection_address = plan_connect_data['connection_address']
    client_contacts = '\n'.join(plan_connect_data['client_contact'])
    manager = ', '.join(plan_connect_data['manager'])
    comments = plan_connect_data['comments']
    comments.reverse()
    comments = [comment for comment in comments if check_informative(comment)]
    comments = '\n'.join(comments)
    connection_tasks = ''
    for connection_task in plan_connect_data['connection_tasks']:
        formated_connection_task = (
            f'ID объекта: _{connection_task["obj_id"]}_;\n'
            f'Тип объекта: _{connection_task["obj_type"]}_;\n'
            f'Наименование: _{connection_task["task_type"]}_;\n'
            f'Идентификатор: _{connection_task["identifier"]}_;\n'
            f'Примечание: \n_{connection_task["note"]}_\n\n'
        )
        connection_tasks += formated_connection_task

    formated_task = (
        f'*{contract_no} {client_name}*\n'
        f'*{connection_address}*\n'
        f'Контакты:\n'
        f'_{client_contacts} _\n'
        f'Менеджер: _{manager}_\n\n'
        f'*Комментарии из moncms:*\n'
        f'_{comments} _\n\n'
        f'*Задания:*\n'
        f'{connection_tasks} \n'
    )
    formated_task = formatting_for_markdown(formated_task)

    return formated_task




def get_task_keyboard():
    comments_button = InlineKeyboardButton(
            text='Комментарии из moncms', 
            callback_data='HANDLE_MONCMS_COMMENTS',
        )
    connection_tasks_button = InlineKeyboardButton(
            text='Задания на включение услуг', 
            callback_data='HANDLE_CONNECTION_TASKS',
        )
    completed_button = InlineKeyboardButton(
            text='Выполнено', 
            callback_data='HANDLE_COMPLETED',
        )
    uncompleted_button = InlineKeyboardButton(
            text='Не выполнено', 
            callback_data='HANDLE_UNCOMPLETED',
        )

    task_keyboard = [
        [comments_button],
        [connection_tasks_button],
        [completed_button, uncompleted_button],
    ]

    return InlineKeyboardMarkup(task_keyboard)


if __name__ == '__main__':
    logger.error('Этот скрипт не предназначен для запуска напрямую')
