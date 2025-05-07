from app import app, db
from models import MenuItem, User
from datetime import datetime

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we already have menu items
        if MenuItem.query.first() is None:
            # Add sample menu items
            menu_items = [
                MenuItem(
                    name='Chicken Biryani',
                    description='Fragrant basmati rice cooked with tender chicken and aromatic spices',
                    price=250.00,
                    category='meals',
                    image_url='biryani.jpg',
                    is_available=True
                ),
                MenuItem(
                    name='Butter Chicken',
                    description='Tender chicken in a rich, creamy tomato-based curry',
                    price=280.00,
                    category='meals',
                    image_url='butter_chicken.jpg',
                    is_available=True
                ),
                MenuItem(
                    name='Veg Fried Rice',
                    description='Stir-fried rice with mixed vegetables',
                    price=180.00,
                    category='meals',
                    image_url='veg_fried_rice.jpg',
                    is_available=True
                ),
                MenuItem(
                    name='Chicken Wings',
                    description='Crispy fried chicken wings with special sauce',
                    price=200.00,
                    category='snacks',
                    image_url='chicken_wings.jpg',
                    is_available=True
                ),
                MenuItem(
                    name='French Fries',
                    description='Crispy golden fries with seasoning',
                    price=120.00,
                    category='snacks',
                    image_url='french_fries.jpg',
                    is_available=True
                ),
                MenuItem(
                    name='Coca Cola',
                    description='Refreshing carbonated drink',
                    price=60.00,
                    category='beverages',
                    image_url='coca_cola.jpg',
                    is_available=True
                ),
                MenuItem(
                    name='Ice Cream',
                    description='Creamy vanilla ice cream',
                    price=80.00,
                    category='desserts',
                    image_url='ice_cream.jpg',
                    is_available=True
                )
            ]
            
            # Add items to database
            for item in menu_items:
                db.session.add(item)
            
            # Create admin user if not exists
            if not User.query.filter_by(email='admin@example.com').first():
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',  # This will be hashed by the User model
                    is_admin=True,
                    is_active=True,
                    is_staff=True
                )
                db.session.add(admin)
            
            # Commit changes
            db.session.commit()
            print("Database initialized with sample data!")

if __name__ == '__main__':
    init_db() 