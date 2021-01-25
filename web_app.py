from flask import Flask, render_template, request, abort
import datetime
import telebot
from sqlalchemy.orm import sessionmaker
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from format_message import format_message
import sqlite3
from database import init_db, db_session
from models import User, Record
from threading import Thread
from sqlalchemy import *
import json
import gspread
import pandas as pd
from gspread import Cell
from oauth2client.service_account import ServiceAccountCredentials
import logging
import os
import time

API_TOKEN = '1424148522:AAFjMIx2a0BXM9VOhhgEUCCilmkfWDxfu6k'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('sheet_creds.json', scope)
client = gspread.authorize(creds)

init_db()

WEBHOOK_HOST = '64.227.120.83'
WEBHOOK_PORT = 80  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_URL_BASE = "http://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (API_TOKEN)

# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)

@app.before_first_request
def before_first_request():
    log_level = logging.INFO

    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)

    root = os.path.dirname(os.path.abspath(__file__))
    logdir = os.path.join(root, 'logs')
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    log_file = os.path.join(logdir, 'app.log')
    handler = logging.FileHandler(log_file)
    handler.setLevel(log_level)
    app.logger.addHandler(handler)

    app.logger.setLevel(log_level)

@app.teardown_appcontext
def shutdown_db_session(exception=None):
    db_session.remove()


# conn = sqlite3.connect('database.sqlite')
# conn.executescript("""create table IF NOT EXISTS main
# (
#     user_phone TEXT
#         constraint table_name_pk
#             primary key,
#     user_name  TEXT,
#     price      int,
#     date       int
# );
#
# create unique index IF NOT EXISTS table_name_user_phone_uindex
#     on main (user_phone);
# """)


@app.route('/')
def webprint():
    return render_template('html/index.html')


def update_record(record_id, confirmed):
    record_data = db_session.query(Record).filter(Record.id == record_id)[0]
    already_confirmed = record_data.confirmed
    db_session.query(Record).filter(Record.id == record_id).update({'confirmed': confirmed})
    db_session.commit()
    if confirmed:
        if not already_confirmed:
            sheet_data_attrs = ['price', 'date', 'time', 'user_phone']
            user_data = db_session.query(User).filter(User.user_phone == record_data.user_phone)[0]
            add_form_to_excel(*[getattr(record_data, attr) for attr in sheet_data_attrs], user_data.user_name)
            sort_excel()
    else:
        pass
        # ToDo
        # make record removing from google sheet


def sort_excel():
    sheet = client.open("andrey_test").sheet1
    all_values = sheet.get_all_values()
    df = pd.DataFrame(all_values[3:])
    df[1] = pd.to_datetime(df[1])
    df[1] = df[1].apply(lambda date: date.strftime('%d/%m/%Y'))
    df[1] = (df[1] + df[3]).apply(pd.to_datetime, format='%d/%m/%Y%H:%M')
    df = df.sort_values(by=[1])
    df[3] = df[1].apply(lambda date: date.strftime('%H:%M'))
    df[1] = df[1].apply(lambda date: date.strftime('%d/%m/%Y'))
    cell_list = []
    row_gap = 4
    cell_gap = 1
    for row_n, row in enumerate(df.values.tolist(), start=row_gap):
        for cell_n, cell_value in enumerate(row, start=cell_gap):
            google_cell = Cell(row_n, cell_n)
            google_cell.value = cell_value
            cell_list.append(google_cell)
    sheet.update_cells(cell_list)


#     sheet.values_update(
#     'Sheet1!B4',
#     params={
#         'valueInputOption': 'RAW'
#     },
#     body={
#         'values':df.values.tolist()
#     }
# )
#     range = None

def add_form_to_db(body):
    app.logger.info('addformtodb')
    user_phone = body['phone']
    user_name = body['name']
    price = int(body['price'])
    date = body['date']
    time = body['time']
    user = User(user_phone=user_phone, user_name=user_name)
    record = Record(price=price, date=date, time=time, user_phone=user_phone)
    try:
        db_session.add(user)
        db_session.add(record)
        db_session.commit()
    except:
        db_session.rollback()
        db_session.add(record)
        db_session.commit()
    return record.id


def get_markup(record_id):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Подтвердить", callback_data=str(record_id) + ':confirmed'),
               InlineKeyboardButton("Отклонить", callback_data=str(record_id) + ':deny'))
    return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    app.logger.info('callback')
    update_record(call.data.split(':')[0], call.data.endswith('confirmed'))


def add_form_to_excel(price, date, time, user_phone, user_name):
    sheet = client.open("andrey_test").sheet1
    records_len = len(sheet.get_all_values())
    week_day = datetime.datetime.strptime(date, '%m/%d/%Y').strftime('%A')
    row = ['', date, week_day, time, user_name, user_phone, '', '', price]
    sheet.insert_row(row, records_len + 1)


@app.route('/submit_form', methods=['POST'])
def submit_form():
    body = request.get_json()
    record_id = add_form_to_db(body)
    template = "  Цена  : {price}     \n " \
               "  Дата  : {date}     \n " \
               "  Время  : {time}     \n " \
               "  Имя  : {name}     \n " \
               "  Телефон  : {phone}     \n "
    formatted_message = template.format(price=body['price'],
                                        date=body['date'],
                                        time=body['time'],
                                        name=body['name'],
                                        phone=body['phone'])
    # bot.send_message(334755342 -413309944, formatted_message, reply_markup=get_markup(record_id))
    bot.send_message(334755342, formatted_message, reply_markup=get_markup(record_id))
    return '', 200


@app.route('/get_times_by_date', methods=['POST'])
def get_times_by_date():
    date = request.get_json()['date']
    not_available_times = [record.time for record in db_session.query(Record).filter_by(date=date, confirmed=True)]
    return {'not_available_time': list(set(not_available_times))}


if __name__ == '__main__':
    bot.remove_webhook()

    time.sleep(0.1)

    # Set webhook
    bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)
    Thread(target=bot.polling).start()
    app.run(host='0.0.0.0')
