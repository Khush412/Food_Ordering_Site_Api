import requests
from django.conf import settings
import json
from django.middleware.csrf import get_token
from django.http import HttpRequest

class APIService:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:5000/api/v1'
        self.session = requests.Session()
    
    def _get_headers(self, request=None):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add CSRF token if request is provided
        if request:
            csrf_token = get_token(request)
            headers['X-CSRFToken'] = csrf_token
            
            # Add session cookie if available
            if 'session' in request.COOKIES:
                headers['Cookie'] = f'session={request.COOKIES["session"]}'
            
            # Add API session if available
            if 'api_session' in request.session:
                api_session = request.session['api_session']
                if 'session' in api_session:
                    headers['Cookie'] = f'session={api_session["session"]}'
            
        return headers
    
    def _handle_response(self, response):
        if response.status_code >= 400:
            try:
                error_data = response.json()
                return {'error': error_data.get('error', 'An error occurred')}
            except:
                return {'error': f'HTTP Error {response.status_code}'}
        return response.json()
    
    def _update_session(self, response, request):
        """Update session cookies and store in Django session"""
        if 'Set-Cookie' in response.headers:
            session_cookie = response.headers['Set-Cookie']
            self.session.cookies.update(response.cookies)
            
            # Store session in Django session
            if request:
                request.session['api_session'] = {
                    'session': session_cookie
                }
    
    def login(self, request, email, password):
        """Login user and store session"""
        try:
            url = f"{self.base_url}/auth/login"
            data = {
                'email': email,
                'password': password
            }
            
            response = self.session.post(url, json=data, headers=self._get_headers(request))
            
            if response.status_code == 200:
                session_data = response.json()
                self._update_session(response, request)
                return session_data
            else:
                try:
                    error_data = response.json()
                    return {'error': error_data.get('error', 'Login failed')}
                except:
                    return {'error': f'Login failed with status {response.status_code}'}
        except Exception as e:
            return {'error': str(e)}
    
    def register(self, request, email, username, password1, password2):
        url = f"{self.base_url}/auth/register"
        data = {
            'email': email,
            'username': username,
            'password1': password1,
            'password2': password2
        }
        response = self.session.post(url, json=data, headers=self._get_headers(request))
        return self._handle_response(response)
    
    def get_menu(self, request=None):
        url = f"{self.base_url}/menu"
        response = self.session.get(url, headers=self._get_headers(request))
        return self._handle_response(response)
    
    def get_cart(self, request=None):
        """Get user's cart"""
        try:
            headers = self._get_headers(request)
            
            # First try to refresh session if needed
            if not self.session.cookies.get('session'):
                menu_response = self.session.get(f"{self.base_url}/menu", headers=headers)
                if menu_response.status_code != 200:
                    return {'error': 'Please log in to view your cart'}
            
            response = self.session.get(f"{self.base_url}/cart", headers=headers)
            
            if response.status_code == 401:
                menu_response = self.session.get(f"{self.base_url}/menu", headers=headers)
                if menu_response.status_code == 200:
                    response = self.session.get(f"{self.base_url}/cart", headers=headers)
                else:
                    return {'error': 'Please log in to view your cart'}
            
            if response.status_code != 200:
                return {'error': f'Failed to get cart: {response.status_code}'}
            
            try:
                data = response.json()
                self._update_session(response, request)
                
                # Handle different response formats
                if isinstance(data, dict):
                    if 'items' in data:
                        return data
                    elif 'cart' in data:
                        cart_data = data['cart']
                        return {
                            'items': cart_data.get('items', []),
                            'subtotal': cart_data.get('subtotal', 0),
                            'delivery_fee': cart_data.get('delivery_fee', 50.00),
                            'total': cart_data.get('total', 0)
                        }
                    else:
                        return {'items': [], 'subtotal': 0, 'delivery_fee': 50.00, 'total': 50.00}
                elif isinstance(data, list):
                    subtotal = sum(item.get('price', 0) * item.get('quantity', 0) for item in data)
                    return {
                        'items': data,
                        'subtotal': subtotal,
                        'delivery_fee': 50.00,
                        'total': subtotal + 50.00
                    }
                else:
                    return {'items': [], 'subtotal': 0, 'delivery_fee': 50.00, 'total': 50.00}
                    
            except json.JSONDecodeError:
                return {'error': 'Invalid response from server'}
            
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    def add_to_cart(self, request, item_id, quantity):
        """Add item to cart"""
        try:
            url = f"{self.base_url}/cart"
            data = {
                'item_id': item_id,
                'quantity': quantity
            }
            
            response = self.session.post(url, json=data, headers=self._get_headers(request))
            self._update_session(response, request)
            return self._handle_response(response)
            
        except Exception as e:
            return {'error': str(e)}
    
    def update_cart(self, request, item_id, quantity):
        """Update cart item quantity"""
        try:
            url = f"{self.base_url}/cart/{item_id}"
            data = {
                'quantity': quantity
            }
            
            response = self.session.put(url, json=data, headers=self._get_headers(request))
            self._update_session(response, request)
            return self._handle_response(response)
            
        except Exception as e:
            return {'error': str(e)}
    
    def remove_from_cart(self, request, item_id):
        """Remove item from cart"""
        try:
            url = f"{self.base_url}/cart/{item_id}"
            
            response = self.session.delete(url, headers=self._get_headers(request))
            self._update_session(response, request)
            return self._handle_response(response)
            
        except Exception as e:
            return {'error': str(e)}
    
    def create_order(self, request, full_name, email, phone, address, payment_method):
        """Create a new order"""
        try:
            print("API Service - Creating order...")  # Debug log
            url = f"{self.base_url}/orders"
            
            # Get cart first to ensure we have the latest items
            cart_response = self.get_cart(request)
            if 'error' in cart_response:
                print("API Service - Error getting cart:", cart_response['error'])  # Debug log
                return {'error': f"Failed to get cart: {cart_response['error']}"}
            
            cart_items = cart_response.get('items', [])
            if not cart_items:
                return {'error': 'Cart is empty'}
            
            # Prepare order data
            data = {
                'full_name': full_name,
                'email': email,
                'phone': phone,
                'address': address,
                'payment_method': payment_method,
                'items': cart_items,
                'subtotal': cart_response.get('subtotal', 0),
                'delivery_fee': cart_response.get('delivery_fee', 50.00),
                'total': cart_response.get('total', 0)
            }
            
            print("API Service - Order data:", data)  # Debug log
            
            # Ensure we have a valid session
            headers = self._get_headers(request)
            if not self.session.cookies.get('session'):
                print("API Service - No session cookie, attempting to refresh...")  # Debug log
                menu_response = self.session.get(f"{self.base_url}/menu", headers=headers)
                if menu_response.status_code != 200:
                    return {'error': 'Please log in to place an order'}
            
            # Create order
            response = self.session.post(url, json=data, headers=headers)
            print("API Service - Order response status:", response.status_code)  # Debug log
            print("API Service - Order response headers:", dict(response.headers))  # Debug log
            print("API Service - Order response content:", response.text)  # Debug log
            
            if response.status_code == 401:
                print("API Service - Session expired, attempting to refresh...")  # Debug log
                menu_response = self.session.get(f"{self.base_url}/menu", headers=headers)
                if menu_response.status_code == 200:
                    print("API Service - Session refreshed, retrying order creation...")  # Debug log
                    response = self.session.post(url, json=data, headers=headers)
                else:
                    return {'error': 'Please log in to place an order'}
            
            if response.status_code != 201:
                try:
                    error_data = response.json()
                    return {'error': error_data.get('error', 'Failed to create order')}
                except:
                    return {'error': f'Failed to create order: {response.status_code}'}
            
            # Clear cart after successful order
            try:
                clear_response = self.session.post(f"{self.base_url}/cart/clear", headers=headers)
                if clear_response.status_code != 200:
                    print("API Service - Warning: Failed to clear cart after order")  # Debug log
            except Exception as e:
                print("API Service - Warning: Error clearing cart:", str(e))  # Debug log
            
            return response.json()
            
        except Exception as e:
            print("API Service - Error creating order:", str(e))  # Debug log
            return {'error': str(e)}
    
    def get_orders(self, request=None):
        """Get user's order history"""
        try:
            print("API Service - Getting orders...")
            print("API Service - Session cookies:", self.session.cookies.get_dict())
            
            headers = self._get_headers(request)
            print("API Service - Headers:", headers)
            
            response = self.session.get(f"{self.base_url}/orders", headers=headers)
            print("API Service - Response status:", response.status_code)
            print("API Service - Response headers:", dict(response.headers))
            print("API Service - Response content:", response.text)
            
            if response.status_code == 401:
                print("API Service - Session expired, attempting to refresh...")
                menu_response = self.session.get(f"{self.base_url}/menu", headers=headers)
                if menu_response.status_code == 200:
                    print("API Service - Session refreshed, retrying orders request...")
                    response = self.session.get(f"{self.base_url}/orders", headers=headers)
                else:
                    return {'error': 'Please log in to view your orders'}
            
            if response.status_code != 200:
                return {'error': f'Failed to get orders: {response.status_code}'}
            
            try:
                data = response.json()
                print("API Service - Parsed response:", data)
                if isinstance(data, dict) and 'orders' in data:
                    return data
                elif isinstance(data, list):
                    return {'orders': data}
                else:
                    return {'orders': []}
            except json.JSONDecodeError:
                print("API Service - Failed to parse JSON response")
                return {'error': 'Invalid response from server'}
            
        except requests.exceptions.RequestException as e:
            print("API Service - Error getting orders:", str(e))
            return {'error': str(e)} 