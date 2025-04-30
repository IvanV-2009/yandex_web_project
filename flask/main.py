from flask import Flask, render_template, redirect, request, url_for, abort, send_from_directory, jsonify
from data.users import User
from data.likes import Like
from forms.user import RegisterForm
from forms.login_form import LoginForm
from data.news import News
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from forms.news import NewsForm
from data.comment import Comment
from forms.comments import CommentForm
from data.tags import Tags
from werkzeug.utils import secure_filename
import os
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

upload_folder = os.path.join('static', 'uploads')

app.config['UPLOAD'] = upload_folder

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
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        new = News(title=form.title.data,
                   content=form.content.data,
                   user_id=current_user.id)

        tag_names = [t.strip().lower() for t in form.tags.data.split(',')]
        for name in tag_names:
            tag = db_sess.query(Tags).filter_by(name=name).first()
            if not tag:
                tag = Tags(name=name)
                db_sess.add(tag)
            new.tags.append(tag)
        img = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD'], filename))
                img = os.path.join(app.config['UPLOAD'], filename)
                im = Image.open(img)
                im.thumbnail((400, 400))
                im.save(img)
        new.image_path = img
        db_sess.add(new)
        db_sess.commit()
        return redirect('/news_log')
    return render_template('news.html', title='Новости', form=form)


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
    new = db_sess.query(News).filter(News.id == id).first()
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            db_sess = db_session.create_session()
            comment = Comment(content=form.content.data,
                              user_id=current_user.id,
                              news_id=id)
            db_sess.add(comment)
            db_sess.commit()
        else:
            return redirect('/register')
    comments = db_sess.query(Comment).filter(Comment.news_id == id).all()
    return render_template('new.html', new=new, form=form, comments=comments)


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
    news = db_sess.query(News).filter(News.id == id).first()
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
    user = db_sess.query(User).filter(User.id == user_id).first()
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


if __name__ == '__main__':
    main()
