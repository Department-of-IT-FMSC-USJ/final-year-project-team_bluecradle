from django.db import models
from django.contrib.auth.models import AbstractUser
from . constants import UserRole

class User(AbstractUser):
    # Custom built user model. Used because an email-based login is required which is unlkely in built in User model.
    email = models.EmailField(unique = True)
    username = models.CharField(unique = True, max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def get_role(self):
        if hasattr(self, 'phm_profile'):
            return UserRole.PHM
        elif hasattr(self, 'parent_profile'):
            return UserRole.PARENT
        elif hasattr(self, 'moh_profile'):
            return UserRole.MOH
        else:
            return
        
class PHM_User(models.Model):
    user = models.OneToOneField(
        User,
        on_delete = models.CASCADE,
        related_name = 'phm_profile'
    )
    full_name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=50, unique=True)
    contact_no = models.CharField(max_length=10)
    moh_division = models.CharField(max_length=100)
    operational_area = models.CharField(max_length=200)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.full_name} - {self.moh_division}'
    

# ---------------- PARENT MODEL ----------------
class Parent(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='guardian_profile'   # ⚠️ MUST be guardian_profile — Minoli's permission.py checks this exact name
    )
    full_name = models.CharField(max_length=200)
    phn = models.CharField(max_length=50, unique=True)        # Personal Health Number from physical CHDR booklet
    contact_no = models.CharField(max_length=10, blank=True, null=True)   # Optional
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.full_name} - PHN: {self.phn}'


# ---------------- MOH MODEL ----------------
class MOH_Officer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='moh_profile'        # Must be moh_profile — Minoli's permission.py checks this
    )
    full_name = models.CharField(max_length=200)
    employee_id = models.CharField(max_length=50, unique=True)   # MOH Officer's official employee ID
    moh_division = models.CharField(max_length=100)
    contact_no = models.CharField(max_length=10)
    is_verified = models.BooleanField(default=False)    # Admin verifies via Django admin panel
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.full_name} - {self.moh_division}'
