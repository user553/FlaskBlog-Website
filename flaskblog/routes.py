import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, session, json
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, CommentForm
from flaskblog.models import User, Post, Comment
from flaskblog import application, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
import datetime
from sqlalchemy import or_


@application.route("/")
@application.route("/home", methods=['GET', 'POST'])
def home():
    form = CommentForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        comment = Comment(comm=form.comment.data, author=current_user, post_id=form.post_id.data)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted', 'success')
        return redirect(url_for('home'))
    page =  request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted)
    comms = Comment.query.order_by(Comment.date_comm)
    print(comms)
    return render_template('home.html', posts=posts, comments=comms, form=form, title='Home')

@application.route("/about")
def about():
    return render_template('about.html', title='about')

@application.route("/signup", methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()    
        flash(f'Your account has been created', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', title='signup', form=form)

@application.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
       user = User.query.filter_by(email=form.email.data).first()
       if user and bcrypt.check_password_hash(user.password, form.password.data):
           session['user'] = user.username
           login_user(user, remember=form.remember.data)
           next_page = request.args.get('next')
           return redirect(next_page) if next_page else redirect(url_for('home'))
       else:
            flash(f'Login Unsuccessful. Please check username and password', 'warning')
    return render_template('login.html', title='login', form=form)

@application.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    f_name, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(application.root_path, 'static/Images', picture_fn)
    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail = output_size
    i.save(picture_path)
    return picture_fn

@application.route("/post/new", methods = ['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        picture_file = 'default.png'
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
        post = Post(title=form.title.data, image_file=picture_file, content=form.content.data, tags=form.tags.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title = 'New Post', form = form, legend='New Post', author='Neetash', date=datetime.date.today())
 
@application.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author.username != current_user.username:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        picture_file = 'default.png'
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
        post.title = form.title.data
        post.content = form.content.data
        post.tags = form.tags.data
        post.image_file = picture_file
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('home'))
    elif request.method == 'GET':
        form.title.data = post.title 
        form.content.data = post.content
        form.tags.data = post.tags
    image_file =  url_for('static', filename='Images/' + post.image_file)
    return render_template('create_post.html', title='Update post', form=form, image_file=image_file, legend='Update Post')
 
@application.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author.username != current_user.username:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted', 'success')
    return redirect(url_for('home'))

@application.route("/user/<string:username>")
@login_required
def user_posts(username):
    page =  request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page = 3)
    return render_template('user_posts.html', posts=posts, user=user, title="all_blogs")

@application.route("/search", methods=['POST'])
@login_required
def search_post():
    page =  request.args.get('page', 1, type=int)
    keyword = request.form.get("search")
    posts = Post.query
    posts = posts.filter(or_(Post.title.like('%' + keyword + '%'), Post.content.like('%' + keyword + '%'), Post.tags.like('%' + keyword + '%')))
    posts = posts.order_by(Post.title).all()
    comms = Comment.query.order_by(Comment.date_comm)
    msg = "Total results found: " + str(len(posts))
    flash(msg, 'info')
    return render_template('home.html', title="Home", posts=posts, comments=comms)

@application.route("/like", methods=['POST'])
@login_required
def like_post():
    post_id = request.form.get("id").split("-")[1]
    user_id = current_user.id

    post = Post.query.get_or_404(post_id)
    if post.liked_by:
        likes = post.liked_by.split(",")
        likes = [str(a) for a in likes]

        if str(current_user.id) in likes:
            likes.remove(str(current_user.id))
        else:
            likes.append(str(current_user.id))
        temp = ','.join(likes)
        post.liked_by = temp
    else:
        post.liked_by = str(user_id)
    
    db.session.commit()

    return json.dumps({"success": "updated"})