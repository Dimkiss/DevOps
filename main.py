from flask import Flask
import parse_data
import sqlite3
    
# Создаем соединение с базой данных. Если базы данных не существует, она будет создана.
conn = sqlite3.connect('mydatabase.db')

# Создаем курсор - это специальный объект, который делает запросы и получает их результаты
cursor = conn.cursor()


app = Flask(__name__)

@app.route('/', methods=['GET'])
def get_data():
    data = parse_data.main()

    # здесь можно сохранять в бд

    return {
        'status': 200,
        'data': data
    }

@app.route('/create_table', methods=['GET'])
def create_table():
    # Создаем таблицу
    cursor.execute("""CREATE TABLE articles(
            title text,
            
    )""")

    # Сохраняем изменения
    conn.commit()

    return {
        'status': 200
    }

# Закрываем соединение с базой данных
conn.close()