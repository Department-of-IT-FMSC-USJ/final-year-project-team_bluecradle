from django.shortcuts import render, redirect
from . constants import UserRole
from . models import User, PHM_User
from . forms import PHMRegistrationForm, LoginForm
from django.db import transaction
from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth import login, logout
from django.urls import reverse

def signup_role(request):
    if request.method == 'POST':
        selected_signup_role = request.POST.get('role')
        # Store role in session for use in register view
        request.session['signup_role'] = selected_signup_role
        # Redirect to register view
        return redirect('user:register')  
    
    return render(
        request,
        'accounts_module/signup_role.html',
        {
            'title': 'BlueCradle - Register - Select Role'
        }
    )

def register(request):
    signup_role_value =  request.session.get('signup_role')

    if signup_role_value == UserRole.PHM:
        return register_phm(request)
    elif signup_role_value == UserRole.PARENT:
        return register_parent(request)
    elif signup_role_value == UserRole.MOH:
        return register_moh(request)
    else:
        return signup_role(request)

def register_user(registration_form):
    user = User.objects.create_user(
        email = registration_form.cleaned_data['email'],
        username = registration_form.cleaned_data['username'],
        password = registration_form.cleaned_data['password']
    )

    return user

def register_phm(request):
    if request.method == 'POST':
        form = PHMRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    PHM_User.objects.create(
                        user = register_user(form),
                        full_name=form.cleaned_data['full_name'],
                        registration_number=form.cleaned_data['registration_number'],
                        contact_no=form.cleaned_data['contact_no'],
                        moh_division=form.cleaned_data['moh_division'],
                        operational_area=form.cleaned_data['operational_area'],
                        is_verified=False,
                    )

                    return redirect(f"{reverse('user:user_login')}?registered=true")

            except Exception as e:
                messages.error(request, 'Registration failed. Please try again.')
        else:
            # Add message for form validation errors
            if form.errors:
                messages.error(request, 'Registration failed. Please correct the errors below.')

    else:
            form = PHMRegistrationForm()
                
    return render(
        request, 
        'accounts_module/register_phm.html', 
        {
            'title': 'BlueCradle - Register as PHM',
            'form': form
        }
    )

def register_parent(request):
    # Complete this
    return render(request, 'accounts_module/register_parent.html', {'title': 'BlueCradle - Register as Parent'})

def register_moh(request):
    # Complete this
    return render(request, 'accounts_module/register_moh.html', {'title': 'BlueCradle - Register as MOH'})

def user_login(request):
    if request.user.is_authenticated:
        return role_redirect(request)

    if request.method == 'POST':
        # Handle role selection POST from multi-role screen
        if 'role' in request.POST:
            return select_session_role(request)
        
        # Handle login form POST
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return role_redirect(request)
        else:
            messages.error(
                request, 
                'Invalid email or password.'
            )
    else:
        form = LoginForm(request)

    return render(
        request, 
        'accounts_module/login.html',
        {
            'form': form
        }
    )


def role_redirect(request):
    if not request.user.is_authenticated:
        return redirect('user:user_login')

    user = request.user
    roles = []

    if hasattr(user, 'phm_profile'):
        roles.append(UserRole.PHM)
    if hasattr(user, 'guardian_profile'):
        roles.append(UserRole.PARENT)
    if hasattr(user, 'moh_profile'):
        roles.append(UserRole.MOH)

    if len(roles) == 1:
        request.session['active_role'] = roles[0]
        return redirect_to_dashboard(roles[0])
    
    elif len(roles) > 1:
        return render(
            request,
            'accounts_module/role_select_session.html',
            {
                'roles': roles
            }
        )
    else:
        messages.error(request, 'No role assigned to this account.')
        logout(request)
        return redirect('user:user_login')


def select_session_role(request):
    role = request.POST.get('role')
    request.session['active_role'] = role
    return redirect_to_dashboard(role)


def redirect_to_dashboard(role):
    if role == UserRole.PHM:
        return redirect('clinic:phm_dashboard')
    elif role == UserRole.PARENT:
        return redirect('parent:dashboard')
    elif role == UserRole.MOH:
        return redirect('moh:dashboard')
    return redirect('user:user_login')


def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect('user:user_login')