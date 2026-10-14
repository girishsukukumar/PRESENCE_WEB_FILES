from flask import (Flask, render_template, request, redirect,
                   url_for, session, send_from_directory)

from werkzeug.security import check_password_hash
from functools import wraps



app = Flask(__name__)
# gentlesteps.wsgi also sets secret_key; keep one value in both places or remove one
app.secret_key = "0x413455aabdff9cd58pfc"
PAGES_DIR = "/var/www/gentlesteps/pages"
PROTECTED_PAGE = "welcome.html"
# login name -> password hash (paste the hash generated above)
USERS = {
    "admin": "scrypt:32768:8:1$BaHH7DlePjfkoz9r$167ccd3c34cdc12bda046b1be7f24a216a58e5771a5f184c63b49b789fa571fa1e72049fa83ae1e5d8b72a7e0f150242f951c7dda7ad6700544514fb86267966",
    "prachi": "scrypt:32768:8:1$9ZL1ioOz27JPVYgr$04df5a5c72df99eb159dfdee64f0b7aa9d1615d2191656527f81bb5cbffdb519906d3dad8e858c25657dc3be2f11113a3b62f85329d82bf52510509bfdd59662"
}


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("home"))
    return render_template("login.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return redirect(url_for("index"))


    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    stored_hash = USERS.get(username)
    if stored_hash and check_password_hash(stored_hash, password):
        session.clear()
        session["user"] = username
        return redirect(url_for("home"))
    return render_template("login.html",
                           error="Invalid login name or password."), 401





@app.route("/home")
@login_required
def home():
    response = send_from_directory(PAGES_DIR, PROTECTED_PAGE)
    response.headers["Cache-Control"] = "no-store"
    return response



@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run()
