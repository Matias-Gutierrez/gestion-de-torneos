import pytest
from flask import Flask

@pytest.fixture(scope='module')
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        yield app

@pytest.fixture(scope='module')
def db(app):
    from flaskapp.database.models import db
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield db
        db.drop_all()