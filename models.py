# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # plain text for demo
    role = db.Column(db.String(20), nullable=False)        # 'admin', 'waiter', 'cashier'

    def __repr__(self):
        return f"<User {self.username}>"

class DiningTable(db.Model):
    __tablename__ = "tables"

    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.String(10), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="available")
    # available / occupied / reserved

    orders = db.relationship("Order", backref="table", lazy=True)

    def __repr__(self):
        return f"<Table {self.table_number} ({self.status})>"

class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)   # Starter, Main, Dessert, Drink
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)

    order_items = db.relationship("OrderItem", backref="menu_item", lazy=True)

    def __repr__(self):
        return f"<MenuItem {self.name} - {self.price}>"

class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))

    orders = db.relationship("Order", backref="customer", lazy=True)

    def __repr__(self):
        return f"<Customer {self.name}>"

class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey("tables.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default="open")
    # open / paid / cancelled

    order_items = db.relationship("OrderItem", backref="order", lazy=True)
    payment = db.relationship("Payment", backref="order", uselist=False)

    def __repr__(self):
        return f"<Order {self.id} - Table {self.table_id} - {self.status}>"

class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    def __repr__(self):
        return f"<OrderItem order={self.order_id}, item={self.menu_item_id}, qty={self.quantity}>"

class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    mode = db.Column(db.String(20))      # cash / card / upi
    status = db.Column(db.String(20))    # paid / pending

    def __repr__(self):
        return f"<Payment {self.id} - Order {self.order_id}>"
