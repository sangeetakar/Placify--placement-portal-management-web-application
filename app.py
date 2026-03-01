from flask import Flask 
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# -----------------------------
# Load Configuration
# -----------------------------
from config import Config
app.config.from_object(Config)

# -----------------------------
# Initialize Database
# -----------------------------
from models import db
db.init_app(app)

from models import init_db

with app.app_context():
    init_db()
# -----------------------------
# Register Blueprints
# -----------------------------
from routes import bp
app.register_blueprint(bp)


if __name__=='__main__':
    app.run(debug=True) #we can see the error in the browser as well