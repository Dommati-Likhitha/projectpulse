#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to the Python path
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ethara_project.settings')

django.setup()

from django.contrib.auth import get_user_model
from project_app.models import UserProfile

User = get_user_model()

# Create superuser
user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@example.com',
        'is_staff': True,
        'is_superuser': True
    }
)

if created:
    user.set_password('admin123')
    user.save()
    print("Superuser 'admin' created successfully!")
else:
    print("Superuser 'admin' already exists.")

# Ensure UserProfile exists
profile, profile_created = UserProfile.objects.get_or_create(
    user=user,
    defaults={'role': 'admin'}
)

if profile_created:
    print("UserProfile created for admin.")
else:
    print("UserProfile already exists for admin.")