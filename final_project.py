import sqlite3
import re 
import random
import getpass
import bcrypt
import datetime
import time

DB_NAME = "bank.db"

# make the tables users and transactions
with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        fullname TEXT NOT NULL, 
        password_hash TEXT NOT NULL,
        account_number TEXT UNIQUE,
        balance REAL DEFAULT 0.0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    amount REAL,
    timestamp TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
   )
               
               """)
conn.commit()

# my validation functions

def validate_full_name(full_name):
    return full_name.replace(' ', '').isalpha() and 4 <= len(full_name.replace(' ', '')) <= 255


def validate_username(username):
    username_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_-]{3,18}[a-zA-Z0-9]$'
    
    if re.match(username_pattern, username):
        return True
    else:
        return False
    
def validate_password (password):
    regex_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"
    
    if re.fullmatch(regex_pattern, password):
        return True
    else:
        return False
    
# created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    
def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed)



def generate_account_number():
    while True:
        acct_num = str(random.randint(10000000, 99999999))
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE account_number = ?", (acct_num,))
            if not cursor.fetchone():
                return acct_num

    
def initial_depo(initial_deposit):
    try:
        if initial_deposit >= 2000:
            return True
        else: 
            return False
    except ValueError:
        print("Enter a number")
    
        
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    else:
        return False



def deposit_validation (deposit):
    try:
        value = float(deposit)
        return value > 0
    except:
        return False
    
# def balance(balance):
#     balance = deposit + initial_deposit
    
# def withdrawal_validation(withdrawal):
#     deposit = input(float("Enter deposit amount"))
#     if withdrawal <= 0 and withdrawal > balance
    


def register_user():
    # Full name
    while True:
        full_name = input("Enter your full name: ").strip()
        if not validate_full_name(full_name):
            print("Invalid full name")
            continue
        break

    # Username
    while True:
        username = input("Enter your username: ").strip()
        if not validate_username(username):
            print("Invalid username.")
            continue
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            print("Username already taken.")
            continue
        break

    # Email
    while True:
        email = input("Enter your Email: ").strip()
        if not validate_email(email):
            print("Invalid email.")
            continue
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            print("Email already taken.")
            continue
        break

    # Password
    while True:
        password = getpass.getpass("Enter a Password: ").strip()
        if not validate_password(password):
            print("Weak password.")
            continue
        password_confirm = getpass.getpass("Confirm Password: ").strip()
        if password != password_confirm:
            print("Passwords do not match.")
            continue
        break


    # Initial deposit
    while True:
        initial_deposit_str = input("Initial Deposit amount (min ₦2000): ").strip()
        try:
            initial_deposit = float(initial_deposit_str)
        except ValueError:
            print("Enter a valid number.")
            continue
        if not initial_depo(initial_deposit):
            print("Deposit must be at least ₦2000.")
            continue
        break

    # Prepare and insert user
    hashed_pw = hash_password(password)
    account_num = generate_account_number()
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute("""
        INSERT INTO users (username, email, fullname, password_hash, account_number, balance, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (username, email, full_name, hashed_pw, account_num, initial_deposit, created_at))
        conn.commit()

        user_id = cursor.lastrowid

        # Record initial deposit as a transaction
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, "deposit", initial_deposit, created_at))
        conn.commit()
        # remember to automatically enter logged-in menu hereeee
        print(f"Registration successful. Account number: {account_num}")
        time.sleep(1)
        print("Logging you in...")
        time.sleep(1)
        logged_in_menu(user_id)   
        return
    except sqlite3.IntegrityError as e:
        print("Database error:", e)
    
    

def login():
    print("\n=== Login ===")
    while True:
        username = input("Username: ").strip()
        if not validate_username(username):
            print("Invalid username format.")
            continue
            
        password = getpass.getpass("Password: ").strip()
        if not password:
            print("Password cannot be empty.")
            continue

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if not result:
                print("Invalid credentials.")
                time.sleep(1)
                return None
                
            user_id, stored_hash = result
            
            if verify_password(password, stored_hash):
                print("\nLogin successful!")
                time.sleep(1)
                return user_id
            else:
                print("Invalid credentials.")
                time.sleep(1)
                return None

def get_balance(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0.0

def deposit(user_id):
    print("\n=== Deposit ===")
    while True:
        amount_str = input("Enter amount to deposit: ").strip()
        try:
            amount = float(amount_str)
            if amount <= 0:
                print("Amount must be positive.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
            
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, timestamp)
            VALUES (?, 'deposit', ?, ?)
        """, (user_id, amount, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    
    print(f"\nSuccessfully deposited ₦{amount:,.2f}")
    time.sleep(1)

def withdraw(user_id):
    print("\n=== Withdrawal ===")
    balance = get_balance(user_id)
    
    while True:
        amount_str = input("Enter amount to withdraw: ").strip()
        try:
            amount = float(amount_str)
            if amount <= 0:
                print("Amount must be positive.")
                continue
            if amount > balance:
                print("Insufficient funds.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
            
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id))
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, timestamp)
            VALUES (?, 'withdrawal', ?, ?)
        """, (user_id, amount, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    
    print(f"\nSuccessfully withdrew ₦{amount:,.2f}")
    time.sleep(1)

def transfer(user_id):
    print("\n=== Transfer ===")
    balance = get_balance(user_id)
    
    while True:
        recipient_acct = input("Enter recipient's account number: ").strip()
        if not recipient_acct.isdigit() or len(recipient_acct) != 8:
            print("Invalid account number.")
            continue
            
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE account_number = ?", (recipient_acct,))
            recipient = cursor.fetchone()
            
            if not recipient:
                print("Recipient account not found.")
                continue
            if recipient[0] == user_id:
                print("Cannot transfer to your own account.")
                continue
            break
    
    while True:
        amount_str = input("Enter amount to transfer: ").strip()
        try:
            amount = float(amount_str)
            if amount <= 0:
                print("Amount must be positive.")
                continue
            if amount > balance:
                print("Insufficient funds.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Deduct from sender
        cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id))
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, timestamp)
            VALUES (?, 'transfer_sent', ?, ?)
        """, (user_id, amount, timestamp))
        
        # Add to recipient
        cursor.execute("UPDATE users SET balance = balance + ? WHERE account_number = ?", 
                      (amount, recipient_acct))
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, timestamp)
            VALUES (?, 'transfer_received', ?, ?)
        """, (recipient[0], amount, timestamp))
        
        conn.commit()
    
    print(f"\nSuccessfully transferred ₦{amount:,.2f}")
    time.sleep(1)

def show_transaction_history(user_id):
    print("\n=== Transaction History ===")
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT type, amount, timestamp 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY timestamp DESC
        """, (user_id,))
        transactions = cursor.fetchall()
        
        if not transactions:
            print("No transactions found.")
            return
            
        for type_, amount, timestamp in transactions:
            print(f"{timestamp} | {type_:15} | ₦{amount:,.2f}")
    
    input("\nPress Enter to continue...")

def show_account_details(user_id):
    print("\n=== Account Details ===")
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fullname, username, account_number, balance 
            FROM users 
            WHERE id = ?
        """, (user_id,))
        details = cursor.fetchone()
        
        if details:
            fullname, username, acct_num, balance = details
            print(f"Full Name: {fullname}")
            print(f"Username: {username}")
            print(f"Account Number: {acct_num}")
            print(f"Current Balance: ₦{balance:,.2f}")
    
    input("\nPress Enter to continue...")

def main_menu():
    while True:
        print("\n=== Welcome to Jamin Bank ===")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        
        choice = input("Choose an option: ").strip()
        
        if choice == "1":
            register_user()
        elif choice == "2":
            user_id = login()
            if user_id:
                logged_in_menu(user_id)
        elif choice == "3":
            print("\nThank you for banking with Jamin Bank!")
            break
        else:
            print("Invalid choice.")

def logged_in_menu(user_id):
    while True:
        print("\n=== Jamin Bank Main Menu ===")
        print("1. Check Balance")
        print("2. Deposit")
        print("3. Withdraw")
        print("4. Transfer")
        print("5. Transaction History")
        print("6. Account Details")
        print("7. Logout")
        
        choice = input("Choose an option: ").strip()
        
        if choice == "1":
            balance = get_balance(user_id)
            print(f"\nYour current balance: ₦{balance:,.2f}")
            time.sleep(1)
        elif choice == "2":
            deposit(user_id)
        elif choice == "3":
            withdraw(user_id)
        elif choice == "4":
            transfer(user_id)
        elif choice == "5":
            show_transaction_history(user_id)
        elif choice == "6":
            show_account_details(user_id)
        elif choice == "7":
            print("\nLogging out...")
            time.sleep(1)
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main_menu()











