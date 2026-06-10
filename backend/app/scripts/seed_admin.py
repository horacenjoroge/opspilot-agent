import argparse

from app.db.session import SessionLocal, init_db
from app.services.auth import AuthService


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed or reset a local OpsPilot admin user.")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--name", default="OpsPilot Admin", help="Admin display name")
    args = parser.parse_args()

    init_db()
    session = SessionLocal()
    try:
        user = AuthService(session).seed_dev_admin(email=args.email, password=args.password, name=args.name)
    finally:
        session.close()

    print(f"Seeded admin user {user.email} with role {user.role.value}.")


if __name__ == "__main__":
    main()
