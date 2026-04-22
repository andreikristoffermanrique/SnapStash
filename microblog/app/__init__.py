from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_migrate import upgrade
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)

# Initialize the Database tools
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize Login Manager
login = LoginManager(app)
login.login_view = 'login'

@login.user_loader
def load_user(id):
    from app.models import User
    return User.query.get(int(id))

from app import routes, models


with app.app_context():
    upgrade()