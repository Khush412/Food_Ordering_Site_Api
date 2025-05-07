"""
URL configuration for ziggy_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin #type:ignore 
from django.urls import path, include #type:ignore
from django.conf import settings #type:ignore
from django.conf.urls.static import static#type:ignore
from orders.views import signup, restaurant_list, login_view #type:ignore

urlpatterns = [
    path('', restaurant_list, name='homepage'),  # Homepage at root
    path('orders/', include('orders.urls')),
    path('signup/', signup, name='signup'),
    path('login/', login_view, name='login'),  # Added project-level login route
    path('delivery/', include('delivery.urls', namespace='delivery')),  # Added namespace
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
