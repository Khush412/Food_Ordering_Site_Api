from django.urls import path
from . import views_admin

app_name = 'orders'

urlpatterns = [
    path('admin/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('admin/orders/', views_admin.order_list, name='admin_order_list'),
    path('admin/orders/<int:pk>/', views_admin.order_detail, name='admin_order_detail'),
    path('admin/orders/create/', views_admin.order_create, name='admin_order_create'),
    path('admin/orders/<int:pk>/edit/', views_admin.order_edit, name='admin_order_edit'),
    path('admin/orders/<int:pk>/delete/', views_admin.order_delete, name='admin_order_delete'),
    path('admin/contact-messages/', views_admin.contact_messages_list, name='admin_contact_messages'),
    path('admin/riders/', views_admin.rider_list, name='admin_rider_list'),
    path('admin/riders/<int:pk>/edit/', views_admin.rider_edit, name='admin_rider_edit'),
    path('admin/riders/<int:pk>/approve/', views_admin.rider_approve, name='admin_rider_approve'),
]
