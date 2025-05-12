from django.shortcuts import render, redirect, get_object_or_404 #type:ignore
from django.db.models import Q #type:ignore
from django.contrib import messages #type:ignore
from .models import Restaurant, Cart, Order, OrderItem #type:ignore
from django.http import JsonResponse #type:ignore
from collections import defaultdict #type:ignore
from django.contrib.auth.forms import UserCreationForm #type:ignore
from django.contrib.auth.models import User #type:ignore
from django.contrib.auth import login, logout #type:ignore
from django.contrib.auth.views import LoginView #type:ignore
from .forms import CustomUserCreationForm, SignUpForm #type:ignore
from django.contrib.auth import authenticate #type:ignore
from .forms import LoginForm #type:ignore
from django.contrib.auth.decorators import login_required #type:ignore
from decimal import Decimal  #type:ignore
from .forms import ContactMessageForm
from django.views.decorators.http import require_POST, require_http_methods #type:ignore
from .forms import OrderForm
from .api_services import APIService
from .views_admin import admin_dashboard
import json

api_service = APIService()

# View for the homepage
def restaurant_list(request):
    # Fetch all restaurant objects (no description field as requested)
    restaurants = Restaurant.objects.all()
    
    # Pass restaurants to the context in the template
    return render(request, 'orders/homepage.html', {'restaurants': restaurants})

# View for the Ziggy Cafe menu (your menu page)
@login_required
def ziggy_cafe_menu(request):
    query = request.GET.get('q', '')
    is_veg = request.GET.get('is_veg', 'all')  # 'veg', 'non-veg', or 'all'
    remove_id = request.GET.get('remove')

    # Ensure API session is restored
    api_session = request.session.get('api_session', {})
    if api_session:
        api_service.session.cookies.update(api_session)

    # Fetch menu items from Flask API
    response = api_service.get_menu(request)
    if 'error' in response:
        messages.error(request, response['error'])
        return render(request, 'orders/ziggycafemenu.html', {'categorized_menu': {}, 'query': query, 'is_veg': is_veg, 'cart_items': {}, 'total_items': 0, 'total_price': 0})

    menu_items = response.get('menu_items', [])

    # Apply search filter
    if query:
        menu_items = [item for item in menu_items if query.lower() in item['name'].lower() or query.lower() in (item.get('description') or '').lower()]

    # Apply veg/non-veg filter
    if is_veg in ['veg', 'non-veg']:
        menu_items = [item for item in menu_items if (item['is_veg'] if is_veg == 'veg' else not item['is_veg'])]

    # Categorize menu items for display
    categorized_menu = defaultdict(list)
    for item in menu_items:
        categorized_menu[item['category'].capitalize()].append(item)

    # Get current cart items
    cart_response = api_service.get_cart(request)
    cart_items = cart_response.get('items', []) if 'error' not in cart_response else []
    total_items = sum(item.get('quantity', 0) for item in cart_items)
    total_price = cart_response.get('total', 0) if 'error' not in cart_response else 0

    context = {
        'categorized_menu': dict(categorized_menu),
        'query': query,
        'is_veg': is_veg,
        'cart_items': cart_items,
        'total_items': total_items,
        'total_price': total_price,
    }

    return render(request, 'orders/ziggycafemenu.html', context)

@login_required
def cart(request):
    try:
        # Ensure API session is restored
        api_session = request.session.get('api_session', {})
        if api_session:
            api_service.session.cookies.update(api_session)
        
        # Fetch cart from Flask API
        print("Fetching cart from API...")  # Debug log
        response = api_service.get_cart(request)
        print("Cart API Response:", response)  # Debug log
        
        if 'error' in response:
            print("Cart API Error:", response['error'])  # Debug log
            if 'Please log in' in response['error']:
                messages.error(request, 'Your session has expired. Please log in again.')
                return redirect('login')
            messages.error(request, response['error'])
            return redirect('cart')

        cart_items = response.get('items', [])
        subtotal = Decimal(str(response.get('subtotal', 0)))
        delivery_fee = Decimal(str(response.get('delivery_fee', 50.00)))
        total = Decimal(str(response.get('total', subtotal + delivery_fee)))

        # Format cart items for template
        formatted_items = []
        for item in cart_items:
            menu_item = item.get('menu_item', {})
            formatted_item = {
                'id': item.get('id'),  # cart row id
                'product_id': item.get('product_id'),  # product id
                'menu_item': {
                    'name': menu_item.get('name', 'Unknown Item'),
                    'image_url': menu_item.get('image_url', 'https://via.placeholder.com/150'),
                },
                'price': Decimal(str(item.get('price', 0))),
                'quantity': item.get('quantity', 0)
            }
            formatted_items.append(formatted_item)
    
        context = {
            'cart_items': formatted_items,
            'subtotal': subtotal,
            'delivery_fee': delivery_fee,
            'total': total
        }
        return render(request, 'orders/cart.html', context)
        
    except Exception as e:
        print("Cart Error:", str(e))  # Debug print
        messages.error(request, f'Error loading cart: {str(e)}')
        return redirect('homepage')

@login_required
@require_POST
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        
        if not item_id:
            return JsonResponse({'error': 'Item ID is required'}, status=400)
            
        response = api_service.add_to_cart(request, item_id, quantity)
        if 'error' in response:
            return JsonResponse({'error': response['error']}, status=400)
        return JsonResponse({'success': True, 'message': 'Item added to cart'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print("Add to cart error:", str(e))  # Debug print
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def update_cart_quantity(request):
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        
        if not item_id:
            return JsonResponse({'error': 'Item ID is required'}, status=400)
            
        response = api_service.update_cart(request, item_id, quantity)
        if 'error' in response:
            return JsonResponse({'error': response['error']}, status=400)
        
        return JsonResponse({
            'success': True,
            'message': 'Cart updated',
            'cart_total': response.get('total', 0),
            'cart_count': response.get('count', 0)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
def remove_from_cart(request):
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        if not item_id:
            return JsonResponse({'error': 'Item ID is required'}, status=400)
            
        response = api_service.remove_from_cart(request, item_id)
        if 'error' in response:
            return JsonResponse({'error': response['error']}, status=400)
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart_total': response.get('total', 0),
            'cart_count': response.get('count', 0)
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def checkout(request):
    try:
        # Ensure API session is restored
        api_session = request.session.get('api_session', {})
        if api_session:
            api_service.session.cookies.update(api_session)
        
        # Fetch cart from Flask API
        print("Fetching cart from API...")  # Debug log
        response = api_service.get_cart(request)
        print("Cart API Response:", response)  # Debug log
        
        if 'error' in response:
            print("Cart API Error:", response['error'])  # Debug log
            if 'Please log in' in response['error']:
                messages.error(request, 'Your session has expired. Please log in again.')
                return redirect('login')
            messages.error(request, response['error'])
            return redirect('cart')

        cart_items = response.get('items', [])
        subtotal = Decimal(str(response.get('subtotal', 0)))
        delivery_fee = Decimal(str(response.get('delivery_fee', 50.00)))
        total_price = Decimal(str(response.get('total', subtotal + delivery_fee)))
        
        if not cart_items:
            messages.warning(request, 'Your cart is empty')
            return redirect('cart')
        
        if request.method == 'POST':
            try:
                # Get form data
                full_name = request.POST.get('full_name')
                email = request.POST.get('email')
                phone = request.POST.get('phone')
                address = request.POST.get('address')
                payment_method = request.POST.get('payment_method')
                
                # Validate required fields
                if not all([full_name, email, phone, address, payment_method]):
                    messages.error(request, 'All fields are required')
                    return redirect('checkout')
                
                print("Creating order with data:", {  # Debug log
                    'full_name': full_name,
                    'email': email,
                    'phone': phone,
                    'address': address,
                    'payment_method': payment_method
                })
            
                # Create order via Flask API
                order_response = api_service.create_order(
                    request,
                    full_name,
                    email,
                    phone,
                    address,
                    payment_method
                )
                
                print("Order API Response:", order_response)  # Debug log
                
                if 'error' in order_response:
                    print("Order API Error:", order_response['error'])  # Debug log
                    messages.error(request, order_response['error'])
                    return redirect('checkout')
                
                # Update Django session with latest API session
                request.session['api_session'] = api_service.session.cookies.get_dict()
                
                # Show confirmation page using Flask API order response
                messages.success(request, 'Order placed successfully!')
                return render(request, 'orders/order_confirmation.html', {'order': order_response.get('order', {})})
                
            except Exception as e:
                print("Order Creation Error:", str(e))  # Debug log
                messages.error(request, f'Error placing order: {str(e)}')
                return redirect('checkout')
        
        # Update Django session with latest API session
        request.session['api_session'] = api_service.session.cookies.get_dict()
        
        context = {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'delivery_fee': delivery_fee,
            'total_price': total_price,
            'payment_methods': [
                ('cash_on_delivery', 'Cash on Delivery'),
                ('online_payment', 'Online Payment'),
                ('card_payment', 'Credit/Debit Card'),
            ]
        }
        return render(request, 'orders/checkout.html', context)
        
    except Exception as e:
        print("Checkout Error:", str(e))  # Debug log
        messages.error(request, f'Error in checkout process: {str(e)}')
        return redirect('cart')

@login_required
def order_history(request):
    # Restore API session if it exists
    api_session = request.session.get('api_session', {})
    if api_session:
        api_service.session.cookies.update(api_session)

    # Get orders from Flask API
    response = api_service.get_orders(request)
    if 'error' in response:
        messages.error(request, response['error'])
        return render(request, 'orders/order_history.html', {'orders': []})

    orders = response.get('orders', [])
    return render(request, 'orders/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
@require_POST
def cancel_order(request, order_id):
    try:
        # Get the order and verify ownership
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Debug logging
        print(f"Attempting to cancel order #{order.id} for user {request.user.username}")
        print(f"Current status: {order.status}")
        
        # Check if order can be cancelled
        if order.status != 'pending':
            print(f"Cannot cancel order #{order.id}: status is {order.status}")
            return JsonResponse({
                'error': 'Only pending orders can be cancelled'
            }, status=400)
        
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        print(f"Successfully cancelled order #{order.id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Order cancelled successfully'
        })
        
    except Order.DoesNotExist:
        print(f"Order #{order_id} not found")
        return JsonResponse({
            'error': 'Order not found'
        }, status=404)
    except Exception as e:
        print(f"Error cancelling order #{order_id}: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
def place_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            response = api_service.create_order(**data)
            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def create_user_view(request):
    # Creating a user programmatically
    user = User.objects.create_user(username="newuser", password="password123", email="newuser@example.com")
    user.save()  # Save the user object to the database
    return redirect('login')  # Redirect to login page after user creation

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Try Flask API registration first
            response = api_service.register(
                request,
                form.cleaned_data['email'],
                form.cleaned_data['username'],
                form.cleaned_data['password1'],
                form.cleaned_data['password2']
            )
            
            if 'error' not in response:
                # Create Django user
                user = form.save()
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('homepage')
            else:
                messages.error(request, response['error'])
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignUpForm()
    return render(request, 'orders/signup.html', {'form': form})

def login_view(request):
    from .forms import LoginForm  # Ensure correct form is used
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            # Try Flask API first
            response = api_service.login(request, email, password)
            if 'error' not in response:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    username = email.split('@')[0]
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )
                login(request, user)
                messages.success(request, 'Logged in successfully!')
                next_url = request.GET.get('next', 'homepage')
                return redirect(next_url)
            else:
                try:
                    user = User.objects.get(email=email)
                    user = authenticate(request, username=user.username, password=password)
                    if user is not None:
                        login(request, user)
                        messages.success(request, 'Logged in successfully!')
                        next_url = request.GET.get('next', 'homepage')
                        return redirect(next_url)
                except User.DoesNotExist:
                    pass
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()  # Always use your LoginForm for GET
    print("Form class:", form.__class__)
    print("Form fields:", list(form.fields.keys()))
    return render(request, 'orders/login.html', {'form': form})

@login_required
def menu(request):
    # Fetch menu items from Flask API
    response = api_service.get_menu(request)
    if 'error' in response:
        messages.error(request, response['error'])
        return render(request, 'orders/menu.html', {'menu_items': [], 'categories': []})

    menu_items = response.get('menu_items', [])
    # Extract unique categories from menu_items
    categories = []
    category_labels = {}
    for item in menu_items:
        cat = item.get('category', '').lower()
        if cat and cat not in [c[0] for c in categories]:
            # Use Flask's CATEGORY_CHOICES for label if needed, else capitalize
            label = cat.capitalize()
            if cat == 'beverages': label = 'Beverages'
            elif cat == 'snacks': label = 'Snacks'
            elif cat == 'meals': label = 'Meals'
            elif cat == 'desserts': label = 'Desserts'
            categories.append((cat, label))
    return render(request, 'orders/menu.html', {'menu_items': menu_items, 'categories': categories})

def order_success(request):
    return render(request, 'orders/order_success.html')


def contact_view(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contact2')  # Make sure this is a named URL
    else:
        form = ContactMessageForm()
    return render(request, 'orders/contact.html', {'form': form})  # THIS is key


def terms_and_conditions(request):
    return render(request, 'orders/terms_and_conditions.html')

@login_required
def order_details(request, order_id):
    try:
        # Restore API session if it exists
        api_session = request.session.get('api_session', {})
        if api_session:
            api_service.session.cookies.update(api_session)
        
        # Get all orders from API
        response = api_service.get_orders()
        if 'error' in response:
            messages.error(request, response['error'])
            return redirect('order_history')
        
        # Find the specific order
        orders = response.get('orders', [])
        order = None
        for o in orders:
            if str(o['id']) == str(order_id):
                order = o
                break
        
        if not order:
            messages.error(request, "Order not found")
            return redirect('order_history')
        
        # Update Django session with latest API session
        request.session['api_session'] = api_service.session.cookies.get_dict()
        
        return render(request, 'orders/order_details.html', {
            'order': order
        })
    except Exception as e:
        messages.error(request, f"Error loading order details: {str(e)}")
        return redirect('order_history')

def about_view(request):
    return render(request, 'orders/about.html')