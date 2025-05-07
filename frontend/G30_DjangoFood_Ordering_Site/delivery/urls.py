from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_rider, name='register_rider'),
    path('waiting-for-approval/', views.waiting_for_approval, name='waiting_for_approval'),
    path('login/', views.login_rider, name='login_rider'),
    path('dashboard/', views.rider_dashboard, name='rider_dashboard'),

    # Additional pages for navbar/footer
    path('about/', views.about, name='about'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('contact/', views.contact_view, name='contact'),
    path('register/', views.register_rider, name='register_rider'),
    path('waiting/', views.waiting_for_approval, name='waiting_for_approval'),
    path('toggle-duty/', views.toggle_duty_status, name='toggle_duty_status'),  # 👈 Add this
]
