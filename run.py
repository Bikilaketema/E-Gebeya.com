from packages import app
from flask_migrate import Migrate
from packages import app, db  # Replace 'your_flask_app' with the actual name of your Flask application

migrate = Migrate(app, db)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
