from flask import Flask

# db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    from execute import main
    app.register_blueprint(main)
    return app