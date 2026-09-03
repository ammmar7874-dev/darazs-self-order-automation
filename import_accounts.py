import sys
from sqlmodel import Session, select
from backend.database import engine, Account, init_db

def add_account(email: str, password: str, phone: str = None, full_name: str = "Buyer"):
    init_db()
    with Session(engine) as session:
        existing = session.exec(select(Account).where(Account.email == email)).first()
        if existing:
            existing.password = password
            if phone:
                existing.phone = phone
            existing.status = "active"
            session.add(existing)
            session.commit()
            print(f"[SUCCESS] Updated account: {email} (Phone: {phone})")
        else:
            acc = Account(
                email=email,
                password=password,
                phone=phone,
                full_name=full_name,
                status="active"
            )
            session.add(acc)
            session.commit()
            print(f"[SUCCESS] Added new account: {email} (Phone: {phone})")

def list_accounts():
    init_db()
    with Session(engine) as session:
        accs = session.exec(select(Account)).all()
        print(f"\nTotal Registered Daraz Accounts: {len(accs)}")
        print("-" * 65)
        for a in accs:
            print(f"ID: {a.id} | Email/Phone: {a.email} ({a.phone or 'No Phone'}) | Status: {a.status}")
        print("-" * 65)

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        pwd = sys.argv[2]
        phone = sys.argv[3] if len(sys.argv) > 3 else None
        add_account(email, pwd, phone)
    else:
        list_accounts()
        print("\nUsage to add account:")
        print("  python import_accounts.py <email_or_username> <password> [phone_number]")
