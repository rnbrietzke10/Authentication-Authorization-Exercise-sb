import os
from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegistrationForm, LoginForm, FeedbackForm
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
            form.username.errors.append("Username is taken. Please pick a different username")
            return render_template('register.html', form=form)
        session["user_id"] = new_user.username
        flash(f"Welcome {new_user.first_name}, you successfully created your account", "success")
        return redirect(f'/user/{new_user.username}')

    return render_template('register.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login_user():
    if "user_id" in session:
        return redirect(f"/users/{session['user_id']}")
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.first_name}", "success")
            session["user_id"] = user.username
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ["Invalid username/password"]
    return render_template('login.html', form=form)


@app.route('/users/<username>')
def user_profile_route(username):
    if "user_id" not in session:
        flash("Please Login", "danger")
        return redirect("/login")
    user = User.query.get_or_404(username)
    feedback = Feedback.query.all()


    return render_template('secret.html', user=user, feedback=feedback)


# /users/{{user.username}}/delete

# /users/<username>/feedback/add
@app.route('/users/<username>/feedback/add', methods=["GET", "POST"])
def add_feedback(username):
    if "user_id" not in session:
        flash("Please Login", "danger")
        return redirect("/login")
    form = FeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(title=title, content=content, username=username)
        db.session.add(new_feedback)
        db.session.commit()
        flash("Feedback Added!", 'success')
        return redirect(f'/users/{username}')
    btn_text = "Add"
    return render_template('feedback.html', form=form, btn_text= btn_text)

# /feedback/{{feed.id}}/update
@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    if "user_id" not in session:
        flash("Please login first!", "danger")
        return redirect('/login')
    feedback = Feedback.query.get_or_404(feedback_id)
    user_feedback = {
        "title": feedback.title,
        "content": feedback.content
    }
    print(user_feedback)
    form = FeedbackForm(obj=user_feedback)
    btn_text= "Update"
    return render_template("feedback.html", form=form, btn_text=btn_text)



# /feedback/{{feed.id}}/delete

@app.route('/logout', methods=["POST"])
def logout_user():
    session.pop('user_id')
    flash("Successfully Logged Out!", "info")
    return redirect('/')

