from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, CustomUserCreationForm
from predictor.utils import send_sms
from django.core.mail import send_mail
from django.conf import settings

def root_redirect(request):
    """Redirect root URL to dashboard if authenticated, otherwise to login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Send welcome SMS
            full_phone = f"{form.cleaned_data['country_code']}{form.cleaned_data['phone_number']}"
            sms_message = f"Welcome to Food Price Predictor! Your account has been created successfully."
            send_sms(full_phone, sms_message)
            
            # Send welcome email
            email_message = f"""
            Welcome to Food Price Predictor!
            
            Your account has been created successfully.
            You can now start making predictions and receive them via SMS and email.
            
            Best regards,
            Food Price Predictor Team
            """
            send_mail(
                'Welcome to Food Price Predictor',
                email_message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Registration successful! Welcome messages have been sent.')
            return redirect('home')
        messages.error(request, 'Unsuccessful registration. Invalid information.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'userauth/login.html')

@login_required
def dashboard(request):
    """User dashboard view"""
    return render(request, 'userauth/dashboard.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')
