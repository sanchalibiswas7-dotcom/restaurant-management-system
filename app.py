# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime
import os

from config import Config
from models import db, User, DiningTable, MenuItem, Customer, Order, OrderItem, Payment


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure instance folder exists
    os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)

    # Initialize DB
    db.init_app(app)

    with app.app_context():
        db.create_all()
        create_default_admin()

    # ---------- Helper: login_required decorator ----------

    def login_required(role=None):
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                if "user_id" not in session:
                    return redirect(url_for("login"))
                if role and session.get("role") != role:
                    return "Forbidden: you do not have permission to access this page.", 403
                return f(*args, **kwargs)
            return wrapped
        return decorator
    

    # --------------------- AUTH ROUTES ---------------------

    @app.route("/")
    def home():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            user = User.query.filter_by(username=username, password=password).first()
            if user:
                session["user_id"] = user.id
                session["username"] = user.username
                session["role"] = user.role
                flash("Login successful!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password", "danger")

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Logged out successfully.", "info")
        return redirect(url_for("login"))
    
    @app.route("/change-credentials", methods=["GET", "POST"])
    @login_required(role="admin")
    def change_credentials():
        user = User.query.get(session["user_id"])

        if request.method == "POST":
            new_username = request.form.get("username")
            new_password = request.form.get("password")

            if not new_username or not new_password:
                flash("Username and password cannot be empty.", "danger")
                return redirect(url_for("change_credentials"))

            # Check if username already exists (except current user)
            existing_user = User.query.filter(
                User.username == new_username,
                User.id != user.id
            ).first()

            if existing_user:
                flash("Username already taken.", "danger")
                return redirect(url_for("change_credentials"))

            user.username = new_username
            user.password = new_password
            db.session.commit()

            # Update session username
            session["username"] = new_username

            flash("Username and password updated successfully.", "success")
            return redirect(url_for("dashboard"))

        return render_template("change_credentials.html")


    # --------------------- DASHBOARD ---------------------

    @app.route("/dashboard")
    @login_required()
    def dashboard():
        total_tables = DiningTable.query.count()
        available_tables = DiningTable.query.filter_by(status="available").count()
        occupied_tables = DiningTable.query.filter_by(status="occupied").count()
        total_menu_items = MenuItem.query.count()
        open_orders = Order.query.filter_by(status="open").count()

        return render_template(
            "dashboard.html",
            total_tables=total_tables,
            available_tables=available_tables,
            occupied_tables=occupied_tables,
            total_menu_items=total_menu_items,
            open_orders=open_orders,
        )

    # --------------------- TABLE MANAGEMENT ---------------------

    @app.route("/tables")
    @login_required()
    def tables_list():
        tables = DiningTable.query.order_by(DiningTable.table_number).all()
        return render_template("tables.html", tables=tables)

    @app.route("/tables/add", methods=["GET", "POST"])
    @login_required(role="admin")
    def add_table():
        if request.method == "POST":
            table_number = request.form.get("table_number")
            capacity = int(request.form.get("capacity"))

            table = DiningTable(
                table_number=table_number,
                capacity=capacity,
                status="available",
            )
            db.session.add(table)
            db.session.commit()
            flash("Table added successfully.", "success")
            return redirect(url_for("tables_list"))

        return render_template("add_table.html")

    @app.route("/tables/<int:table_id>/edit", methods=["GET", "POST"])
    @login_required(role="admin")
    def edit_table(table_id):
        table = DiningTable.query.get_or_404(table_id)

        if request.method == "POST":
            table.table_number = request.form.get("table_number")
            table.capacity = int(request.form.get("capacity"))
            table.status = request.form.get("status")
            db.session.commit()
            flash("Table updated successfully.", "success")
            return redirect(url_for("tables_list"))

        return render_template("edit_table.html", table=table)

    @app.route("/tables/<int:table_id>/delete", methods=["POST"])
    @login_required(role="admin")
    def delete_table(table_id):
        table = DiningTable.query.get_or_404(table_id)

        if table.orders:
            flash("Cannot delete table with existing orders.", "danger")
            return redirect(url_for("tables_list"))

        db.session.delete(table)
        db.session.commit()
        flash("Table deleted successfully.", "success")
        return redirect(url_for("tables_list"))

    # --------------------- MENU MANAGEMENT ---------------------

    @app.route("/menu")
    @login_required()
    def menu_list():
        items = MenuItem.query.order_by(MenuItem.category, MenuItem.name).all()
        return render_template("menu.html", items=items)

    @app.route("/menu/add", methods=["GET", "POST"])
    @login_required(role="admin")
    def add_menu_item():
        if request.method == "POST":
            name = request.form.get("name")
            category = request.form.get("category")
            price = float(request.form.get("price"))
            is_available = request.form.get("is_available") == "on"

            item = MenuItem(
                name=name,
                category=category,
                price=price,
                is_available=is_available,
            )
            db.session.add(item)
            db.session.commit()
            flash("Menu item added successfully.", "success")
            return redirect(url_for("menu_list"))

        return render_template("add_menu_item.html")

    @app.route("/menu/<int:item_id>/edit", methods=["GET", "POST"])
    @login_required(role="admin")
    def edit_menu_item(item_id):
        item = MenuItem.query.get_or_404(item_id)

        if request.method == "POST":
            item.name = request.form.get("name")
            item.category = request.form.get("category")
            item.price = float(request.form.get("price"))
            item.is_available = request.form.get("is_available") == "on"
            db.session.commit()
            flash("Menu item updated successfully.", "success")
            return redirect(url_for("menu_list"))

        return render_template("edit_menu_item.html", item=item)

    @app.route("/menu/<int:item_id>/delete", methods=["POST"])
    @login_required(role="admin")
    def delete_menu_item(item_id):
        item = MenuItem.query.get_or_404(item_id)

        if item.order_items:
            flash("Cannot delete menu item that has been ordered.", "danger")
            return redirect(url_for("menu_list"))

        db.session.delete(item)
        db.session.commit()
        flash("Menu item deleted successfully.", "success")
        return redirect(url_for("menu_list"))

    # --------------------- CUSTOMER MANAGEMENT ---------------------

    @app.route("/customers")
    @login_required()
    def customers_list():
        customers = Customer.query.order_by(Customer.name).all()
        return render_template("customers.html", customers=customers)

    @app.route("/customers/add", methods=["GET", "POST"])
    @login_required()
    def add_customer():
        if request.method == "POST":
            name = request.form.get("name")
            phone = request.form.get("phone")
            email = request.form.get("email")

            customer = Customer(name=name, phone=phone, email=email)
            db.session.add(customer)
            db.session.commit()
            flash("Customer added successfully.", "success")
            return redirect(url_for("customers_list"))

        return render_template("add_customer.html")

    # --------------------- ORDER MANAGEMENT ---------------------

    @app.route("/orders")
    @login_required()
    def orders_list():
        orders = Order.query.order_by(Order.created_at.desc()).all()
        return render_template("orders.html", orders=orders)

    @app.route("/orders/add", methods=["GET", "POST"])
    @login_required()
    def add_order():
        tables = DiningTable.query.order_by(DiningTable.table_number).all()
        customers = Customer.query.order_by(Customer.name).all()
        menu_items = MenuItem.query.filter_by(is_available=True).order_by(MenuItem.category, MenuItem.name).all()

        if request.method == "POST":
            table_id = int(request.form.get("table_id"))
            customer_id = request.form.get("customer_id")
            customer_id = int(customer_id) if customer_id else None

            table = DiningTable.query.get(table_id)
            if table.status == "occupied":
                flash("Selected table is already occupied.", "danger")
                return redirect(url_for("add_order"))

            # Create order
            order = Order(
                table_id=table_id,
                customer_id=customer_id,
                status="open",
            )
            db.session.add(order)
            db.session.flush()  # get order.id before commit

            # Retrieve lists of item IDs and quantities from form
            item_ids = request.form.getlist("item_id[]")
            quantities = request.form.getlist("quantity[]")

            if not item_ids:
                flash("No items selected for the order.", "danger")
                db.session.rollback()
                return redirect(url_for("add_order"))

            for item_id, qty in zip(item_ids, quantities):
                if not item_id or not qty:
                    continue
                qty = int(qty)
                if qty <= 0:
                    continue
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=int(item_id),
                    quantity=qty,
                )
                db.session.add(order_item)

            # Mark table as occupied
            table.status = "occupied"

            db.session.commit()
            flash(f"Order #{order.id} created successfully.", "success")
            return redirect(url_for("orders_list"))

        return render_template(
            "add_order.html",
            tables=tables,
            customers=customers,
            menu_items=menu_items,
        )

    @app.route("/orders/<int:order_id>")
    @login_required()
    def view_order(order_id):
        order = Order.query.get_or_404(order_id)

        # Calculate total amount (for display)
        total = 0
        for oi in order.order_items:
            total += oi.menu_item.price * oi.quantity

        return render_template("view_order.html", order=order, total=total)

    # --------------------- CHECKOUT / BILLING ---------------------

    @app.route("/orders/<int:order_id>/checkout", methods=["GET", "POST"])
    @login_required()
    def checkout(order_id):
        order = Order.query.get_or_404(order_id)

        if order.status != "open":
            flash("Order is already paid or cancelled.", "info")
            return redirect(url_for("orders_list"))

        # Calculate total amount
        total_amount = 0
        for oi in order.order_items:
            total_amount += oi.menu_item.price * oi.quantity

        if request.method == "POST":
            mode = request.form.get("mode")
            status = request.form.get("status")

            payment = Payment(
                order_id=order.id,
                amount=total_amount,
                mode=mode,
                status=status,
            )

            order.status = "paid"
            # free up the table
            order.table.status = "available"

            db.session.add(payment)
            db.session.commit()
            flash("Payment recorded. Order closed.", "success")
            return redirect(url_for("orders_list"))

        return render_template(
            "checkout.html",
            order=order,
            total_amount=total_amount,
        )

    return app


def create_default_admin():
    """Create a default admin user if no users exist."""
    if User.query.count() == 0:
        admin = User(username="Admin123", password="21112005", role="admin")
        db.session.add(admin)
        db.session.commit()

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
