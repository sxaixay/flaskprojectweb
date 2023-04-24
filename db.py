from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# Функция, которая инициализирует БД и создает таблицы
def db_init(app):
    db.init_app(app)

    # Создает таблицы журналов, если БД еще не существует
    with app.app_context():
        db.create_all()