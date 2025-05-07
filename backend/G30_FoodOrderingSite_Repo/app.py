from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import text
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from decimal import Decimal
import os
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_session import Session
from datetime import timedelta
from functools import wraps
from models import db, User, MenuItem, Cart, Order, OrderItem, bcrypt
from api import api

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_ordering.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize session
Session(app)

app.secret_key = 'your_secret_key_here'

db.init_app(app)
bcrypt.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Register API blueprint
app.register_blueprint(api, url_prefix='/api/v1')

# Exempt API routes from CSRF protection
csrf.exempt(api)

# Custom decorator for API authentication
def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Form Classes
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
    password1 = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password1')])
    submit = SubmitField('Sign Up')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html', user=current_user if current_user.is_authenticated else None)

@app.route('/about-us')
def about_us():
    return render_template('about_us.html')

@app.route('/terms_and_conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')

@app.route('/menu')
def menu():
    menu_items = MenuItem.query.all()
    categories = MenuItem.CATEGORY_CHOICES
    return render_template('menu.html', menu_items=menu_items, categories=categories)

@app.route('/register', methods=['GET', 'POST'])
def register():
    print("\n=== Registration Debug ===")
    form = RegisterForm()
    
    if form.validate_on_submit():
        try:
            username = form.username.data
            email = form.email.data
            password1 = form.password1.data
            
            print(f"Registration attempt for email: {email}")
        
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                print(f"User with email {email} already exists")
                flash('Email already registered! Please try logging in.', 'danger')
                return redirect(url_for('login'))
            
            # Create new user
            hashed_password = bcrypt.generate_password_hash(password1).decode('utf-8')
            new_user = User(
                username=username,
                email=email,
                password=hashed_password,
                is_admin=False,
                is_active=True,
                is_staff=False
            )
            
            db.session.add(new_user)
            db.session.commit()
        
            print(f"New user created: {username} ({email})")
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')
    
    print("=== End Registration Debug ===\n")
    return render_template('register.html', form=form)

@app.route('/offers')
def offers():
    return render_template('offers.html')


@app.route('/more-food')
def more_food():
    return render_template('more_food.html', user=current_user if current_user.is_authenticated else None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    print("\n=== Login Debug ===")
    form = LoginForm()
    
    if form.validate_on_submit():
        try:
            email = form.email.data
            password = form.password.data
            print(f"Login attempt for email: {email}")
        
            user = User.query.filter_by(email=email).first()
            print(f"User found: {user is not None}")
        
            if user and bcrypt.check_password_hash(user.password, password):
                print("Password check successful")
                
                if not user.is_active:
                    print("User account is inactive")
                    flash('Your account is inactive. Please contact support.', 'danger')
                    return redirect(url_for('login'))

                login_user(user)
                user.last_login = db.func.current_timestamp()
                db.session.commit()
            
                print(f"User {user.username} logged in successfully")
                flash('Login successful!', 'success')
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                if user.is_admin:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('home'))
            else:
                print("Invalid email or password")
                flash('Invalid email or password', 'danger')
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'danger')
            
    print("=== End Login Debug ===\n")
    return render_template('login.html', form=form)

@app.route('/admin-dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    return render_template('admin_dashboard.html')

@app.route('/admin/manage-menu', methods=['GET', 'POST'])
@login_required
def manage_menu():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        is_veg = request.form.get('is_veg') == 'true'
        category = request.form.get('category')
        image_url = request.form.get('image_url')
        
        new_item = MenuItem(
            name=name,
            description=description,
            price=float(price),
            is_veg=is_veg,
            category=category,
            image_url=image_url
        )
        db.session.add(new_item)
        db.session.commit()
        flash("Menu item added successfully!", "success")
    menu_items = MenuItem.query.all()
    return render_template('admin_manage_menu.html', 
                         menu_items=menu_items,
                         categories=MenuItem.CATEGORY_CHOICES)

@app.route('/admin/manage-users')
@login_required
def manage_users():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    users = User.query.all()
    return render_template('admin_manage_users.html', users=users)

@app.route('/admin/manage-offers')
@login_required
def manage_offers():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    return render_template('admin_manage_offers.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

@app.route('/cart')
@login_required
def cart():
    try:
        # Get cart items for the current user
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        
        # Calculate totals
        subtotal = sum(Decimal(str(item.price)) * Decimal(str(item.quantity)) for item in cart_items)
        delivery_fee = Decimal('50.00')
        total = subtotal + delivery_fee
        
        # Get total number of items
        total_items = sum(item.quantity for item in cart_items)
        
        # Convert all monetary values to float for template
        context = {
            'cart_items': cart_items,
            'subtotal': float(subtotal),
            'delivery_fee': float(delivery_fee),
            'total': float(total),
            'total_items': total_items
        }
        
        return render_template('cart.html', **context)
    except Exception as e:
        print(f"Cart error: {str(e)}")  # Add debug print
        flash(f'Error loading cart: {str(e)}', 'error')
        return redirect(url_for('home'))

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        
        if not item_id:
            return jsonify({'error': 'Item ID is required'}), 400
        
        menu_item = MenuItem.query.get(item_id)
        if not menu_item:
            return jsonify({'error': 'Item not found'}), 404
        
        # Check if item already in cart
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
        
        # Calculate updated cart totals
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total_price = sum(float(item.price) * item.quantity for item in cart_items)
        total_items = sum(item.quantity for item in cart_items)
        
        return jsonify({
            'success': True,
            'message': f"{menu_item.name} added to cart",
            'cart_total': total_price,
            'cart_items': total_items
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error adding to cart: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/update_cart_quantity', methods=['POST'])
@login_required
def update_cart_quantity():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        
        if not item_id:
            return jsonify({'error': 'Item ID is required'}), 400
        
        cart_item = Cart.query.filter_by(
            user_id=current_user.id,
            product_id=item_id
        ).first()
        
        if not cart_item:
            return jsonify({'error': 'Item not found in cart'}), 404
        
        cart_item.quantity = quantity
        db.session.commit()
        
        # Calculate updated cart totals
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total_price = sum(float(item.price) * item.quantity for item in cart_items)
        total_items = sum(item.quantity for item in cart_items)
        
        return jsonify({
            'success': True,
            'total_items': total_items,
            'cart_total': total_price
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_cart_quantity: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        item_id = data.get('item_id')
        
        if not item_id:
            return jsonify({'error': 'Item ID is required'}), 400
        
        cart_item = Cart.query.filter_by(
            user_id=current_user.id,
            product_id=item_id
        ).first()
        
        if not cart_item:
            return jsonify({'error': 'Item not found in cart'}), 404
        
        db.session.delete(cart_item)
        db.session.commit()
        
        # Calculate updated cart totals
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total_price = sum(float(item.price) * item.quantity for item in cart_items)
        total_items = sum(item.quantity for item in cart_items)
        
        return jsonify({
            'success': True,
            'total_items': total_items,
            'cart_total': total_price
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in remove_from_cart: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/checkout')
@login_required
def checkout():
    try:
        # Get cart items for the current user
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        
        if not cart_items:
            flash('Your cart is empty', 'warning')
            return redirect(url_for('cart'))
        
        # Calculate totals - convert all to Decimal
        subtotal = sum(Decimal(str(item.price)) * Decimal(str(item.quantity)) for item in cart_items)
        delivery_fee = Decimal('50.00')
        total_price = subtotal + delivery_fee
        
        return render_template('checkout.html',
                             cart_items=cart_items,
                             subtotal=float(subtotal),
                             delivery_fee=float(delivery_fee),
                             total_price=float(total_price),
                             payment_methods=Order.PAYMENT_METHOD_CHOICES)
                             
    except Exception as e:
        flash(f'Error loading checkout: {str(e)}', 'error')
        return redirect(url_for('cart'))

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    try:
        # Get cart items for the current user
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        
        if not cart_items:
            flash('Your cart is empty', 'warning')
            return redirect(url_for('cart'))
        
        # Calculate totals - convert all to Decimal
        subtotal = sum(Decimal(str(item.price)) * Decimal(str(item.quantity)) for item in cart_items)
        delivery_fee = Decimal('50.00')
        total_price = subtotal + delivery_fee
        
        # Create order
        order = Order(
            user_id=current_user.id,
            full_name=request.form.get('full_name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            payment_method=request.form.get('payment_method'),
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
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_history'))
        
    except Exception as e:
        db.session.rollback()
        print('Order placement error:', e)
        flash(f'Error placing order: {str(e)}', 'error')
        return redirect(url_for('checkout'))

# Route to delete a user
@app.route('/admin/delete-user/<int:user_id>')
def delete_user(user_id):
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for('home'))
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('manage_users'))

@app.route('/admin/delete-menu-item/<int:item_id>')
def delete_menu_item(item_id):
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for('home'))
    item = MenuItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('manage_menu'))

@app.route('/admin/add-offer', methods=['POST'])
def add_offer():
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for('home'))
    
    title = request.form.get('title')
    discount = request.form.get('discount')

    new_offer = offers(title=title, discount=discount)
    db.session.add(new_offer)
    db.session.commit()

    return redirect(url_for('manage_offers'))

@app.route('/admin/delete-offer/<int:offer_id>')
def delete_offer(offer_id):
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for('home'))
    offer = offers.query.get(offer_id)
    if offer:
        db.session.delete(offer)
        db.session.commit()
    return redirect(url_for('manage_offers'))

@app.route('/order-history')
@login_required
def order_history():
    try:
        # Get all orders for the current user, ordered by creation date (newest first)
        orders = Order.query.filter_by(user_id=current_user.id)\
                           .order_by(Order.created_at.desc())\
                           .all()
        
        # Get order items for each order with their product details
        order_details = {}
        for order in orders:
            # Get all order items for this order
            order_items = OrderItem.query.filter_by(order_id=order.id).all()
            
            # Get product details for each order item
            items_with_details = []
            for item in order_items:
                # Get the product details from MenuItem
                product = MenuItem.query.get(item.product_id)
                if product:
                    items_with_details.append({
                        'id': item.id,
                        'product': {
                            'id': product.id,
                            'name': product.name,
                            'price': float(product.price),
                            'image_url': product.image_url
                        },
                        'quantity': item.quantity,
                        'price': float(item.price)
                    })
            
            order_details[order.id] = items_with_details
        
        status_labels = dict(Order.STATUS_CHOICES)
        payment_method_labels = dict(Order.PAYMENT_METHOD_CHOICES)
        return render_template('order_history.html',
                             orders=orders,
                             order_details=order_details,
                             status_labels=status_labels,
                             payment_method_labels=payment_method_labels)
        
    except Exception as e:
        print('Error in order history:', e)
        flash('Error loading order history. Please try again.', 'error')
        return redirect(url_for('home'))

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash("You do not have permission to view this order.", "danger")
        return redirect(url_for('order_history'))
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    status_labels = dict(Order.STATUS_CHOICES)
    payment_method_labels = dict(Order.PAYMENT_METHOD_CHOICES)
    return render_template('order_detail.html', order=order, order_items=order_items, status_labels=status_labels, payment_method_labels=payment_method_labels)

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        # Check if the order belongs to the current user
        if order.user_id != current_user.id:
            return jsonify({'error': 'You do not have permission to cancel this order'}), 403
        
        # Check if the order is in a cancellable state
        if order.status != 'pending':
            return jsonify({'error': 'Only pending orders can be cancelled'}), 400
        
        # Update order status to cancelled
        order.status = 'cancelled'
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Order cancelled successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error cancelling order: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Drop all tables and recreate them
# def recreate_database():
#     with app.app_context():
#         db.drop_all()
#         db.create_all()
#         print("✅ Database recreated successfully!")

# Call this function to recreate the database
# recreate_database()  # Comment out or remove this line

def add_is_admin_column():
    with app.app_context():
        from sqlalchemy.exc import OperationalError
        try:
            db.session.execute(text('SELECT is_admin FROM "user" LIMIT 1'))
        except OperationalError:
            db.session.execute(text('ALTER TABLE "user" ADD COLUMN is_admin BOOLEAN DEFAULT 0'))
            db.session.commit()
            print("✅ Column 'is_admin' added successfully!")

add_is_admin_column()

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables if they don't exist
        db.create_all()
        
        # Check if admin user exists, if not create one
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                username='admin',
                email='admin@example.com',
                password=hashed_password,
                is_admin=True,
                is_active=True,
                is_staff=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully!")
                                            
        # Check if any users exist, if not create a test user
        if User.query.count() == 1:  # Only admin exists
            hashed_password = bcrypt.generate_password_hash('test123').decode('utf-8')
            test_user = User(
                username='testuser',
                email='test@example.com',
                password=hashed_password,
                is_admin=False,
                is_active=True,
                is_staff=False
            )
            db.session.add(test_user)
            db.session.commit()
            print("✅ Test user created successfully!")
            
    app.run(debug=True)
