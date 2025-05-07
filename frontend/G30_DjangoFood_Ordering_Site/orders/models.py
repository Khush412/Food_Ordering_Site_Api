from django.db import models  # type: ignore
from django.contrib.auth.models import User #type:ignore
from decimal import Decimal #type:ignore
from django.conf import settings #type:ignore

# Cart model now only stores product_id and product_name as primitives
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    image_url = models.URLField()

    def __str__(self):
        return self.name

class Order(models.Model):
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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    full_name = models.CharField(max_length=255, default='Unknown')
    email = models.EmailField(max_length=255, default='default@example.com')
    address = models.CharField(max_length=255, default='Default Address')
    phone = models.CharField(max_length=15, default='null')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='cash_on_delivery')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

    def get_total_price(self):
        return float(self.total_price + self.delivery_fee)

    def get_subtotal(self):
        return float(self.total_price - self.delivery_fee)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user.id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'full_name': self.full_name,
            'email': self.email,
            'address': self.address,
            'phone': self.phone,
            'payment_method': self.payment_method,
            'total_price': float(self.total_price),
            'delivery_fee': float(self.delivery_fee),
            'items': [item.to_dict() for item in self.items.all()] if hasattr(self, 'items') else []
        }

# OrderItem model now only stores product_id and product_name as primitives
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} in Order #{self.order.id}"

    def get_total(self):
        return self.quantity * self.price

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'price': float(self.price),
            'total': float(self.get_total())
        }

    class Meta:
        db_table = 'orders_orderitem'

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"