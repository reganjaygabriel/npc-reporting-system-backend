#!/usr/bin/env python3
"""
Email configuration helper for NPC Reporting System
"""

import os
from pathlib import Path

def setup_email_config():
    """Interactive email configuration setup"""
    
    print("📧 NPC Reporting System - Email Configuration Setup")
    print("=" * 55)
    
    env_file = Path(__file__).parent / '.env'
    
    # Read existing .env file
    env_content = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_content[key] = value
    
    print("\nCurrent email configuration:")
    print(f"  EMAIL_BACKEND: {env_content.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')}")
    print(f"  EMAIL_HOST: {env_content.get('EMAIL_HOST', 'smtp.gmail.com')}")
    print(f"  DEFAULT_FROM_EMAIL: {env_content.get('DEFAULT_FROM_EMAIL', 'noreply@npc-reporting.com')}")
    
    print("\nEmail Backend Options:")
    print("1. Console Backend (Development) - Prints emails to console")
    print("2. SMTP Backend (Production) - Sends real emails")
    print("3. File Backend (Testing) - Saves emails to files")
    
    choice = input("\nSelect email backend (1-3): ").strip()
    
    if choice == '1':
        # Console backend
        env_content['EMAIL_BACKEND'] = 'django.core.mail.backends.console.EmailBackend'
        print("✅ Console backend configured - emails will print to console")
        
    elif choice == '2':
        # SMTP backend
        env_content['EMAIL_BACKEND'] = 'django.core.mail.backends.smtp.EmailBackend'
        
        print("\nSMTP Configuration:")
        print("1. Gmail")
        print("2. Office 365")
        print("3. Custom SMTP")
        
        smtp_choice = input("Select SMTP provider (1-3): ").strip()
        
        if smtp_choice == '1':
            # Gmail
            env_content['EMAIL_HOST'] = 'smtp.gmail.com'
            env_content['EMAIL_PORT'] = '587'
            env_content['EMAIL_USE_TLS'] = 'True'
            
            email = input("Gmail address: ").strip()
            password = input("App password (not regular password): ").strip()
            
            env_content['EMAIL_HOST_USER'] = email
            env_content['EMAIL_HOST_PASSWORD'] = password
            
        elif smtp_choice == '2':
            # Office 365
            env_content['EMAIL_HOST'] = 'smtp.office365.com'
            env_content['EMAIL_PORT'] = '587'
            env_content['EMAIL_USE_TLS'] = 'True'
            
            email = input("Office 365 email: ").strip()
            password = input("Password: ").strip()
            
            env_content['EMAIL_HOST_USER'] = email
            env_content['EMAIL_HOST_PASSWORD'] = password
            
        elif smtp_choice == '3':
            # Custom SMTP
            host = input("SMTP host: ").strip()
            port = input("SMTP port (587): ").strip() or '587'
            use_tls = input("Use TLS? (y/n): ").strip().lower() == 'y'
            
            email = input("Email username: ").strip()
            password = input("Email password: ").strip()
            
            env_content['EMAIL_HOST'] = host
            env_content['EMAIL_PORT'] = port
            env_content['EMAIL_USE_TLS'] = 'True' if use_tls else 'False'
            env_content['EMAIL_HOST_USER'] = email
            env_content['EMAIL_HOST_PASSWORD'] = password
        
        from_email = input(f"From email ({env_content.get('DEFAULT_FROM_EMAIL', 'noreply@npc-reporting.com')}): ").strip()
        if from_email:
            env_content['DEFAULT_FROM_EMAIL'] = from_email
            
        print("✅ SMTP backend configured")
        
    elif choice == '3':
        # File backend
        env_content['EMAIL_BACKEND'] = 'django.core.mail.backends.filebased.EmailBackend'
        env_content['EMAIL_FILE_PATH'] = 'emails'
        print("✅ File backend configured - emails will be saved to 'emails' directory")
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.write("# NPC Reporting System Configuration\n")
        f.write("SECRET_KEY=django-insecure-test-key-for-development-only-change-in-production\n")
        f.write("DEBUG=True\n")
        f.write("ALLOWED_HOSTS=localhost,127.0.0.1\n\n")
        
        f.write("# Database Configuration\n")
        f.write("DB_NAME=npc_reporting\n")
        f.write("DB_USER=postgres\n")
        f.write("DB_PASSWORD=postgres\n")
        f.write("DB_HOST=localhost\n")
        f.write("DB_PORT=5432\n\n")
        
        f.write("# Email Configuration\n")
        for key, value in env_content.items():
            if key.startswith('EMAIL_') or key == 'DEFAULT_FROM_EMAIL':
                f.write(f"{key}={value}\n")
        
        f.write("\n# AI Chatbot Configuration - Free Mode (No API Key Needed)\n")
        f.write("AI_PROVIDER=\n")
        f.write("OPENAI_API_KEY=your-openai-api-key-here\n")
        f.write("OPENAI_MODEL=gpt-3.5-turbo\n")
    
    print(f"\n✅ Configuration saved to {env_file}")
    print("\n📧 Test your email configuration:")
    print("   cd npc-reporting-system")
    print("   python test_email_notifications.py")
    
    print("\n🔄 Restart your Django server to apply changes:")
    print("   python manage.py runserver")

if __name__ == '__main__':
    setup_email_config()