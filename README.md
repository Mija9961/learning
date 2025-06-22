# learning
# Create Virtual Environment
python -m venv venv-learning
# Activate it


my_flask_app/
├── venv/                     # Python Virtual Environment
├── run.py                    # Entry point to run the application
├── config.py                 # Application-wide configuration
├── requirements.txt          # Project dependencies
├── .flaskenv                 # For environment variables (optional, good practice)
├── app/                      # Main Flask application package
│   ├── __init__.py           # App factory, extension init, blueprint registration
│   ├── models.py             # Database models (User, Admin, App, etc.)
│   ├── extensions.py         # Initialize Flask extensions (DB, LoginManager)
│   ├── admin/                # Admin Blueprint
│   │   ├── __init__.py       # Initializes the blueprint
│   │   ├── routes.py         # Admin view functions (dashboard, manage users)
│   │   ├── forms.py          # Admin-specific forms (e.g., user management forms)
│   │   └── templates/
│   │       └── admin/
│   │           ├── base_admin.html   # Admin panel base layout
│   │           └── dashboard.html    # Admin dashboard
│   │           └── users.html        # Example: list users
│   ├── user/                 # User Blueprint (main user panel)
│   │   ├── __init__.py       # Initializes the blueprint
│   │   ├── routes.py         # User panel view functions (dashboard, profile)
│   │   ├── forms.py          # User-specific forms (e.g., profile update)
│   │   └── templates/
│   │       └── user/
│   │           ├── base_user.html    # User panel base layout
│   │           └── dashboard.html    # User dashboard
│   │           └── profile.html      # User profile page
│   ├── apps/                 # Directory for individual user-facing apps
│   │   ├── __init__.py       # (Can be empty or handle app registration)
│   │   ├── app1/             # User App 1 Blueprint
│   │   │   ├── __init__.py
│   │   │   ├── routes.py     # App1 specific routes
│   │   │   ├── forms.py      # App1 specific forms (if any)
│   │   │   └── templates/
│   │   │       └── apps/
│   │   │           └── app1/
│   │   │               └── index.html  # App1 main page
│   │   ├── app2/             # User App 2 Blueprint (similar structure)
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── forms.py
│   │   │   └── templates/
│   │   │       └── apps/
│   │   │           └── app2/
│   │   │               └── index.html
│   │   └── ...               # You can add more apps here
│   ├── auth/                 # Authentication Blueprint (login, register, logout)
│   │   ├── __init__.py       # Initializes the blueprint
│   │   ├── routes.py         # Auth view functions
│   │   ├── forms.py          # Auth forms (login, registration)
│   │   └── templates/
│   │       └── auth/
│   │           ├── login.html
│   │           └── register.html
│   ├── static/               # Global static files (e.g., global CSS, JS, favicon)
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   └── templates/            # Global base templates (e.g., for login/register, or a very generic base)
│       ├── base.html         # Main application base layout
│       └── home.html         # Landing page for unauthenticated users
├── migrations/               # Flask-Migrate directory (created after `flask db init`)
├── tests/                    # Unit/integration tests (optional for initial setup)
│   └── __init__.py
│   └── test_auth.py


# Database migrate
flask db init
flask db migrate
flask db upgrade


# Project Name

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## Installation
Instructions for installation...

## Usage
Instructions for usage...

## Configuration
Details about configuration...

## Examples
Code examples, screenshots, or output...

## Contributing
Guidelines for contributions...

## License
Information about the license...
