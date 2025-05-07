from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_required, login_user, logout_user
from functools import wraps
from models import db, MenuItem, Cart, Order, OrderItem, User, bcrypt
from datetime import datetime
from decimal import Decimal

api = Blueprint('api', __name__)

def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Error handlers
@api.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@api.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

@api.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': str(error)}), 404

@api.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500

# Authentication endpoints
@api.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['email', 'username', 'password1', 'password2']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if passwords match
        if data['password1'] != data['password2']:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=data['email']).first()
        if existing_email:
            return jsonify({'error': 'Email already registered'}), 400
            
        # Check if username already exists
        existing_username = User.query.filter_by(username=data['username']).first()
        if existing_username:
            return jsonify({'error': 'Username already taken'}), 400
        
        # Create new user
        hashed_password = bcrypt.generate_password_hash(data['password1']).decode('utf-8')
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=hashed_password,
            is_admin=False,
            is_active=True,
            is_staff=False
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'Account created successfully',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user and bcrypt.check_password_hash(user.password, data['password']):
            if not user.is_active:
                return jsonify({'error': 'Account is inactive'}), 403
            
            login_user(user)
            user.last_login = db.func.current_timestamp()
            db.session.commit()
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_admin': user.is_admin
                }
            })
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/auth/logout', methods=['POST'])
@api_login_required
def logout():
    try:
        logout_user()
        return jsonify({'message': 'Logged out successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Menu endpoints
@api.route('/menu', methods=['GET'])
def get_menu():
    try:
        category = request.args.get('category')
        query = MenuItem.query
        
        if category:
            query = query.filter_by(category=category)
            
        menu_items = query.all()
        return jsonify({
            'menu_items': [{
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'price': float(item.price),
                'is_veg': item.is_veg,
                'category': item.category,
                'image_url': item.image_url
            } for item in menu_items]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/menu/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    try:
        item = MenuItem.query.get_or_404(item_id)
        return jsonify({
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': float(item.price),
            'is_veg': item.is_veg,
            'category': item.category,
            'image_url': item.image_url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Cart endpoints
@api.route('/cart', methods=['GET'])
@api_login_required
def get_cart():
    try:
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        subtotal = sum(Decimal(str(item.price)) * Decimal(str(item.quantity)) for item in cart_items)
        delivery_fee = Decimal('50.00')
        total = subtotal + delivery_fee
        
        return jsonify({
            'items': [{
                'id': item.id,
                'product_id': item.product_id,
                'quantity': item.quantity,
                'price': float(item.price),
                'menu_item': {
                    'id': item.menu_item.id,
                    'name': item.menu_item.name,
                    'description': item.menu_item.description,
                    'price': float(item.menu_item.price),
                    'image_url': item.menu_item.image_url
                }
            } for item in cart_items],
            'subtotal': float(subtotal),
            'delivery_fee': float(delivery_fee),
            'total': float(total)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/cart', methods=['POST'])
@api_login_required
def add_to_cart():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        
        if not item_id:
            return jsonify({'error': 'Item ID is required'}), 400
        
        menu_item = MenuItem.query.get_or_404(item_id)
        
        cart_item = Cart.query.filter_by(
            user_id=current_user.id,
            product_id=item_id
        ).first()
        
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = Cart(
                user_id=current_user.id,
                product_id=item_id,
                quantity=quantity,
                price=menu_item.price
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        return jsonify({
            'message': f"{menu_item.name} added to cart",
            'cart_item': {
                'id': cart_item.id,
                'product_id': cart_item.product_id,
                'quantity': cart_item.quantity,
                'price': float(cart_item.price)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/cart/<int:item_id>', methods=['PUT'])
@api_login_required
def update_cart_item(item_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        quantity = int(data.get('quantity', 1))
        
        cart_item = Cart.query.filter_by(
            user_id=current_user.id,
            product_id=item_id
        ).first_or_404()
        
        cart_item.quantity = quantity
        db.session.commit()
        
        return jsonify({
            'message': 'Cart updated successfully',
            'cart_item': {
                'id': cart_item.id,
                'product_id': cart_item.product_id,
                'quantity': cart_item.quantity,
                'price': float(cart_item.price)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/cart/<int:item_id>', methods=['DELETE'])
@api_login_required
def remove_from_cart(item_id):
    try:
        cart_item = Cart.query.filter_by(
            user_id=current_user.id,
            product_id=item_id
        ).first_or_404()
        
        db.session.delete(cart_item)
        db.session.commit()
        
        return jsonify({'message': 'Item removed from cart'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Order endpoints
@api.route('/orders', methods=['GET'])
@api_login_required
def get_orders():
    try:
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        return jsonify({
            'orders': [{
                'id': order.id,
                'status': order.status,
                'total_price': float(order.total_price),
                'delivery_fee': float(order.delivery_fee),
                'created_at': order.created_at.isoformat(),
                'items': [{
                    'id': item.id,
                    'product_id': item.product_id,
                    'quantity': item.quantity,
                    'price': float(item.price)
                } for item in order.items]
            } for order in orders]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/orders/<int:order_id>', methods=['GET'])
@api_login_required
def get_order(order_id):
    try:
        # Get order and verify ownership
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Get order items with menu item details
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        items_data = []
        for item in order_items:
            menu_item = MenuItem.query.get(item.product_id)
            if menu_item:
                items_data.append({
                    'id': item.id,
                    'product_id': item.product_id,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'menu_item': {
                        'id': menu_item.id,
                        'name': menu_item.name,
                        'description': menu_item.description,
                        'price': float(menu_item.price),
                        'image_url': menu_item.image_url
                    }
                })

        return jsonify({
            'id': order.id,
            'status': order.status,
            'total_price': float(order.total_price),
            'delivery_fee': float(order.delivery_fee),
            'created_at': order.created_at.isoformat(),
            'full_name': order.full_name,
            'email': order.email,
            'phone': order.phone,
            'address': order.address,
            'payment_method': order.payment_method,
            'items': items_data
        })
    except Exception as e:
        print(f"Error getting order: {str(e)}")  # Add debug print
        return jsonify({'error': str(e)}), 500

@api.route('/orders', methods=['POST'])
@api_login_required
def create_order():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Validate required fields
        required_fields = ['full_name', 'email', 'phone', 'address', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Get cart items
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Calculate totals
        subtotal = sum(Decimal(str(item.price)) * Decimal(str(item.quantity)) for item in cart_items)
        delivery_fee = Decimal('50.00')
        total_price = subtotal + delivery_fee
        
        # Create order
        order = Order(
            user_id=current_user.id,
            full_name=data['full_name'],
            email=data['email'],
            phone=data['phone'],
            address=data['address'],
            payment_method=data['payment_method'],
            total_price=total_price,
            delivery_fee=delivery_fee
        )
        db.session.add(order)
        
        # Create order items
        for item in cart_items:
            order_item = OrderItem(
                order=order,
                product_id=item.product_id,
                quantity=item.quantity,
                price=Decimal(str(item.price))
            )
            db.session.add(order_item)
        
        # Clear cart
        for item in cart_items:
            db.session.delete(item)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Order created successfully',
            'order': {
                'id': order.id,
                'status': order.status,
                'total_price': float(order.total_price),
                'delivery_fee': float(order.delivery_fee),
                'created_at': order.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/orders/<int:order_id>/cancel', methods=['POST'])
@api_login_required
def cancel_order(order_id):
    try:
        # Get order and verify ownership
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Check if order can be cancelled
        if order.status != 'pending':
            return jsonify({'error': 'Only pending orders can be cancelled'}), 400

        # Update order status
        order.status = 'cancelled'
        db.session.commit()

        return jsonify({
            'message': 'Order cancelled successfully',
            'order': {
                'id': order.id,
                'status': order.status,
                'total_price': float(order.total_price),
                'delivery_fee': float(order.delivery_fee)
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error cancelling order: {str(e)}")  # Add debug print
        return jsonify({'error': str(e)}), 500 