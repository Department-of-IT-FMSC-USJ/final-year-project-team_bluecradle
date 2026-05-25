from django.contrib import admin
from . models import User, PHM_User, Parent, MOH_Officer

admin.site.register(User)
admin.site.register(PHM_User)
admin.site.register(Parent)
admin.site.register(MOH_Officer)