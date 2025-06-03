import os

from datetime import datetime
from random import randrange

from flask import Flask, abort, flash, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, URLField
from wtforms.validators import DataRequired, Length, Optional


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db = SQLAlchemy(app)


class Opinion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    text = db.Column(db.Text, unique=True, nullable=False)
    source = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)


class OpinionForm(FlaskForm):
    title = StringField(
        'Введите название фильма',
        validators=[
            DataRequired(message='Обязательное поле'),
            Length(1, 128)
        ]
    )
    text = TextAreaField(
        'Напишите мнение',
        validators=[DataRequired(message='Обязательное поле')]
    )
    source = URLField(
        'Добавьте ссылку на подробный обзор фильма', 
        validators=[
            Length(1, 255),
            Optional()
        ]
    )
    submit = SubmitField('Добавить')


@app.route('/')
def index_view():
    quantity = Opinion.query.count()
    if not quantity:
        abort(500)
    # Случайное число от нуля до quantity
    offset_value = randrange(quantity)
    opinion = Opinion.query.offset(offset_value).first()
    return render_template('opinion.html', opinion=opinion)


@app.route('/opinions/<int:id>')
def opinion_view(id):
    opinion = Opinion.query.get_or_404(id)
    return render_template('opinion.html', opinion=opinion)


@app.route('/add', methods=['GET', 'POST'])
def add_opinion_view():
    form = OpinionForm()
    if form.validate_on_submit():
        text = form.text.data
        # Если в БД уже есть мнение с текстом, который ввёл пользователь...
        if Opinion.query.filter_by(text=text).first() is not None:
            # ...вызвать функцию flash и передать соответствующее сообщение:
            flash('Такое мнение уже было оставлено ранее"!')
            # Вернуть пользователя на страницу «Добавить новое мнение»:
            return render_template('add_opinion.html', form=form)
        opinion = Opinion(
            title=form.title.data,
            text=form.text.data,
            source=form.source.data
        )
        db.session.add(opinion)
        db.session.commit()
        return redirect(url_for('opinion_view', id=opinion.id))
    # Если валидация не пройдена — просто отрисовать страницу с формой:
    return render_template('add_opinion.html', form=form)


@app.errorhandler(500)
def internal_error(error):
    # Ошибка 500 возникает в нештатных ситуациях на сервере. 
    # Например, провалилась валидация данных.
    # В таких случаях можно откатить изменения, не зафиксированные в БД,
    # чтобы в базу не записалось ничего лишнего.
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run()
