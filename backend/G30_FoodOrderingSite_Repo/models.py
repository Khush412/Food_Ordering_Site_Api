from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime
from decimal import Decimal

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    date_joined = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_staff = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.DECIMAL(10, 2), nullable=False)
    
    menu_item = db.relationship('MenuItem', backref='cart_items', lazy='joined')
    user = db.relationship('User', backref='cart_items', lazy='joined')

    def __repr__(self):
        return f'<Cart {self.quantity}x {self.menu_item.name if self.menu_item else "Unknown"}>'

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': float(self.price),
            'menu_item': {
                'id': self.menu_item.id,
                'name': self.menu_item.name,
                'price': float(self.menu_item.price),
                'image_url': self.menu_item.image_url
            } if self.menu_item else None
        }

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.DECIMAL(10, 2), nullable=False)
    is_veg = db.Column(db.Boolean, default=True)
    category = db.Column(db.String(50), default='meals')
    image_url = db.Column(db.String(200))

    CATEGORY_CHOICES = [
        ('beverages', 'Beverages'),
        ('snacks', 'Snacks'),
        ('meals', 'Meals'),
        ('desserts', 'Desserts'),
    ]

    def __repr__(self):
        return f'<MenuItem {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'is_veg': self.is_veg,
            'category': self.category,
            'image_url': self.image_url
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(50), default='pending')
    full_name = db.Column(db.String(255), default='Unknown')
    email = db.Column(db.String(255), default='default@example.com')
    address = db.Column(db.String(255), default='Default Address')
    phone = db.Column(db.String(15), default='null')
    payment_method = db.Column(db.String(50), default='cash_on_delivery')
    total_price = db.Column(db.DECIMAL(10, 2), nullable=False)
    delivery_fee = db.Column(db.DECIMAL(10, 2), default=50.00)
    items = db.relationship('OrderItem', backref='order', lazy=True)
    user = db.relationship('User', backref='orders', lazy=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash_on_delivery', 'Cash on Delivery'),
        ('online_payment', 'Online Payment'),
        ('card_payment', 'Card Payment')
    ]

    def __repr__(self):
        return f"Order #{self.id} - {self.user.username if self.user else 'Unknown'}"

    def get_total_price(self):
        return float(self.total_price + self.delivery_fee)

    def get_subtotal(self):
        return float(self.total_price - self.delivery_fee)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'full_name': self.full_name,
            'email': self.email,
            'address': self.address,
            'phone': self.phone,
            'payment_method': self.payment_method,
            'total_price': float(self.total_price),
            'delivery_fee': float(self.delivery_fee),
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.DECIMAL(10, 2), nullable=False)
    product = db.relationship('MenuItem', backref='order_items')

    def get_total(self):
        return float(self.price * self.quantity)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': float(self.price),
            'total': self.get_total(),
            'product': self.product.to_dict() if self.product else None
        } 