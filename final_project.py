import sqlite3
import re 
import random
import getpass
import bcrypt
import datetime


DB_NAME = "bank.db"

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
            INSERT INTO users (username, email, fullname, password_hash, account_number, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, email, full_name, hashed_pw, account_num, created_at))
        conn.commit()
        user_id = cursor.lastrowid

        # Record initial deposit as a transaction
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, "deposit", initial_deposit, created_at))
        conn.commit()

        print(f"Registration successful. Account number: {account_num}")
    except sqlite3.IntegrityError as e:
        print("Database error:", e)
        





    


    

