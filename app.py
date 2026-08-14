import re
from functools import wraps
from urllib.parse import urljoin, urlparse

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from config import Config
from models import Bookmark, ContactMessage, User, db
from services import NewsAPIService


login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Please login first."
login_manager.login_message_category = "warning"

CATEGORIES = ["general", "world", "nation", "business", "technology", "entertainment", "sports", "science", "health"]
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def is_safe_url(target):
    reference = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in {"http", "https"} and reference.netloc == test.netloc


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_globals():
        return {"categories": CATEGORIES}

    @app.get("/")
    def index():
        latest, error = NewsAPIService.top_headlines(limit=10)
        sections = {}
        for category in ("technology", "business", "sports", "science", "health"):
            articles, _ = NewsAPIService.top_headlines(category, limit=4)
            sections[category] = articles
        return render_template("index.html", articles=latest, featured=latest[0] if latest else None, sections=sections, api_error=error)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirmation = request.form.get("confirm_password", "")
            errors = []
            if not all((name, username, email, password, confirmation)):
                errors.append("All fields are required.")
            if email and not EMAIL_PATTERN.match(email):
                errors.append("Enter a valid email address.")
            if len(password) < 8:
                errors.append("Password must contain at least 8 characters.")
            if password != confirmation:
                errors.append("Password confirmation does not match.")
            if User.query.filter_by(email=email).first():
                errors.append("An account with that email already exists.")
            if User.query.filter_by(username=username).first():
                errors.append("That username is already in use.")
            if errors:
                for error in errors:
                    flash(error, "danger")
            else:
                user = User(name=name, username=username, email=email)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash("Registration successful! You can now log in.", "success")
                return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        if request.method == "POST":
            identity = request.form.get("identity", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter(or_(User.email == identity, User.username == identity)).first()
            if not user:
                flash("User not found.", "danger")
            elif not user.check_password(password):
                flash("Incorrect password.", "danger")
            else:
                login_user(user, remember=request.form.get("remember") == "on")
                flash("Welcome back!", "success")
                next_page = request.args.get("next")
                return redirect(next_page if next_page and is_safe_url(next_page) else url_for("index"))
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            username = request.form.get("username", "").strip()
            duplicate = User.query.filter(User.username == username, User.id != current_user.id).first()
            if not name or not username:
                flash("Name and username are required.", "danger")
            elif duplicate:
                flash("That username is already in use.", "danger")
            else:
                current_user.name, current_user.username = name, username
                db.session.commit()
                flash("Profile updated successfully.", "success")
                return redirect(url_for("profile"))
        return render_template("profile.html")

    @app.get("/category/<category>")
    def category(category):
        category = category.lower()
        if category not in CATEGORIES:
            abort(404)
        page = max(request.args.get("page", 1, type=int), 1)
        articles, error = NewsAPIService.top_headlines(category, page=page, limit=10)
        return render_template("category.html", category=category, articles=articles, api_error=error, page=page)

    @app.get("/search")
    def search():
        query = request.args.get("q", "").strip()
        page = max(request.args.get("page", 1, type=int), 1)
        articles, error = (NewsAPIService.search(query, page=page) if query else ([], None))
        return render_template("search.html", query=query, articles=articles, api_error=error, page=page)

    @app.get("/article")
    def article():
        item = NewsAPIService.article_from_request(request.args)
        if not item:
            abort(404)
        return render_template("article.html", article=item)

    @app.get("/bookmarks")
    @login_required
    def bookmarks():
        items = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.created_at.desc()).all()
        return render_template("bookmarks.html", bookmarks=items)

    @app.post("/bookmark/add")
    @login_required
    def add_bookmark():
        article_url = request.form.get("article_url", "").strip()
        if not article_url or urlparse(article_url).scheme not in {"http", "https"}:
            flash("This article cannot be saved.", "danger")
        elif Bookmark.query.filter_by(user_id=current_user.id, article_url=article_url).first():
            flash("This article is already saved.", "info")
        else:
            db.session.add(Bookmark(
                user_id=current_user.id,
                title=request.form.get("title", "Untitled")[:500],
                description=request.form.get("description", ""),
                image_url=request.form.get("image_url", ""),
                article_url=article_url,
                source=request.form.get("source", "Unknown source")[:255],
                published_at=request.form.get("published_at", "")[:80],
            ))
            db.session.commit()
            flash("Article saved successfully.", "success")
        return redirect(request.referrer or url_for("bookmarks"))

    @app.post("/bookmark/remove/<int:bookmark_id>")
    @login_required
    def remove_bookmark(bookmark_id):
        item = Bookmark.query.filter_by(id=bookmark_id, user_id=current_user.id).first_or_404()
        db.session.delete(item)
        db.session.commit()
        flash("Article removed from bookmarks.", "success")
        return redirect(url_for("bookmarks"))

    @app.get("/about")
    def about():
        return render_template("about.html")

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            subject = request.form.get("subject", "").strip()
            message = request.form.get("message", "").strip()
            if not all((name, email, subject, message)) or not EMAIL_PATTERN.match(email):
                flash("Complete every field with a valid email address.", "danger")
            else:
                db.session.add(ContactMessage(name=name, email=email, subject=subject, message=message))
                db.session.commit()
                flash("Message sent successfully.", "success")
                return redirect(url_for("contact"))
        return render_template("contact.html")

    @app.get("/admin")
    @admin_required
    def admin():
        return render_template(
            "admin.html",
            user_count=User.query.count(),
            bookmark_count=Bookmark.query.count(),
            messages=ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(20).all(),
            recent_users=User.query.order_by(User.created_at.desc()).limit(10).all(),
        )

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, title="Access denied", message="You do not have permission to view this page."), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, title="Page not found", message="The page you're looking for doesn't exist."), 404

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return render_template("error.html", code=500, title="Something went wrong", message="We could not complete your request. Please try again."), 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
