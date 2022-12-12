import random
import string
import requests
import pymysql.cursors
import credits as cred


# Подключение к БД
def get_connection():
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='QWER2006ZXCV',
                                 db='support',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    
    return connection


# Генерация случайной последовательности символов
def random_string(length):
    rand_string = ''
    letters = string.ascii_lowercase
    
    for i in range(length):
        rand_string = ''.join(random.choice(letters))
    
    return rand_string


# Отправка теста в тг
def send_message(chat_id, text):
    answer = {'chat_id': chat_id, 'text': text}
    req = requests.post(url=f'{cred.URL}/sendMessage', json=answer)
    
    return req.json()
