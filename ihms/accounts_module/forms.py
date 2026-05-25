from django import forms
from django.contrib.auth.password_validation import validate_password
from . models import User, PHM_User, Parent, MOH_Officer
from django.contrib.auth.forms import AuthenticationForm

class PHMRegistrationForm(forms.Form):
    full_name = forms.CharField(
        label='Full Name',
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Agatha Christy',
                'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
            }
        )
    )

    registration_number = forms.CharField(
        label='SLMC Registration Number',
        max_length=50,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'SEC51 - 1234',
                'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all',
                'oninput': 'this.value = this.value.toUpperCase()'
            }
        )
    )

    moh_division = forms.CharField(
        label='MOH Division',
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Deraniyagala',
                'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
            }
        )
    )

    operational_area = forms.CharField(
        label='Operational Area',
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Maliboda',
                'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
            }
        )
    )

    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'agathachristy@example.com',
                'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
            }
        )
    )

    contact_no = forms.CharField(
        label='Contact Number',
        max_length=20,
        widget=forms.TextInput(
            attrs={
                'placeholder': '0771234567',
                'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
            }
        )
    )

    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'agathachristy@example.com', 
                'readonly': 'readonly',
                'class': 'w-full bg-surface-container-high border-0 rounded-xl px-4 py-3 text-primary-container font-medium cursor-not-allowed ring-1 ring-inset ring-outline-variant/30'
            }
        )
    )

    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Create a password',
                'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
            }
        ),
        validators=[validate_password]
    )

    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Repeat your password',
                'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
            }
        )
    )

    # --------- Validation ---------
    def clean_registration_number(self):
        reg_number = self.cleaned_data.get('registration_number')
        if PHM_User.objects.filter(registration_number = reg_number):
            self.add_error(
                'registration_number', 
                'This SLMC registration number is already registered.'
            ) 
        return reg_number        
    
    def clean_contact_no(self):
        contact = self.cleaned_data.get('contact_no')
        if contact is None or len(contact) != 10:
            self.add_error(
                'contact_no',
                'Phone number must be 10 digits.'
            )
        return contact

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email = email):
            self.add_error(
                'email',
                'An account with this email already exists.'
            )
        return email
        
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')  

        return cleaned_data
    
# ---------------- PARENT REGISTRATION FORM ----------------
class ParentRegistrationForm(forms.Form):

    full_name = forms.CharField(
        label='Full Name',
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Kumari Perera',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
        })
    )

    phn = forms.CharField(
        label='Personal Health Number (PHN)',
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter PHN from your CHDR booklet',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
        })
    )

    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'placeholder': 'kumari@example.com',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
        })
    )

    contact_no = forms.CharField(
        label='Contact Number (Optional)',
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '0771234567',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
        })
    )

    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Auto-filled from your email',
            'readonly': 'readonly',
            'class': 'w-full bg-surface-container-high border-0 rounded-xl px-4 py-3 text-primary-container font-medium cursor-not-allowed ring-1 ring-inset ring-outline-variant/30'
        })
    )

    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create a password',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
        })
        # No validate_password here intentionally —
        # A PHM or MOH registering as Parent will enter their existing password.
        # That credential check happens in the view via authenticate(), not in the form.
    )

    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repeat your password',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
        })
    )

    def clean_phn(self):
        phn = self.cleaned_data.get('phn')
        if Parent.objects.filter(phn=phn).exists():
            self.add_error('phn', 'This PHN is already registered in the system.')
        return phn

    def clean_contact_no(self):
        contact = self.cleaned_data.get('contact_no')
        if contact and len(contact) != 10:
            self.add_error('contact_no', 'Phone number must be 10 digits.')
        return contact

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data


# ---------------- MOH REGISTRATION FORM ----------------
class MOHRegistrationForm(forms.Form):

    full_name = forms.CharField(
        label='Full Name',
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Dr. Nimal Silva',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
        })
    )

    employee_id = forms.CharField(
        label='Employee ID',
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'MOH-12345',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all',
            'oninput': 'this.value = this.value.toUpperCase()'
        })
    )

    moh_division = forms.CharField(
        label='MOH Division',
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Deraniyagala',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
        })
    )

    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'placeholder': 'nimal@health.gov.lk',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
        })
    )

    contact_no = forms.CharField(
        label='Contact Number',
        max_length=10,
        widget=forms.TextInput(attrs={
            'placeholder': '0771234567',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
        })
    )

    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Auto-filled from your email',
            'readonly': 'readonly',
            'class': 'w-full bg-surface-container-high border-0 rounded-xl px-4 py-3 text-primary-container font-medium cursor-not-allowed ring-1 ring-inset ring-outline-variant/30'
        })
    )

    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create a password',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
        }),
        validators=[validate_password]
    )

    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repeat your password',
            'class': 'w-full bg-surface-container-lowest border-0 rounded-xl px-4 py-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-primary transition-all'
        })
    )

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if MOH_Officer.objects.filter(employee_id=employee_id).exists():
            self.add_error('employee_id', 'This Employee ID is already registered.')
        return employee_id

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            self.add_error('email', 'An account with this email already exists.')
        return email

    def clean_contact_no(self):
        contact = self.cleaned_data.get('contact_no')
        if contact is None or len(contact) != 10:
            self.add_error('contact_no', 'Phone number must be 10 digits.')
        return contact

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].label = 'Username/Email'
        self.fields['username'].widget.attrs.update(
            {
                'class': 'w-full bg-surface-container-low border-none rounded-xl py-4 pl-12 pr-4 text-on-surface placeholder:text-on-surface-variant/50 focus:ring-2 focus:ring-primary transition-all',
                'placeholder': 'johndoe@example.com'
            }
        )

        self.fields['password'].label = 'Password'
        self.fields['password'].widget.attrs.update(
            {
                'class': 'w-full bg-surface-container-low border-none rounded-xl py-4 pl-12 pr-12 text-on-surface placeholder:text-on-surface-variant/50 focus:ring-2 focus:ring-primary transition-all',
                'placeholder': '••••••••••••'
            }
        )