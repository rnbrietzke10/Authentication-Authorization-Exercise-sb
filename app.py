import os
from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User
from forms import RegistrationForm, LoginForm
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///flask_feedback_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = os.urandom(24)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)

connect_db(app)


@app.route('/')
def home_page():
    return redirect('/register')


@app.route('/register', methods=["GET", "POST"])
def register_user():
    form = RegistrationForm()
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        username = form.username.data
        password = form.password.data
        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append("Username is taken. Please pick a different username", "danger")
            return render_template('register.html', form=form)
        session["user_id"] = new_user.username
        flash(f"Welcome {new_user.first_name}, you successfully created your account", "success")
        return redirect('/secret')

    return render_template('register.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.first_name}", "success")
            session["user_id"] = user.username
            return redirect(f'/user/{user.username}')
        else:
            form.username.errors = ["Invalid username/password"]
    return render_template('login.html', form=form)


@app.route('/user/<username>')
def secret_route(username):
    if "user_id" not in session:
        flash("Please Login", "danger")
        return redirect("/login")
    user = User.query.get_or_404(username)


    return render_template('secret.html', user=user)


@app.route('/logout', methods=["POST"])
def logout_user():
    session.pop('user_id')
    flash("Successfully Logged Out!", "info")
    return redirect('/')

