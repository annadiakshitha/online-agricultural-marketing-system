"""AgroConnect - Farmer E-Commerce Marketplace (Flask entry point)."""
import os
from flask import Flask, render_template, request, jsonify, abort
from config import Config, GENERIC_REMOTE
from backend import close_db, csrf_token, check_csrf, current_user, account_type, image_url, query, sale_price, ORDER_STATUSES
from backend.auth import bp as auth_bp
from backend.products import bp as products_bp
from backend.cart import bp as cart_bp
from backend.orders import bp as orders_bp
from backend.users import bp as users_bp
from backend.tracking import bp as tracking_bp
from backend.assistant import bp as assistant_bp
from backend.coupons import bp as coupons_bp
from backend.invoice import bp as invoice_bp
from backend.rentals import bp as rentals_bp
from backend.cropdoctor import bp as cropdoctor_bp
from backend.tools import bp as tools_bp
from backend.farmer import bp as farmer_bp
from backend.migrate import ensure as ensure_extras


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["GENERIC_REMOTE"] = GENERIC_REMOTE

    # First run: create + seed the database automatically.
    if not os.path.exists(app.config["DATABASE"]):
        from database.seed import build
        build(app.config["DATABASE"])

    ensure_extras(app.config["DATABASE"])      # additive tables: rentals, coupons

    for bp in (users_bp, auth_bp, products_bp, cart_bp, orders_bp, tracking_bp, assistant_bp, coupons_bp, invoice_bp, rentals_bp, cropdoctor_bp, tools_bp, farmer_bp):
        app.register_blueprint(bp)
    app.teardown_appcontext(close_db)

    @app.before_request
    def protect():
        if not check_csrf():
            if request.is_json or request.path.startswith("/api") or request.method in ("PUT", "DELETE"):
                return jsonify(ok=False, error="Session expired. Please refresh the page."), 400
            abort(400)

    @app.context_processor
    def inject():
        u = current_user()
        acct = account_type(u)
        is_farmer = acct == "farmer"
        nav_categories = query("SELECT name, slug FROM categories WHERE audience=? ORDER BY id", (acct,)) if acct in ("customer", "farmer") else []
        return dict(csrf_token=csrf_token, current_user=u, account_type=acct, is_farmer=is_farmer, img=image_url, sale_price=sale_price,
                    order_statuses=ORDER_STATUSES, nav_categories=nav_categories, cfg=app.config)

    @app.template_filter("inr")
    def inr(v):
        return "₹{:,.0f}".format(v or 0)

    @app.template_filter("date")
    def fmt_date(v, fmt="%d %b %Y"):
        from datetime import datetime
        try:
            return datetime.fromisoformat(str(v)).strftime(fmt)
        except ValueError:
            return v

    @app.errorhandler(404)
    def not_found(_e):
        if request.path.startswith("/api"):
            return jsonify(ok=False, error="Not found"), 404
        return render_template("404.html"), 404

    @app.errorhandler(400)
    def bad_request(_e):
        return render_template("404.html", code=400, title="Bad Request",
                               message="Your session expired or the request was invalid. Please go back and try again."), 400

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify(ok=False, error="File is too large (max 4 MB)."), 413

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("404.html", code=500, title="Something went wrong",
                               message="We hit a problem on our side. Please try again in a moment."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
