from django.urls import path #type:ignore
from . import views #type:ignore
from django.conf import settings #type:ignore
from django.conf.urls.static import static #type:ignore
from django.contrib.auth import views as auth_views #type:ignore
from . import views

urlpatterns = [
    path('', views.restaurant_list, name='homepage'),
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('ziggy-cafe/', views.ziggy_cafe_menu, name='ziggy_cafe_menu'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Only one login/logout path needed
    path('login/', views.login_view, name='login'),  # Use your custom login_view
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('terms/', views.terms_and_conditions, name='terms'),
    path('checkout/', views.checkout, name='checkout'),
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('place_order/', views.place_order, name='place_order'),
    path('signup/', views.signup, name='signup'),
    path('menu/', views.menu, name='menu'),
    path('order-success/', views.order_success, name='order_success'),
    path('contact/', views.contact_view, name='contact'),
    path('order-history/', views.order_history, name='order_history'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('create-user/', views.create_user_view, name='create_user'),
    path('about/', views.about_view, name='about'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])


