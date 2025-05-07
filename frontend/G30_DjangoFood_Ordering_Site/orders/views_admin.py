from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Order
from .forms import OrderForm  # You'll need to create this form
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from delivery.models import Rider
from delivery.forms import RiderRegistrationForm

def is_admin(user):
    return user.is_staff

@user_passes_test(is_admin)
def order_list(request):
    orders = Order.objects.all()
    return render(request, 'orders/order_list.html', {'orders': orders})

@user_passes_test(is_admin)
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/order_detail.html', {'order': order})

@user_passes_test(is_admin)
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('orders:admin_order_list')
    else:
        form = OrderForm()
    return render(request, 'orders/order_form.html', {'form': form})

@user_passes_test(is_admin)
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('orders:admin_order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
    return render(request, 'orders/order_form.html', {'form': form})

@user_passes_test(is_admin)
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        return redirect('orders:admin_order_list')
    return render(request, 'orders/order_confirm_delete.html', {'order': order})

@user_passes_test(is_admin)
def contact_messages_list(request):
    messages = ContactMessage.objects.all().order_by('-created_at')
    return render(request, 'orders/contact_messages_list.html', {'messages': messages})

from .models import Order, ContactMessage

@user_passes_test(is_admin)
def admin_dashboard(request):
    order_count = Order.objects.count()
    message_count = ContactMessage.objects.count()
    return render(request, 'orders/admin_dashboard.html', {
        'order_count': order_count,
        'message_count': message_count,
    })

# orders/views_admin.py


def rider_list(request):
    riders = Rider.objects.all()
    return render(request, 'orders/rider_list.html', {'riders': riders})

def rider_edit(request, pk):
    rider = get_object_or_404(Rider, pk=pk)
    if request.method == 'POST':
        form = RiderRegistrationForm(request.POST, instance=rider)
        if form.is_valid():
            form.save()
            return redirect('orders:admin_rider_list')
    else:
        form = RiderRegistrationForm(instance=rider)
    return render(request, 'orders/rider_edit.html', {'form': form, 'rider': rider})

def rider_approve(request, pk):
    rider = get_object_or_404(Rider, pk=pk)
    rider.is_approved = True
    rider.save()
    return redirect('orders:admin_rider_list')

from delivery.models import Rider

def admin_dashboard(request):
    order_count = Order.objects.count()
    message_count = ContactMessage.objects.count()
    rider_count = Rider.objects.count()  # <-- Add this line
    return render(request, 'orders/admin_dashboard.html', {
        'order_count': order_count,
        'message_count': message_count,
        'rider_count': rider_count,  # <-- Include this
    })
