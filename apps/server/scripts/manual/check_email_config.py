#!/usr/bin/env python3
"""
Diagnostic script to check SendGrid email configuration.
Run this to verify if emails can be sent.
"""
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("SendGrid Email Configuration Check")
print("=" * 60)

# Check required environment variables
sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
sendgrid_sender_email = os.getenv("SENDGRID_SENDER_EMAIL")
sendgrid_sender_name = os.getenv("SENDGRID_SENDER_NAME", "AssessorAI")
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8000")

print(f"\n✓ Configuration Status:")
print(f"  SENDGRID_API_KEY: {'✓ Set' if sendgrid_api_key else '✗ NOT SET'}")
print(f"  SENDGRID_SENDER_EMAIL: {sendgrid_sender_email if sendgrid_sender_email else '✗ NOT SET'}")
print(f"  SENDGRID_SENDER_NAME: {sendgrid_sender_name}")
print(f"  FRONTEND_URL: {frontend_url}")

# Try to import and initialize the email service
print(f"\n✓ Email Service Status:")

# Check if sendgrid is installed
try:
    import sendgrid
    print(f"  SendGrid package: ✓ Installed (version {sendgrid.__version__})")
except ImportError:
    print(f"  SendGrid package: ✗ NOT INSTALLED")
    print(f"  Install with: pip install sendgrid")

# Manual check based on environment variables (since we can't import the service directly)
if sendgrid_api_key and sendgrid_sender_email:
    print(f"  Email service would be configured: ✓")
    print(f"\n✓ Email service is ready to send emails!")
else:
    print(f"  Email service would be configured: ✗")
    print(f"\n⚠ Email service is NOT configured!")
    print(f"  Please set the following environment variables:")
    if not sendgrid_api_key:
        print(f"    - SENDGRID_API_KEY")
    if not sendgrid_sender_email:
        print(f"    - SENDGRID_SENDER_EMAIL")

# Check template directory
print(f"\n✓ Template Check:")
template_dir = ROOT_DIR / "services" / "templates" / "emails"
if template_dir.exists():
    print(f"  Template directory: ✓ {template_dir}")
    templates = list(template_dir.glob("*.md"))
    print(f"  Available templates:")
    for t in sorted(templates):
        print(f"    - {t.name}")
else:
    print(f"  ✗ Template directory not found: {template_dir}")

print("\n" + "=" * 60)
