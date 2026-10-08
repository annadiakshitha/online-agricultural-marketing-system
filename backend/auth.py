"""Register / login / logout using Flask sessions and hashed passwords."""
import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from . import query, execute, current_user, account_type

bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _safe_next(target):
    return target if target and target.startswith("/") and not target.startswith("//") else None


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Please fill all required fields.", "error")
            return render_template("login.html"), 400
        user = query("SELECT * FROM users WHERE email=?", (email,), one=True)
        if not user or not check_password_hash(user["password"], password):
            flash("Invalid login credentials.", "error")
            return render_template("login.html", email=email), 401
        session.clear()
        session["user_id"] = user["id"]
        flash(f"Welcome back, {user['name'].split()[0]}!", "success")
        nxt = _safe_next(request.args.get("next") or request.form.get("next"))
        if nxt:
            return redirect(nxt)
        acct = account_type(user)
        return redirect(url_for({"seller": "main.seller_dashboard", "admin": "main.admin_dashboard", "farmer": "farmer.dashboard"}.get(acct, "main.index")))
    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = {k: request.form.get(k, "").strip() for k in ("name", "email", "phone", "role", "business", "location")}
        pw, pw2 = request.form.get("password", ""), request.form.get("confirm_password", "")
        f["email"] = f["email"].lower()
        error = None
        if not all([f["name"], f["email"], f["phone"], pw, pw2]):
            error = "Please fill all required fields."
        elif not EMAIL_RE.match(f["email"]):
            error = "Enter a valid email address."
        elif not re.fullmatch(r"(\+91[\s-]?)?[6-9]\d{9}", f["phone"]):
            error = "Enter a valid 10-digit Indian mobile number."
        elif len(pw) < 6:
            error = "Password must be at least 6 characters."
        elif pw != pw2:
            error = "Passwords do not match."
        elif f["role"] not in ("customer", "seller", "farmer"):
            error = "Please choose a role."
        elif query("SELECT 1 FROM users WHERE email=?", (f["email"],), one=True):
            error = "An account with this email already exists."
        if error:
            flash(error, "error")
            return render_template("register.html", form=f), 400
        selected_role = f["role"]
        try:
            uid = execute("INSERT INTO users (name,email,phone,password,role) VALUES (?,?,?,?,?)",
                          (f["name"], f["email"], f["phone"], generate_password_hash(pw), selected_role))
        except Exception as exc:
            # Databases created by older AgroConnect versions only allow customer/seller/admin.
            # Keep farmer identity through farmer_profiles until that legacy DB is replaced.
            if selected_role != "farmer" or "CHECK constraint failed" not in str(exc):
                raise
            uid = execute("INSERT INTO users (name,email,phone,password,role) VALUES (?,?,?,?,?)",
                          (f["name"], f["email"], f["phone"], generate_password_hash(pw), "customer"))
        if f["role"] == "farmer":                                   # farmer account gets a farm profile
            loc = [x.strip() for x in (f["location"] or "").split(",")]
            execute("INSERT INTO farmer_profiles (user_id,district,state) VALUES (?,?,?)", (uid, loc[0], loc[1] if len(loc) > 1 else ""))
        if f["role"] == "seller":
            execute("INSERT INTO sellers (user_id,business_name,location,verified) VALUES (?,?,?,0)",
                    (uid, f["business"] or f"{f['name']} Farms", f["location"] or "India"))
        session.clear()
        session["user_id"] = uid
        flash("Account created successfully. Welcome to AgroConnect!", "success")
        return redirect(url_for({"seller": "main.seller_dashboard", "farmer": "farmer.dashboard"}.get(f["role"], "main.index")))
    return render_template("register.html", form={})


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))
