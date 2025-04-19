from flask import Flask, render_template, redirect, request, url_for, abort
from data.users import User
from forms.user import RegisterForm
from forms.login_form import LoginForm
from data.news import News
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from forms.news import NewsForm
from data.comment import Comment
from forms.comments import CommentForm
from forms.research_form import SearchForm
from data.tags import Tags

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
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
def reqister():
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
            tag = Tags.query.filter_by(name=name).first()
            if not tag:
                tag = Tags(name=name)
                db_sess.add(tag)
            new.tags.append(tag)

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
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    comments = db_sess.query(Comment).filter(Comment.news_id == id).all()
    if news:
        db_sess.delete(news)
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


@app.route('/')
def index():
    db_sess = db_session.create_session()
    news = db_sess.query(News).all()
    form = SearchForm()
    if form.validate_on_submit():
        return
    return render_template('index.html', news=news, form=form)


@app.route('/discovery')
def discovery():
    query = request.args.get('query', '')
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.title.ilike(f'%{query}%') | News.content.ilike(f'%{query}%')).all()
    users = db_sess.query(User).filter(User.name.ilike(f'%{query}%')).all()
    return render_template('discovery.html', news=news, users=users)


@app.route('/tags/<tag_name>')
def tags(tag):
    db_sess = db_session.create_session()
    tag1 = db_sess.query(Tags).filter(Tags.title == tag).first()
    news = db_sess.query(News).filter(News == tag1.new).all()
    return render_template('index.html', news=news)


if __name__ == '__main__':
    main()
