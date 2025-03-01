# Chess Sansar Backend

This is the backend for the Chess Sansar project, a web-based chess application. The backend is built using Django and Django Channels to support real-time WebSocket communication for live chess games. It also uses Django REST Framework for API endpoints and Djoser for authentication.

## Project Structure
```
backend/
├── .env
├── backend/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── chess_app/
│   ├── __init__.py
│   ├── admin.py
│   ├── apiviews.py
│   ├── apps.py
│   ├── consumers.py
│   ├── middlewares.py
│   ├── migrations/
│   ├── models.py
│   ├── routing.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── requirements.txt
└── manage.py
```

## Installation Instructions

1. **Clone the repository:**
    ```sh
    git clone https://github.com/NishanBhattarai327/ChessSansar.git
    cd ChessSansar/backend
    ```

2. **Create a virtual environment and activate it:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4. **Configure environment:**
    Create a `.env` file in the root directory:
    ```
    SECRET_KEY = provide-django-secret-key
    DEBUG = True

    EMAIL_USER = emal to send email for activation
    EMAIL_PASS = email password

    EMAIL_TO_CONSOLE = True "use console for email instead"
    FRONTEND_API = 'localhost:5173'  "api of chess-sansar frontend"
    ```

5. **Setup database:**
    ```sh
    python manage.py migrate
    python manage.py createsuperuser
    ```

6. **Start development server:**
    ```sh
    python manage.py runserver
    ```

## API Documentation

### REST Endpoints
- **Authentication**
  - Register: `POST /auth/users/`
  - Login: `POST /auth/token/login/`
  - Logout: `POST /auth/token/logout/`

### WebSocket Endpoints
- **Game Management**
  - Create/Join Game: `ws://localhost:8000/ws/chess/{game_id}/`
  - Game Moves: `ws://localhost:8000/ws/chess/{game_id}/`


Production API: `https://api.chess-sansar.com/`

## Technologies Used
- Django 5.x
- Django Channels
- Django REST Framework
- Djoser
- WebSockets
- SQLite