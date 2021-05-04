#!/usr/bin/python3
__author__ = 'ArkJzzz (arkjzzz@gmail.com)'

# Import
import logging
import urllib
import os
import re
import datetime
import json
from urllib.parse import urlparse
from urllib.parse import urlunparse
from urllib.parse import urlencode

from selenium import webdriver
from bs4 import BeautifulSoup
from dotenv import load_dotenv


logger = logging.getLogger('moncms_parser')

MONCMS_BASE_URL = 'https://moncms.ad.severen.net'


def build_url(base_url, path=None, query=None):
    logger.debug('build_url')
    url = urlparse(base_url)
    url = url._replace(path=path, query=query)

    return url.geturl()


def login_to_moncms(browser):
    logger.debug('login_to_moncms')
    moncms_auth_path = '/auth/login'
    moncms_auth_url = build_url(
            base_url=MONCMS_BASE_URL, 
            path=moncms_auth_path,
        )
    browser.get(moncms_auth_url)

    username_field = browser.find_element_by_id('username')
    password_field = browser.find_element_by_id('password')
    login_btn = browser.find_element_by_tag_name('button')

    username_field.send_keys(os.getenv('MONCMS_USERNAME'))
    password_field.send_keys(os.getenv('MONCMS_PASSWORD'))
    login_btn.click()


def get_exits_links_from_page(required_html):
    logger.debug('get_exits_links_from_page')
    soup = BeautifulSoup(required_html, 'lxml')
    links = []
    for link in soup.find_all('a'):
        link = link.get('href')
        link = urlparse(link)
        if 'action=edit' in str(link.query):
            link = build_url(
                    base_url=MONCMS_BASE_URL,
                    path='/index.php',
                    query=link.query
                )
            if link not in links:
                links.append(link)

    return links


def get_next_page_link(required_html):
    logger.debug('get_next_page_link')
    soup = BeautifulSoup(required_html, 'lxml')
    pagination = soup.find_all(class_="pagination")
    if soup.find(string="далее ►"):
        next_page_link = soup.find(string="далее ►").find_parent().get('href')
        next_page_link = urlparse(next_page_link)
        next_page_link = build_url(
                base_url=MONCMS_BASE_URL,
                path=next_page_link.path,
                query=next_page_link.query
            )
        logger.debug(next_page_link)

        return next_page_link


def get_exits_links(date_from=None, date_to=None):
    logger.debug('get_exits_links')
    if not date_from:
        date_from = datetime.datetime.today().strftime("%Y-%m-%d")
    if not date_to:
        date_to = datetime.datetime.today().strftime("%Y-%m-%d")

    moncms_query = {
        'mod': 'planConnect',
        'dateExitFrom': date_from,
        'dateExitTo': date_to
    }
    next_page_link = build_url(
            base_url=MONCMS_BASE_URL, 
            path='/index.php', 
            query=urlencode(moncms_query),
        )
    exits_links = []

    try: 
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        browser =  webdriver.Chrome(chrome_options=options)
        login_to_moncms(browser)
        while next_page_link:
            logger.debug(next_page_link)
            browser.get(next_page_link)
            links = get_exits_links_from_page(browser.page_source)
            exits_links.extend(links)
            next_page_link = get_next_page_link(browser.page_source)
    except Exception as err:
        logger.error(err)
    finally:
        browser.quit()

    return exits_links


def get_plan_connect_data(exit_link):
    logger.debug('get_plan_connect_data')
    logger.debug(f'link: {exit_link}')

    parsed_exit_link = urlparse(exit_link)
    exit_link_query = parsed_exit_link.query.split('&')
    exit_link_query = {key: value for key, value in (
                            item.split('=') for item in exit_link_query)}

    try: 
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        browser = webdriver.Chrome(chrome_options=options)
        login_to_moncms(browser)
        browser.get(exit_link)
        required_html = browser.page_source

    finally:
        browser.quit()

    soup = BeautifulSoup(required_html, 'lxml')

    plan_connect_id = int(exit_link_query['planConnectId'])
    contract_no = soup.find(id='copyContractNo').text
    departure = soup.find(attrs={'name': 'planConnect[departure]'})
    departure_selected = departure.findChildren(selected='selected')[0].text
    date_exit = soup.find(attrs={'name': 'planConnect[dateExit]'})
    date_exit = date_exit.attrs['value']
    workers = soup.find_all(attrs={'name': 'planConnect[workerId][]'})
    workers = [int(worker.attrs['value']) for worker in workers if worker.attrs['value']]
    client_contact = soup.find(attrs={'name': 'planConnect[clientContact]'})
    client_contact = client_contact.text.split('\n')
    connect_status = soup.find(attrs={'name': 'planConnect[status]'})
    connect_status = connect_status.findChildren(selected='selected')[0].text
    contractors = soup.find(attrs={'name': 'planConnect[contractor]'})
    if contractors.findChildren(selected='selected'):
        contractor = contractors.findChildren(selected='selected')[0].text
    else:
        contractor = None
    sign_act = soup.find(attrs={'name': 'planConnect[sign_act]'})
    sign_act = sign_act.findChildren(selected='selected')[0].text
    if sign_act == 'Да':
        sign_act = True
    else:
        sign_act = False
    configuration_pd = soup.find(attrs={'name': 'planConnect[configurationPd]'})
    configuration_pd = configuration_pd.findChildren(
                                                selected='selected')[0].text
    configuration_voip = soup.find(
                        attrs={'name': 'planConnect[configurationVoip]'})
    configuration_voip = configuration_voip.findChildren(
                                                selected='selected')[0].text
    comments = soup.find_all(id='comment_')
    comments = [comment.text for comment in comments]
    task_ids = []
    tables = soup.findChildren('table')
    for table in tables:
        rows = table.findChildren(['th', 'tr'])
        for row in rows:
            cells = row.findChildren('td')
            if cells:
                if cells[0].text == 'Тип включения':
                    connection_type = cells[1].text.strip()
                elif cells[0].text == 'Адрес':
                    connection_address = cells[1].text.strip()
                elif cells[0].text == 'Клиент':
                    client_name = cells[1].text.strip()
                elif cells[0].text == 'Менеджер':
                    manager = cells[1].text.strip().split('\n')
                    manager = [i.strip() for i in manager]
                elif cells[0].text == 'Ид задания':
                    task_ids.append(cells[1].text)
    connection_tasks = []
    for task_id in task_ids:
        connection_task = {'task_id': task_id}
        task_table = soup.find(string=task_id).find_parent('table')
        rows = task_table.findChildren(['th', 'tr'])
        for row in rows:
            cells = row.findChildren('td')
            if cells:
                if cells[0].text == 'Статус':
                    connection_task['status'] = cells[1].text
                elif cells[0].text == 'Ид объекта':
                    connection_task['obj_id'] = cells[1].text
                elif cells[0].text == 'Тип объекта':
                    connection_task['obj_type'] = cells[1].text
                elif cells[0].text == 'Тип задания':
                    connection_task['task_type'] = cells[1].text
                elif cells[0].text == 'Идентификатор':
                    connection_task['identifier'] = cells[1].text
                elif cells[0].text == 'Состояние':
                    connection_task['condition'] = cells[1].text
                elif cells[0].text == 'Служба':
                    connection_task['department'] = cells[1].text
                elif cells[0].text == 'Примечание':
                    connection_task['note'] = cells[1].text
        connection_tasks.append(connection_task)

    return {'plan_connect_id': plan_connect_id, # int
            'contract_no': contract_no, # str
            'connection_type': connection_type, # str
            'connection_address': connection_address, # str
            'departure_selected': departure_selected, # str
            'contractor': contractor, # str
            'date_exit': date_exit, # str
            'workers': workers, # [int]
            'client_name': client_name,
            'client_contact': client_contact, # [str]
            'manager': manager, # [str]
            'connect_status': connect_status, # str
            'sign_act': sign_act, # bool
            'configuration_pd': configuration_pd, # str
            'configuration_voip': configuration_voip, # str
            'comments': comments, # [str]
            'connection_tasks': connection_tasks, # [{}]
            }


if __name__ == '__main__':
    logger.debug('Этот скрипт не предназначен для запуска напрямую')
