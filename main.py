from flask import Flask, render_template, request, redirect, jsonify
from werkzeug.utils import secure_filename
import datetime as dt
import os
import requests

import funcs
import credits as cred

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0



@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        req = request.get_json()
        date_time = dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")  # 2017-04-05-00.18.00
        username = ''
        chat_id = ''
        
        print(req, ' пришло!')
        
        if "'message'" in str(req):
            chat_id = req['message']['chat']['id']
            
            if 'last_name' in str(req):  # Не всегда есть last_name
                username = f'{req["message"]["from"]["first_name"]} {req["message"]["from"]["last_name"]}'
            else:
                username = req['message']['from']['first_name']
        
        
        connection = funcs.get_connection()  # основной коннект
        cursor = connection.cursor()  # курсор есть курсор
        
        position = cursor.execute('SELECT * FROM users_list WHERE name LIKE %s', chat_id)  # Поиск id отправителя. Нужно для запрета публикации топика
        print('chat position', position)
        
        if "text" in str(req) or "document" in str(req) or "photo" in str(req):
            print('Сообщение пришло от', username)
            
            if "'text'" in str(req):
                message = req['message']['text']
                print(message, ' Это отправленный текст')
                
                if message == '/start':
                    funcs.send_message(chat_id, text=f'Здравствуйте, {username}. Если вы хотите написать обращение к администратору, то пишите /new_topic')
                    print('новый запуск')
                
                if message != '/new_topic' and position == 0:
                    funcs.send_message(chat_id, text='У Вас нет открытых обращений. Вам необходимо открыть новое /new_topic')
                
                elif message == '/new_topic' and position == 0:
                    funcs.send_message(chat_id, text='Введите тему сообщения.')
                    
                    cursor.execute('INSERT INTO topic (author, date_time, chat_id) VALUES(%s,%s,%s)', (username, date_time, chat_id))
                    
                    cursor.execute('SELECT id FROM topic ORDER BY id DESC LIMIT 1')
                    id_next = cursor.fetchall()[0]['id']  # перевод в словарь
                    print(id_next, ' последний id')
                    
                    cursor.execute('INSERT INTO users_list (Name, topic_id) VALUES(%s,%s)', (chat_id, id_next))  # вставка строки в таблицу user_list
                    cursor.execute('INSERT INTO updates (ID, isnew) VALUES(%s,%s)', (id_next, True))
                
                
                elif position == 1 and message != '/new_topic':
                    if len(message) <= 255:
                        funcs.send_message(chat_id, text='Введите полное описание проблемы.')
                        
                        cursor.execute("SELECT * FROM users_list WHERE name LIKE %s", chat_id)  # узнаем id топика в который вносим изменения
                        topic_id = cursor.fetchall()[0]['topic_id']
                        
                        cursor.execute('INSERT INTO users_list (Name, topic_id) VALUES(%s,%s)', (chat_id, topic_id))  # вставка строки в таблицу user_list
                        cursor.execute("UPDATE topic SET title = %s WHERE ID = %s", (message, topic_id))
                        print('перезаписалось')
                    else:
                        funcs.send_message(chat_id, text='Сообщение слишком длинное!')
                
                elif position == 2 and message != '/new_topic':
                    if len(message) <= 1000:
                        funcs.send_message(chat_id, text='Теперь можете отправить фото для лучшего понимания проблемы. Если такового нет, отправьте "нет".')
                        
                        cursor.execute("SELECT * FROM users_list WHERE name LIKE %s", chat_id)  # узнаем id топика в который вносим изменения
                        topic_id = cursor.fetchall()[0]['topic_id']
                        
                        cursor.execute('INSERT INTO users_list (Name, topic_id) VALUES(%s,%s)', (chat_id, topic_id))  # вставка строки в таблицу user_list
                        cursor.execute("UPDATE topic SET body_text = %s WHERE ID = %s", (message, topic_id))
                        print('перезаписалось')
                    else:
                        funcs.send_message(chat_id, text='Сообщение слишком длинное!')
                
                elif position == 2 and 'photo' in str(req):
                    funcs.send_message(chat_id, text='Спасибо за сообщение. Топик открыт.')
                    funcs.download_photo(req["message"]["photo"], user_folder)
                    
                    print(req['message']['photo'][0]['file_id'], ': Это id картинки')  # Это id картинки
                
                elif position == 3 and message != '/new_topic':
                    funcs.send_message(chat_id, text='Ваша заявка принята. Системный администратор скоро свяжется с Вами. Отправьте /close_topic если желаете вы сами нашли решение проблемы.')
                    
                    topic_id = cursor.fetchall()[0]['topic_id']
                    cursor.execute('INSERT INTO users_list (Name, topic_id) VALUES(%s,%s)', (chat_id, topic_id))  # вставка строки в таблицу user_list
                    
                    cursor.execute("UPDATE topic SET file_name = %s WHERE ID = %s", ('нет', topic_id))
                    cursor.execute("UPDATE topic SET status = %s WHERE ID = %s", ('открыт', topic_id))
                    print('перезаписалось фото')
                
                elif message == '/close_topic' and position == 4 and message != '/new_topic':
                    funcs.send_message(chat_id, text='Надеемся, что вы нашли решение своей проблемы! Если вопросы возникнут повторно, пишите /new_topic')
                    cursor.execute('SELECT topic_id FROM support.users_list WHERE name LIKE %s', (str(chat_id)))
                    
                    topic_id = int(cursor.fetchall()[-1]['topic_id'])
                    cursor.execute('DELETE FROM support.users_list WHERE topic_id = %s', topic_id)
                    connection.commit()  # подтверждение изменений в базе
                    print('топик удален')
                    
                    cursor.execute("UPDATE topic SET status = %s WHERE ID = %s", ('закрыт', topic_id))
                    connection.commit()
                
                elif position == 4 and message == '/new_topic':
                    funcs.send_message(chat_id, text='У вас уже открыт диалог с модератором. Ждите ответа')
                
                elif position == 4 and message != '/new_topic':
                    cursor.execute('SELECT topic_id FROM support.users_list WHERE Name = %s', chat_id)  # определить id отправителя
                    topic_id = cursor.fetchall()[0]['topic_id']
                    
                    cursor.execute('INSERT INTO talk (topic_id, chat_id, author, date_time, answer, file_name) VALUES(%s,%s,%s,%s,%s,%s)',
                                   (topic_id, chat_id, username, date_time, message, ''))  # выполнение sql команды
                    
                elif message == '/new_topic':
                    funcs.send_message(chat_id, text='Вы уже создаете топик!')
            
            
            elif 'photo' in str(req) and position == 3:
                funcs.send_message(chat_id, text='Ваша заявка принята. Системный администратор скоро свяжется с Вами')
                image_path = funcs.download_photo(req["message"]["photo"], user_folder)
                
                topic_id = cursor.fetchall()[0]['topic_id']
                
                cursor.execute('INSERT INTO users_list (Name, topic_id) VALUES(%s,%s)', (chat_id, topic_id))
                cursor.execute("UPDATE topic SET file_name = %s WHERE ID = %s", (image_path, topic_id))
                cursor.execute("UPDATE topic SET status = %s WHERE ID = %s", ('открыт', topic_id))
                print('перезаписалось фото')
            
            elif 'document' in str(req) and position == 3:
                funcs.send_message(chat_id, text='Ваша заявка принята. Системный администратор скоро свяжется с Вами')
                image_path = funcs.download_file(req["message"]["document"], user_folder)
                
                cursor.execute('SELECT topic_id FROM support.users_list WHERE Name = %s', chat_id)  # определить id отправителя
                topic_id = cursor.fetchall()[0]['topic_id']
                
                cursor.execute('INSERT INTO support.users_list (Name, topic_id) VALUES(%s,%s)', (str(chat_id), topic_id))  # вставка строки в таблицу user_list
                cursor.execute("UPDATE support.topic SET file_name = %s WHERE ID = %s", (image_path, topic_id))
                cursor.execute("UPDATE support.topic SET status = %s WHERE ID = %s", ('открыт', topic_id))
                print('перезаписалось док')
            
            elif 'photo' in str(req) and position == 4:
                image_path = funcs.download_photo(req["message"]["photo"], user_folder)
                
                cursor.execute('SELECT topic_id FROM support.users_list WHERE Name = %s', chat_id)  # определить id потека отправителя
                topic_id = cursor.fetchall()[0]['topic_id']
                cursor.execute('INSERT INTO talk (topic_id, chat_id, author, date_time, answer,file_name) VALUES(%s,%s,%s,%s,%s,%s)',
                               (topic_id, chat_id, username, date_time, "", image_path))  # выполнение sql команды
                print('перезаписалось фото')
            
            elif 'document' in str(req) and position == 4:
                image_path = funcs.download_file(req["message"]["document"], user_folder)
                
                cursor.execute('SELECT topic_id FROM support.users_list WHERE Name = %s', chat_id)  # определить id топика отправителя
                topic_id = cursor.fetchall()[0]['topic_id']
                
                cursor.execute('INSERT INTO support.talk (topic_id, chat_id, author, date_time, answer,file_name) VALUES(%s,%s,%s,%s,%s,%s)',
                               (topic_id, chat_id, username, date_time, "", image_path))  # выполнение sql команды
                print('перезаписалось фото')
            
            connection.commit()
            connection.close()
            
            return jsonify(req)
        else:
            funcs.send_message(chat_id, text='Недопустимый формат! Могут быть присланы только сообщения или фотографии!')
            print('недопустимый формат')
            return "200"


# ---------------------------------------------------------------------------------------------------------------------------
@app.route('/')  # done!
def main():
    return render_template("index.html")


@app.route('/admin/<status>')  # done!
def index1(status):
    connection = funcs.get_connection()  # основной коннект
    cursor = connection.cursor()  # курсор есть курсор
    topic_table = list()

    cursor.execute("select * from support.updates WHERE isnew = True")  # выполнение sql команды
    new_topic = [i['ID'] for i in cursor.fetchall()]
    
    if new_topic:
        updates = True
    else:
        updates = False
    
    if status == 'all':
        cursor.execute("SELECT * FROM topic")  # выполнение sql команды
        topic_table = cursor.fetchall()  # fetchall() это перевод объекта в кортеж
    
    if status == "close":
        cursor.execute("select * from support.topic t WHERE status = 'закрыт'")  # выполнение sql команды
        topic_table = cursor.fetchall()  # fetchall() это перевод объекта в кортеж

    if status == "open":
        cursor.execute("select * from support.topic t WHERE status = 'открыт'")  # выполнение sql команды
        topic_table = cursor.fetchall()  # fetchall() это перевод объекта в кортеж
    
    if status == "new":
        cursor.execute("select * from support.updates WHERE isnew = True")  # выполнение sql команды
        new_topic = [i['ID'] for i in cursor.fetchall()]
        
        for i in new_topic:
            cursor.execute("select * from support.topic WHERE ID = %s;", int(i))
            topic_table.append(cursor.fetchall()[0])

    
    connection.close()
    return render_template('index.html', topic_table=topic_table, status=status, updates=updates)


@app.route('/talk/<text>')  # done!
def talk(text):
    connection = funcs.get_connection()  # основной коннект
    cursor = connection.cursor()  # курсор есть курсор

    cursor.execute("select * from support.updates WHERE isnew = True")  # выполнение sql команды
    new_topic = [i['ID'] for i in cursor.fetchall()]

    if int(text) in new_topic:
        print(new_topic, text, int(text) in new_topic)
        cursor.execute("UPDATE support.updates SET isnew = False WHERE ID = %s;", int(text))
        connection.commit()

    cursor.execute('SELECT * FROM topic t WHERE t.ID = %s', text)  # выполнение sql команды
    table_head = cursor.fetchall()[0]  # fetchall() это перевод объекта в кортеж
    
    cursor.execute('SELECT * FROM talk t WHERE t.topic_id = %s', text)  # выполнение sql команды
    table = cursor.fetchall()  # fetchall() это перевод объекта в кортеж
    
    try:
        chat_id = table[0]['chat_id']
    except IndexError:
        chat_id = ''

    talk_table = [{'id': '~', 'topic_id': table_head['ID'], 'chat_id': chat_id,
                   'author': table_head['author'], 'date_time': table_head['date_time'],
                   'answer': table_head['body_text'], 'file_name': table_head['file_name']}]
    for i in table:
        talk_table.append(i)
    
    position = cursor.execute('SELECT * FROM users_list WHERE topic_id = %s', text)  # Поиск id отправителя. Нужно для запрета публикации топика
    
    connection.close()
    return render_template('talk.html', talk_table=talk_table, text=text, where_name=position)  # f обязательно для поз вращения переменной



@app.route('/send_answer', methods=['POST'])  # done!
def send_answer():
    file_name = ''
    
    if request.method == 'POST':
        connection = funcs.get_connection()  # основной коннект
        cursor = connection.cursor()  # курсор есть курсор
        
        answer = request.form['answer']
        topic_id = request.form['topic_id']
        print(f'topic id: {topic_id}, answer: {answer}')

        cursor.execute('SELECT status FROM topic WHERE ID = %s;', topic_id)
        status = cursor.fetchone()['status']
        print(status)
        
        if status != 'закрыт':
            date_time = dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('SELECT name FROM support.users_list WHERE topic_id = %s;', topic_id)
            chat_id = cursor.fetchall()[0]['name']
            
            funcs.send_message(chat_id, text=answer)
            
            file = request.files['file']
            if file:
                file_name = secure_filename(file.filename)
                print(file, file_name)
                
                if '.' not in file_name:
                    print('Не загрузил. Кириллица в названии')
                else:
                    print(f'{admin_folder}/{file_name}')
                    file.save(f'{admin_folder}/{file_name}')
                    
                    # ---------------переименование загруженного файла-----------------
                    extension = file_name.split('.')[1]
                    random_name = funcs.random_string(16)
                    
                    os.rename(f'{admin_folder}/{file_name}', f'{admin_folder}/{random_name}.{extension}')
                    file_name = f'http://127.0.0.1:5000/{admin_folder}/{random_name}.{extension[1]}'
                    print(f'{random_name}.{extension} - Название переименованного файла')
                    
                    # ----отправка изображения в телегу--------------------------------------------------------------------------------------------
                    file_path = f'{admin_folder}/{random_name}.{extension}'
                    
                    try:
                        files = {'photo': open(file_path, 'rb')}
                        message = f'{cred.URL}/sendPhoto?chat_id={str(chat_id)}'
                    except FileNotFoundError:
                        files = {'document': open(file_path, 'rb')}
                        message = f'{cred.URL}/sendDocument?chat_id={str(chat_id)}'
                    
                    requests.post(message, files=files)
                    
                    cursor.execute('INSERT INTO talk (topic_id, chat_id, author, date_time, answer, file_name) VALUES(%s,1111,%s,%s,%s,%s)',
                                   (topic_id, admin_name, date_time, answer, file_name))  # выполнение sql команды
                    connection.commit()
            else:
                cursor.execute('INSERT INTO talk (topic_id, chat_id, author, date_time, answer,file_name) VALUES(%s,1111,%s,%s,%s,%s)',
                               (topic_id, admin_name, date_time, answer, file_name))  # выполнение sql команды
                connection.commit()
                
            connection.close()
            return redirect('/talk/' + str(topic_id))
        else:
            connection.close()
            return render_template('close_topic.html', sucsess='Топик закрыт!')


@app.route('/close_topic')  # done!
def close_topic():
    return render_template('close_topic.html')


@app.route('/close_handler', methods=['POST'])  # done!
def close_topic1():
    if request.method == 'POST':
        connection = funcs.get_connection()  # основной коннект
        cursor = connection.cursor()  # курсор есть курсор
        
        password_close = request.form['password_close']
        topic_id = int(request.form['topic_id'])
        print(f'topic id: {topic_id}, password: {password_close}')
        
        cursor.execute('SELECT status FROM topic WHERE ID = %s;', topic_id)
        status = cursor.fetchall()[0]['status']
        
        if password_close == '111' and status == 'открыт':
            cursor.execute('SELECT author FROM topic WHERE ID = %s;', topic_id)
            position = cursor.fetchall()[0]['author']
            
            cursor.execute('SELECT chat_id FROM topic WHERE author = %s;', position)
            chat_id = cursor.fetchone()['chat_id']
            
            cursor.execute('DELETE FROM support.users_list WHERE topic_id = %s', topic_id)
            connection.commit()
            
            cursor.execute("UPDATE topic SET status = %s WHERE ID = %s", ('закрыт', topic_id))
            connection.commit()
            connection.close()

            funcs.send_message(chat_id, text='Чат был закрыт администратором. Если вопросы возникнут повторно, пишите /new_topic')
            return render_template('close_topic.html', sucsess='Топик закрыт!')
        
        elif password_close != '111' and status == 'открыт':
            connection.close()
            return render_template('close_topic.html', sucsess='Пароль неверный!')
        
        else:
            connection.close()
            return render_template('close_topic.html', sucsess='Топик уже закрыт!')


name_file = ''

if __name__ == '__main__':
    admin_name = 'admin'
    user_folder = 'user_photos'
    admin_folder = 'admin_photos'
    
    if not os.path.isdir(user_folder):
        os.mkdir(user_folder)
    if not os.path.isdir('admin_photos'):
        os.mkdir('admin_photos')
    
    app.run()
