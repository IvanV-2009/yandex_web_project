from flask import Flask, render_template, redirect, request, url_for, abort, jsonify, session
from data.users import User
from data.likes import Like
from forms.user import RegisterForm
from forms.login_form import LoginForm
from data.news import News
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from forms.news import NewsForm
from data.comment import Comment
from data.tags import Tags
from werkzeug.utils import secure_filename
import os
import bleach
import uuid
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

upload_folder = os.path.join('static', 'uploads')

app.config['UPLOAD'] = upload_folder

DATABASE = 'db/blogs.db'

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)



def main():
    db_session.global_init("db/blogs.db")
    app.run()


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', form=form, title='Регистрация')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/news_log")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/news', methods=['GET', 'POST'])
def create_new():
    if request.method == 'POST':

        title = bleach.clean(request.form['title'])
        content = request.form['content']
        print(1)
        print(title)
        print(content)
        post = News(
            title=title,
            content=content,
            user_id=current_user.id
        )
        db = db_session.create_session()
        db.add(post)
        db.commit()
        return redirect(url_for('news_log'))
    return render_template('news.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/news_log")


@app.route('/news_log', methods=['GET', 'POST'])
def news_log():
    db_sess = db_session.create_session()
    news = db_sess.query(News).all()
    return render_template('lenta.html', news=news)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
def watch_new(id):
    db_sess = db_session.create_session()
    new = db_sess.query(News).get(id)
    db = get_db()

    # Получаем все сообщения с информацией об авторе и реакциях
    messages = db.execute("""
        SELECT m.id, m.text, m.timestamp, m.reply_to, 
               u.name,
               (SELECT COUNT(*) FROM reactions r WHERE r.message_id = m.id AND r.reaction_type = 'like') as likes,
               (SELECT COUNT(*) FROM reactions r WHERE r.message_id = m.id AND r.reaction_type = 'dislike') as dislikes,
               (SELECT r.reaction_type FROM reactions r WHERE r.message_id = m.id AND r.user_id = ?) as user_reaction
        FROM messages m
        JOIN users u ON m.user_id = u.id
        ORDER BY m.timestamp DESC
    """, (current_user.id,)).fetchall()

    return render_template('new.html', new=new, messages=messages)


@app.route('/user_profile/<int:id>')
def user_profile(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(id)
    news = db_sess.query(News).filter(News.user_id == id).all()
    return render_template('user.html', user=user, news=news)


@app.route('/user_profile/<int:id>/comments')
def user_profile_comments(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(id)
    comments = db_sess.query(Comment).filter(Comment.user_id == id).all()
    return render_template('user_comments.html', user=user, comments=comments)


@app.route('/news_edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            db_sess.commit()
            return redirect('/news_log')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).get(id)
    comments = db_sess.query(Comment).filter(Comment.news_id == id).all()
    if news:
        img = news.image_path
        if os.path.exists(img):
            os.remove(img)
        db_sess.delete(news)
        if comments:
            for i in comments:
                db_sess.delete(i)
        db_sess.commit()
    else:
        abort(404)
    return redirect(f'/user_profile/{current_user.id}')


@app.route('/comment_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def comment_delete(id):
    db_sess = db_session.create_session()
    comment = db_sess.query(Comment).filter(Comment.id == id,
                                            Comment.user == current_user
                                            ).first()
    if comment:
        db_sess.delete(comment)
        db_sess.commit()
    else:
        abort(404)
    return redirect(f'/news/{comment.news_id}')


@app.route('/discovery')
def discovery():
    query = request.args.get('query', '')
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.title.ilike(f'%{query}%') | News.content.ilike(f'%{query}%')).all()
    users = db_sess.query(User).filter(User.name.ilike(f'%{query}%')).all()
    return render_template('discovery.html', news=news, users=users)


@app.route('/tags/<tag_name>')
def news_by_tag(tag_name):
    db_sess = db_session.create_session()
    tag = db_sess.query(Tags).filter_by(name=tag_name).first()
    news = tag.tags_news
    return render_template('news_by_tag.html', news=news, tag=tag)


@app.route('/like/<int:new_id>')
@login_required
def like_post(new_id):
    db_sess = db_session.create_session()
    post = db_sess.query(News).get(new_id)
    like = Like(users=current_user, news=post)
    db_sess.add(like)
    db_sess.commit()
    return redirect(f'/news/{new_id}')


@app.route('/unlike/<int:new_id>')
@login_required
def unlike_post(new_id):
    db_sess = db_session.create_session()
    post = db_sess.query(News).get(new_id)
    like = db_sess.query(Like).filter_by(user_id=current_user.id, news_id=post.id)
    db_sess.delete(like)
    db_sess.commit()
    return redirect(f'/news/{new_id}')


@app.route('/subscribe/<int:user_id>')
@login_required
def subscribe(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    user.follow(current_user)
    db_sess.commit()
    db_sess.close()
    return redirect(url_for('user_profile', id=user_id))


@app.route('/unsubscribe/<int:user_id>')
@login_required
def unsubscribe(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    user.unfollow(current_user)
    db_sess.commit()
    db_sess.close()
    return redirect(url_for('user_profile', id=user_id))


@app.route("/settings")
@login_required
def settings():
    return render_template('settings.html')


@app.route('/user_delete/<int:user_id>')
@login_required
def delete_account(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    news = db_sess.query(News).filter(News.user_id == user_id).all()
    comments = db_sess.query(Comment).filter(Comment.news_id == id).all()
    if news:
        img = news.image_path
        if os.path.exists(img):
            os.remove(img)
        db_sess.delete(news)
        db_sess.delete(user)
        if comments:
            for i in comments:
                db_sess.delete(i)
        db_sess.commit()
    else:
        abort(404)
    return redirect(f'/news_log')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
        return jsonify({'url': f"/static/uploads/{unique_name}"})

    return jsonify({'error': 'Invalid file type'}), 400


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def close_db(e=None):
    db = getattr(app, '_database', None)
    if db is not None:
        db.close()


if not os.path.exists('schema.sql'):
    with open('schema.sql', 'w') as f:
        f.write("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            reply_to INTEGER,
            new_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (reply_to) REFERENCES messages (id),
            FOREIGN KEY (new_id) REFERENCES news (id)
        );

        CREATE TABLE IF NOT EXISTS reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reaction_type TEXT CHECK(reaction_type IN ('like', 'dislike')),
            new_id INTEGER NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (new_id) REFERENCES news (id),
            UNIQUE(message_id, user_id, new_id)
        );
        """)

init_db()


@app.route('/send_message/<int:new_id>', methods=['POST'])
def send_message(new_id):
    text = request.form['text']
    reply_to = request.form.get('reply_to', type=int)

    db = get_db()
    db.execute(
        'INSERT INTO messages (user_id, text, reply_to, new_id) VALUES (?, ?, ?)',
        (current_user.id, text, reply_to, new_id)
    )
    db.commit()

    return redirect(url_for('watch_new', id=new_id))


@app.route('/react/<int:message_id>/<reaction_type>')
def react(message_id, reaction_type):
    db = get_db()

    # Удаляем предыдущую реакцию пользователя на это сообщение
    db.execute(
        'DELETE FROM reactions WHERE message_id = ? AND user_id = ?',
        (message_id, current_user.id)
    )

    # Добавляем новую реакцию
    if reaction_type in ('like', 'dislike'):
        db.execute(
            'INSERT INTO reactions (message_id, user_id, reaction_type) VALUES (?, ?, ?)',
            (message_id, current_user.id, reaction_type)
        )

    db.commit()
    return redirect(url_for('news_log'))


if __name__ == '__main__':
    main()
