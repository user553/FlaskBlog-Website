from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

import pymysql
pymysql.install_as_MySQLdb()

application = Flask(__name__)
application.config['SECRET_KEY'] = '3acb3d064226b340103bb84fe5a0cfb3'
application.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://c2078482:Neetash1234@csmysql.cs.cf.ac.uk/c2078482_cmt120_website?charset=utf8'

db = SQLAlchemy(application)
bcrypt = Bcrypt(application)
login_manager = LoginManager(application)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from flaskblog import routes
from flaskblog import models

db.create_all()