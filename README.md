# NewsHub — News Information Website

NewsHub is a polished, responsive full-stack news discovery platform built with Flask, SQLite and the GNews API. It presents current stories in a focused editorial interface while giving registered readers a private bookmark library.

## Features

- Live GNews headlines and keyword search through a server-side API service
- Home page hero story, breaking ticker, latest news and category sections
- General, World, Nation, Business, Technology, Entertainment, Sports, Science and Health categories
- Article detail pages linking to the original publisher
- Registration, login, logout, password hashing and remember-me sessions
- User profile editing and protected bookmarks with save/remove actions
- Contact form stored in SQLite
- Optional admin dashboard using the `admin` user role
- Friendly API, validation, authentication, 403, 404 and 500 error handling
- Responsive layout for desktop, tablet and mobile
- Light/dark theme persisted with `localStorage`
- Lazy-loaded images with an SVG fallback placeholder
- Accessible labels, semantic landmarks, keyboard-friendly controls and dismissible flash messages

## Technology

- HTML5, CSS3 and JavaScript
- Python 3.10+ and Flask
- Flask-SQLAlchemy with SQLite
- Flask-Login
- Requests and python-dotenv
- GNews API

## Project structure

```text
GNEWS/
├── app.py
├── config.py
├── models.py
├── requirements.txt
├── .env.example
├── .gitignore
├── services/
│   ├── __init__.py
│   └── news_api.py
├── templates/
│   ├── base.html, macros.html, index.html
│   ├── category.html, search.html, article.html
│   ├── login.html, register.html, profile.html, bookmarks.html
│   ├── about.html, contact.html, admin.html, error.html
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   └── images/news-placeholder.svg
└── instance/                 # created automatically; local SQLite database
```

## Windows installation

Open Command Prompt or PowerShell in the project directory:

```bat
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If `python` is not recognized, install Python from python.org and enable **Add Python to PATH** during setup.

## Environment variables

Copy the example file to `.env`:

```bat
copy .env.example .env
```

Edit `.env` and add a GNews API key from [gnews.io](https://gnews.io/):

```env
GNEWS_API_KEY=PASTE_YOUR_GNEWS_KEY_HERE
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=sqlite:///news.db
```

Never commit `.env`. It is excluded by `.gitignore`. The app will still load without a key so that the UI and authentication can be tested; news pages show a friendly configuration message.

## Run

With the virtual environment activated:

```bat
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The `instance/news.db` SQLite database and all tables are created automatically on first startup.

To stop the development server, press `Ctrl+C`.

## Create an administrator

Register a normal account first, then run this command from the project directory:

```bat
python -c "from app import app; from models import db, User; from sqlalchemy import select; username=input('Username: '); user=db.session.scalar(select(User).where(User.username==username)); user.role='admin'; db.session.commit(); print('Admin role assigned.') if user else print('User not found.')"
```

The account can then access `/admin`.

## Route map

| Route | Purpose | Access |
|---|---|---|
| `/` | Home and live sections | Public |
| `/category/<category>` | Category headlines and pagination | Public |
| `/search?q=technology` | Keyword search | Public |
| `/article?...` | Normalized article detail | Public |
| `/register`, `/login`, `/logout` | Authentication | Public / authenticated |
| `/profile` | Edit account profile | Login required |
| `/bookmarks` | Saved articles | Login required |
| `/bookmark/add`, `/bookmark/remove/<id>` | Bookmark actions | Login required |
| `/about`, `/contact` | Informational and contact pages | Public |
| `/admin` | Users, bookmarks and messages | Admin only |

## Testing checklist

### Authentication

- Register with valid data and confirm a hashed password is stored.
- Try a missing field, invalid email, short password and mismatched confirmation.
- Try duplicate email and username.
- Log in with email and username, then try an incorrect password.
- Test remember-me, logout and protected page redirects.

### News

- Confirm the home hero, latest cards and category sections load with a valid API key.
- Visit each category, search for `technology`, and move between result pages.
- Open an article, check its original publisher link and test the missing-image fallback.
- Temporarily remove `GNEWS_API_KEY` or disable internet to confirm the friendly error notice.

### Bookmarks and contact

- Save an article while logged in, visit `/bookmarks`, and remove it.
- Click save while logged out and confirm the login redirect.
- Submit a valid contact message and verify it in the `ContactMessage` table/admin dashboard.

### Responsive and accessibility

- Test 1920px, 1440px, 1024px, 768px, 480px, 375px and 320px widths.
- Test mobile menu, theme toggle persistence, keyboard focus, image alt text and flash dismissal.

## Troubleshooting

- **`ModuleNotFoundError`**: activate `venv` and run `pip install -r requirements.txt`.
- **API key message**: verify the file is named `.env`, the variable is `GNEWS_API_KEY`, and restart Flask after editing it.
- **GNews 401/403/429**: generate a valid key, check plan limits, or wait for the rate limit to reset.
- **No news but app works**: no key, no internet, or the API returned no articles; authentication and static pages remain usable.
- **SQLite error**: stop Flask, ensure the `instance` folder exists, and restart. The app calls `db.create_all()` automatically.
- **`TemplateNotFound`**: run `python app.py` from the project root and ensure the requested file exists in `templates`.
- **CSS or images missing**: use the root URL generated by Flask, not a file URL, and hard-refresh the browser with `Ctrl+F5`.
- **Login not working**: check that `SECRET_KEY` is set and the account email/username is entered correctly.
- **Stale database schema**: for a new local project, stop the app and delete `instance/news.db`, then restart. Do not do this if you need existing local data.

## Security notes

Passwords are stored using Werkzeug's password hashing. The GNews key is only used by Flask and is never sent to browser JavaScript. Login-required routes use Flask-Login, bookmark ownership is checked on every mutation, and external article URLs are validated before being accepted.

This project is intended for portfolio and educational use. Article text, images and attribution are supplied by the original publishers through GNews.
"# GNEWS"  
