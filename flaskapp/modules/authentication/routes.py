from flask import app, render_template, redirect, request, url_for, Blueprint
from flask_login import (
    current_user,
    login_user,
    logout_user
)
from flaskapp.database.models import db
from flaskapp import login_manager
from flaskapp.modules.authentication.forms import LoginForm, CreateAccountForm
from flaskapp.database.models import User
from flaskapp.modules.authentication.util import verify_pass

auth_blueprint = Blueprint(
    'authentication_blueprint',
    __name__,
    url_prefix=''
)

@auth_blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))


# Login & Registration

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        email = request.form['email']
        password = request.form['password']

        # Locate user
        user = User.query.filter_by(email=email).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('authentication/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('authentication/login.html',
                               form=login_form)
    else:
        if current_user.is_admin:
            return redirect(url_for('home_blueprint.index'))
        return redirect(url_for('organizations_blueprint.index'))

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        # Check size of the password < 8 characters
        if len(password) < 8 or len(password) > 16:
            return render_template('authentication/register.html',
                                   msg='La contraseña debe tener al menos 8 caracteres y menos de 16 caracteres',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('authentication/register.html',
                                   msg='El email ya esta registrado',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = User(**request.form)
        
        # Get a database session
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('authentication_blueprint.login'))

    else:
        return render_template('authentication/register.html', form=create_account_form)


@auth_blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))


# Errors
@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403