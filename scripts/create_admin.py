import os
import sys

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app"))

from core import models, security
from core.database import SessionLocal


def create_initial_user():
    db = SessionLocal()
    email = "admin@ingestiq.com"
    client = "ingestiq_admin"

    if db.query(models.User).filter(models.User.email == email).first():
        print(f"User {email} already exists.")
        return

    print(f"Creating admin user: {email}")
    user = models.User(
        email=email,
        hashed_password=security.get_password_hash("admin123"),  # Change in prod!
        role=models.UserRole.ADMIN,
        client_id=client,
    )
    db.add(user)
    db.commit()
    print("Admin user created.")
    db.close()


if __name__ == "__main__":
    create_initial_user()
