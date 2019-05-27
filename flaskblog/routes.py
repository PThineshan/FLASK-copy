from flask import render_template, url_for, flash, redirect, request
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, PostForm
from flaskblog.models import User,Post
from flask_login import login_user, current_user, logout_user, login_required
import pickle

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
def preprocess(data):
    stopWords = set(stopwords.words('english'))
    words = word_tokenize(data)
    wordsFiltered = []
    for w in words:
        if w not in stopWords:
            wordsFiltered.append(w)

    #print(wordsFiltered)
    #print(nltk.pos_tag(wordsFiltered))
    review=nltk.pos_tag(wordsFiltered)
    #print(review)

    a=[]
    for pos in review:
        a.append("/".join(pos))
    #print(a)
    #print(" ".join(a))
    return " ".join(a)

@app.route("/")
def homepage():
    return render_template('homepage.html',title='Homepage')



@app.route("/review")
@login_required
def review():
    posts = Post.query.filter_by(user_id=current_user.id).all()
    return render_template('review.html', title='Review', posts=posts)


@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    pkl = open('mlmodel.pickle', 'rb')
    vec = open('vectorizer.pickle', 'rb')

    clf = pickle.load(pkl)
    v = pickle.load(vec)
    form = PostForm()
    if form.validate_on_submit():
        review = form.content.data
        data = [preprocess(review)]
        vect = v.transform(data).toarray()
        my_prediction = clf.predict(vect)
        if my_prediction == 'deceptive':
            form.result.data = 'deceptive'
            flash('This review is considered as A FAKE REVIEW!!!', 'danger')
        elif my_prediction == 'truth':
            form.result.data = 'truth'
            flash('This review is considered as NOT A FAKE REVIEW!!!', 'success')
        post = Post(content=form.content.data, result=form.result.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()

        #return redirect(url_for('review'))
    return render_template('home.html', title='Home', form=form)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('homepage'))

