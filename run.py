from flask import Flask
from config import Config
from database import db
from app.routes.role_routes import role_bp
from app.routes.upload_routes import upload_bp
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)
    
    # Initializing SQLAlchemy with the app
    db.init_app(app)
    
    # Registering the blueprint for endpoints with a URL prefix
    app.register_blueprint(role_bp, url_prefix='/api/roles')
    app.register_blueprint(upload_bp, url_prefix='/api/files')

    
    # Create tables if they don't exist (optional – in production, use migrations)
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

if __name__ == '__main__':
    print(app.url_map)
    app.run(host='0.0.0.0', port=5006, debug=True)
