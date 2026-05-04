#!/usr/bin/env python
"""
Reset admin password to a known value
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

from django.contrib.auth.models import User

def reset_admin_password():
    """Reset admin password to 'admin123'"""
    print("=" * 60)
    print("Resetting Admin Password")
    print("=" * 60)
    
    try:
        # Get or create admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@gmail.com',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        
        if created:
            print("\n✅ Created new admin user")
        else:
            print(f"\n✅ Found existing admin user: {admin.username}")
        
        # Set password
        new_password = 'admin123'
        admin.set_password(new_password)
        admin.save()
        
        print(f"\n✅ Password reset successfully!")
        print(f"\nLogin credentials:")
        print(f"  Username: admin")
        print(f"  Password: {new_password}")
        print(f"\nYou can now login at: http://localhost:3000/login")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    reset_admin_password()
