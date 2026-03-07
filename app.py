from flask import Flask 
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

import os

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'resumes')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  

from config import Config
app.config.from_object(Config)


from models import db
db.init_app(app)

from models import init_db

with app.app_context():
    init_db()
from routes import bp
app.register_blueprint(bp)


if __name__=='__main__':
    app.run(debug=True) #we can see the error in the browser as well