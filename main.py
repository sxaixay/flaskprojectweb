import os
import uuid

from flask import Flask, session, render_template, request, redirect, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash

from db import db_init, db
from flask_session import Session
from func import login_required
from classes import User, Product

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db_init(app)

# Настроить для использования файловой системы
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# путь к static file
@app.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)


# зарегистрироваться как продавец
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        session.clear()
        password = request.form.get("password")
        repeat_password = request.form.get("repassword")
        if password != repeat_password:
            return render_template("error.html", message="Пароли не совпадают!")

        # хэш-пароль
        pw_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        fullname = request.form.get("fullname")
        username = request.form.get("username")
        # хранить в базе данных
        new_user = User(fullname=fullname, username=username, password=pw_hash)
        try:
            db.session.add(new_user)
            db.session.commit()
        except:
            return render_template("error.html", message="Имя пользователя уже занято!")
        return render_template("login.html", msg="Аккаунт создан!")
    return render_template("signup.html")


# войти как продавец
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session.clear()
        username = request.form.get("username")
        password = request.form.get("password")
        result = User.query.filter_by(username=username).first()
        print(result)
        # Убедитесь, что имя пользователя существует и пароль правильный
        if result is None or not check_password_hash(result.password, password):
            return render_template("error.html", message="Неверное имя пользователя или пароль")
        # Запомнить, какой пользователь вошел в систему
        session["username"] = result.username
        return redirect("/home")
    return render_template("login.html")


# выйти
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# посмотреть все товары
@app.route("/")
def index():
    rows = Product.query.all()
    return render_template("index.html", rows=rows)


# домашняя страница продавца для добавления новых продуктов и редактирования существующих продуктов
@app.route("/home", methods=["GET", "POST"], endpoint='home')
@login_required
def home():
    if request.method == "POST":
        image = request.files['image']
        filename = str(uuid.uuid1()) + os.path.splitext(image.filename)[1]
        image.save(os.path.join("static/images", filename))
        category = request.form.get("category")
        name = request.form.get("pro_name")
        description = request.form.get("description")
        price_range = request.form.get("price_range")
        new_pro = Product(category=category, name=name, description=description, price_range=price_range,
                          filename=filename, username=session['username'])
        db.session.add(new_pro)
        db.session.commit()
        rows = Product.query.filter_by(username=session['username'])
        return render_template("home.html", rows=rows, message="Товар добавлен")

    rows = Product.query.filter_by(username=session['username'])
    return render_template("home.html", rows=rows)


# когда выбрана опция редактирования продукта, эта функция загружается
@app.route("/edit/<int:pro_id>", methods=["GET", "POST"], endpoint='edit')
@login_required
def edit(pro_id):
    # выбрать только редактируемый продукт из бд
    result = Product.query.filter_by(pro_id=pro_id).first()
    if request.method == "POST":
        # выдает ошибку, когда какой-то продавец пытается отредактировать товар другого продавца
        if result.username != session['username']:
            return render_template("error.html", message="У вас нет прав на редактирование этого продукта")
        category = request.form.get("category")
        name = request.form.get("pro_name")
        description = request.form.get("description")
        price_range = request.form.get("price_range")
        comments = request.form.get("comments")
        result.category = category
        result.name = name
        result.description = description
        result.comments = comments
        result.price_range = price_range
        db.session.commit()
        rows = Product.query.filter_by(username=session['username'])
        return render_template("home.html", rows=rows, message="Продукт отредактирован")
    return render_template("edit.html", result=result)
