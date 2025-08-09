#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_price_project.settings')
django.setup()

from userauth.models import CustomUser

try:
    # Check if superuser already exists
    if CustomUser.objects.filter(is_superuser=True).exists():
        print("Superuser already exists")
    else:
        # Create superuser
        user = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("Superuser created successfully!")
        print("Username: admin")
        print("Password: admin123")
except Exception as e:
    print(f"Error creating superuser: {e}")
