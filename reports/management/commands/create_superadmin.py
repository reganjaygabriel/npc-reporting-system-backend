#!/usr/bin/env python3

"""
Django management command to create a super admin user
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
import getpass

class Command(BaseCommand):
    help = 'Create a super admin user with full system access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the super admin',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the super admin',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the super admin (will prompt if not provided)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if user exists (will update existing user)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔐 Creating Super Admin User'))
        self.stdout.write('=' * 50)
        
        # Get username
        username = options.get('username')
        if not username:
            username = input('Enter username for super admin: ').strip()
            if not username:
                self.stdout.write(self.style.ERROR('❌ Username is required'))
                return
        
        # Get email
        email = options.get('email')
        if not email:
            email = input('Enter email for super admin: ').strip()
            if not email:
                self.stdout.write(self.style.ERROR('❌ Email is required'))
                return
        
        # Get password
        password = options.get('password')
        if not password:
            password = getpass.getpass('Enter password for super admin: ')
            if not password:
                self.stdout.write(self.style.ERROR('❌ Password is required'))
                return
            
            # Confirm password
            password_confirm = getpass.getpass('Confirm password: ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('❌ Passwords do not match'))
                return
        
        try:
            with transaction.atomic():
                # Check if user exists
                user_exists = User.objects.filter(username=username).exists()
                
                if user_exists and not options.get('force'):
                    self.stdout.write(
                        self.style.ERROR(f'❌ User "{username}" already exists. Use --force to update.')
                    )
                    return
                
                if user_exists:
                    # Update existing user
                    user = User.objects.get(username=username)
                    user.email = email
                    user.set_password(password)
                    user.is_staff = True
                    user.is_superuser = True
                    user.is_active = True
                    user.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Updated existing user "{username}" to super admin')
                    )
                else:
                    # Create new user
                    user = User.objects.create_superuser(
                        username=username,
                        email=email,
                        password=password
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created new super admin user "{username}"')
                    )
                
                # Create or update user profile if it exists
                try:
                    from reports.models import UserProfile
                    profile, created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'role': 'ADMIN',
                            'full_name': username.title(),
                            'department': 'IT Administration',
                            'phone': '',
                            'position': 'System Administrator'
                        }
                    )
                    
                    if not created:
                        profile.role = 'ADMIN'
                        profile.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {"Created" if created else "Updated"} user profile')
                    )
                    
                except ImportError:
                    # UserProfile model doesn't exist, skip
                    pass
                
                # Display user information
                self.stdout.write('\n' + '=' * 50)
                self.stdout.write(self.style.SUCCESS('🎉 Super Admin User Created Successfully!'))
                self.stdout.write('=' * 50)
                self.stdout.write(f'Username: {user.username}')
                self.stdout.write(f'Email: {user.email}')
                self.stdout.write(f'Is Staff: {user.is_staff}')
                self.stdout.write(f'Is Superuser: {user.is_superuser}')
                self.stdout.write(f'Is Active: {user.is_active}')
                self.stdout.write('\n📋 Access Information:')
                self.stdout.write('- Frontend System: http://localhost:3001')
                self.stdout.write('- Django Admin Panel: http://localhost:8000/admin')
                self.stdout.write('- API Access: Full access to all endpoints')
                self.stdout.write('\n🔑 Login Credentials:')
                self.stdout.write(f'Username: {username}')
                self.stdout.write('Password: [The password you just set]')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating super admin: {str(e)}')
            )
            raise