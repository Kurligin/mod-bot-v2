import random
import string
import requests
import pymysql.cursors
import wget

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


# Отправка файла в тг
def download_file(source, user_folder):
    image_url = f'{cred.URL}/getFile?file_id={source["file_id"]}'
    image_json = requests.get(image_url).json()  # Запихиваем в json, т.е. читаем его
    image_inner_path = image_json['result']['file_path']
    image_path = f'{cred.FILE_URL}/{image_inner_path}'  # это путь к картинке
    
    print(image_path, 'ссылка на файл')
    wget.download(image_path, user_folder)  # качаем картинку
    
    return image_path


# Отправка фото в тг
def download_photo(source, user_folder):
    image_url = f'{cred.URL}/getFile?file_id={source[len(source) - 1]["file_id"]}'  # GET строка, которая определяет путь к файлу (getFile это из api телеги)
    image_json = requests.get(image_url).json()  # Запихиваем в json, т.е. читаем его
    image_inner_path = image_json['result']['file_path']
    image_path = f'{cred.FILE_URL}/{image_inner_path}'  # это путь к картинке
    
    print(image_path, 'ссылка на файл')
    wget.download(image_path, user_folder)  # качаем картинку
    
    return image_path
