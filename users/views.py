# IMPORTS
from datetime import datetime
import logging
from functools import wraps
from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from lottery.views import lottery
from models import User
from users.forms import RegisterForm, LoginForm
from werkzeug.security import check_password_hash
import pyotp

# CONFIG
users_blueprint = Blueprint('users', __name__, template_folder='templates')


# VIEWS
# view registration
@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # create signup form object
    form = RegisterForm()

    # if request method is POST or form is valid
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # if this returns a user, then the email already exists in database

        # if email already exists redirect user back to signup page with error message so user can try again
        if user:
            flash('Email address already exists')
            return render_template('register.html', form=form)

        # create a new user with the form data
        new_user = User(email=form.email.data,
                        firstname=form.firstname.data,
                        lastname=form.lastname.data,
                        phone=form.phone.data,
                        password=form.password.data,
                        pin_key=form.pin_key.data,
                        role='user')

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        # sends user to login page
        return redirect(url_for('users.login'))
    # if request method is GET or form not valid re-render signup page
    return render_template('register.html', form=form)


# view user login
@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if not session.get("logins"):
        session["logins"]=0
    elif session.get("logins")>=3:
        flash("Too many incorrect logins.")
    form = LoginForm()

    if form.validate_on_submit():
        #increase login attempts by 1
        session['logins']+=1

        user = User.query.filter_by(email=form.username.data).first()

        if not user or not check_password_hash(user.password, form.password.data):
            if session['logins']==3:
                flash("Too many incorrect logins.")
            elif session['logins']==2:
                flash("Please check ur login details and try again. 1 attempt remaining")
            else:
                flash('Please check your login details and try again. 2 attempts remaining.')

            return render_template('login.html', form=form)

        if pyotp.TOTP(user.pin_key).verify(form.pin.data):

            session["logins"] = 0
            login_user(user)

            user.last_logged_in = user.current_logged_in
            user.current_logged_in = datetime.now()
            db.session.add(user)
            db.session.commit()

            return profile()
        else:
            flash("You have supplied an invalid 2FA token!", "danger")

    return render_template('login.html', form=form)


# view logout
@users_blueprint.route('/logout')
@login_required
def logout():
    session['logins'] = 0
    logout_user()
    return redirect(url_for('index'))


# view user profile
@users_blueprint.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=(current_user.firstname + " " + str(current_user.lastname)))


# view user account
@users_blueprint.route('/account')
@login_required
def account():
    return render_template('account.html',
                           acc_no=current_user.id,
                           email=current_user.email,
                           firstname=current_user.firstname,
                           lastname=current_user.lastname,
                           phone=current_user.phone)
