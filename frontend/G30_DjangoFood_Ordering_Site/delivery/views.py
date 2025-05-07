from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RiderRegistrationForm
from .models import Rider
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Rider
from .forms import ContactMessageForm

def home(request):
    return render(request, 'delivery/home.html')

def about(request):
    return render(request, 'delivery/about.html')

def contact(request):
    return render(request, 'delivery/contact.html')

def terms(request):
    return render(request, 'delivery/terms.html')

def privacy(request):
    return render(request, 'delivery/privacy.html')

def register_rider(request):
    if request.method == 'POST':
        form = RiderRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            rider = form.save()
            print("Rider saved:", rider)  # ✅ Debugging line
            messages.success(request, "You have successfully registered as a rider. Please wait for admin approval.")
            return redirect('waiting_for_approval')  # Ensure this URL is properly defined
        else:
            print("Form is NOT valid ❌")            # ✅ Debug line
            print(form.errors)                       # ✅ See what's wrong
    else:
        form = RiderRegistrationForm()
    return render(request, 'delivery/register_rider.html', {'form': form})



@login_required
def rider_dashboard(request):
    try:
        rider = Rider.objects.get(user=request.user)
        if not rider.is_approved:
            return redirect('waiting_for_approval')  # Redirect if not approved
    except Rider.DoesNotExist:
        return redirect('register_rider')  # Redirect if rider doesn't exist

    return render(request, 'delivery/rider_dashboard.html', {'rider': rider})

def login_rider(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('rider_dashboard')
        else:
            messages.error(request, 'Invalid email or password')
    return render(request, 'delivery/rider_login.html')

def waiting_for_approval(request):
    return render(request, 'delivery/waiting_for_approval.html')


@login_required
def toggle_duty_status(request):
    rider = Rider.objects.get(user=request.user)
    rider.on_duty = not rider.on_duty
    rider.save()
    return redirect('rider_dashboard')  # name of your dashboard url


def contact_view(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been submitted successfully!')
            return redirect('contact')
    else:
        form = ContactMessageForm()
    return render(request, 'delivery/contact.html', {'form': form})
