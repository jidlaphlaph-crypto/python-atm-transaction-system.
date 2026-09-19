import sqlite3
import time
import sys
from getpass import getpass

# Initialize database configuration
DB_FILE = "atm_bank_system.db"

def init_db():
    """Establishes connection and creates the necessary database schema."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            account_number INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            pin TEXT NOT NULL,
            balance REAL DEFAULT 0.0
        )
    ''')
    
    # Create Transactions log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_number INTEGER,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (account_number) REFERENCES users (account_number)
        )
    ''')
    conn.commit()
    conn.close()

def create_account():
    """Registers a new bank account user securely into the system database."""
    print("\n--- OPEN NEW BANK ACCOUNT ---")
    username = input("Enter a unique username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return

    pin = input("Create a 4-digit security PIN: ").strip()
    if len(pin) != 4 or not pin.isdigit():
        print("Invalid PIN format. Must be exactly 4 digits.")
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, pin, balance) VALUES (?, ?, 0.0)", (username, pin))
        conn.commit()
        
        # Fetch the newly assigned account number
        cursor.execute("SELECT account_number FROM users WHERE username = ?", (username,))
        acc_num = cursor.fetchone()[0]
        print(f"\nAccount created successfully!")
        print(f"Your Account Number is: {acc_num} (Remember this to log in)")
    except sqlite3.IntegrityError:
        print("Error: That username is already taken. Please choose another.")
    finally:
        conn.close()

def login():
    """Authenticates users against stored database credentials."""
    print("\n--- ATM SYSTEM LOGIN ---")
    acc_num_input = input("Enter your Account Number: ").strip()
    # Mask input if supported, fallback to regular input
    try:
        pin_input = getpass("Enter your 4-digit PIN: ").strip()
    except Exception:
        pin_input = input("Enter your 4-digit PIN: ").strip()

    if not acc_num_input.isdigit():
        print("Account number must be numeric.")
        return None

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT account_number, username, balance FROM users WHERE account_number = ? AND pin = ?", 
                   (int(acc_num_input), pin_input))
    user = cursor.fetchone()
    conn.close()

    if user:
        print(f"\nWelcome back, {user[1]}!")
        return {"account_number": user[0], "username": user[1]}
    else:
        print("Invalid Account Number or PIN combination.")
        return None

def log_transaction(account_number, tx_type, amount):
    """Inserts an immutable log record into the transaction database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO transactions (account_number, type, amount, timestamp) VALUES (?, ?, ?, ?)",
                   (account_number, tx_type, amount, current_time))
    conn.commit()
    conn.close()

def check_balance(account_number):
    """Retrieves the latest account balance directly from the database query."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE account_number = ?", (account_number,))
    balance = cursor.fetchone()[0]
    conn.close()
    print(f"\nYour current available balance is: KSH {balance:,.2f}")

def deposit_cash(account_number):
    """Updates account balance and appends a positive cash flow transaction record."""
    try:
        amount = float(input("\nEnter amount to deposit: "))
        if amount <= 0:
            print("Deposit amount must be positive.")
            return
    except ValueError:
        print("Invalid monetary input.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE account_number = ?", (amount, account_number))
    conn.commit()
    conn.close()

    log_transaction(account_number, "DEPOSIT", amount)
    print(f"Successfully deposited KSH {amount:,.2f}")

def withdraw_cash(account_number):
    """Verifies funds, updates database values, and logs withdrawals safely."""
    try:
        amount = float(input("\nEnter amount to withdraw: "))
        if amount <= 0:
            print("Withdrawal amount must be positive.")
            return
    except ValueError:
        print("Invalid monetary input.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE account_number = ?", (account_number,))
    current_balance = cursor.fetchone()[0]

    if amount > current_balance:
        print("Transaction Declined: Insufficient available funds.")
        conn.close()
        return

    cursor.execute("UPDATE users SET balance = balance - ? WHERE account_number = ?", (amount, account_number))
    conn.commit()
    conn.close()

    log_transaction(account_number, "WITHDRAWAL", amount)
    print(f"Please collect your cash. Successfully withdrew KSH {amount:,.2f}")

def view_statement(account_number):
    """Generates an itemized historical breakdown list of transaction records."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT type, amount, timestamp FROM transactions WHERE account_number = ? ORDER BY transaction_id DESC LIMIT 10", 
                   (account_number,))
    rows = cursor.fetchall()
    conn.close()

    print("\n--- RECENT MINI-STATEMENT (Last 10 Tx) ---")
    if not rows:
        print("No transactional logs found for this account.")
        return

    for row in rows:
        print(f"[{row[2]}] {row[0]:<12} | KSH {row[1]:,.2f}")

def atm_dashboard(user_session):
    """Main operations selection dashboard for an authenticated user session."""
    while True:
        print(f"\n=============================")
        print(f"     APEX DIGITAL ATM        ")
        print(f"=============================")
        print("1. Check Account Balance")
        print("2. Deposit Funds")
        print("3. Withdraw Cash")
        print("4. View Mini-Statement")
        print("5. Log Out Session")
        
        choice = input("\nSelect an operation (1-5): ").strip()
        if choice == "1":
            check_balance(user_session["account_number"])
        elif choice == "2":
            deposit_cash(user_session["account_number"])
        elif choice == "3":
            withdraw_cash(user_session["account_number"])
        elif choice == "4":
            view_statement(user_session["account_number"])
        elif choice == "5":
            print(f"Session safely closed. Thank you for banking with us, {user_session['username']}!")
            break
        else:
            print("Invalid selection. Choose an option from 1 to 5.")

def main():
    """Main terminal loop orchestrating user lifecycle flow initialization."""
    init_db()
    while True:
        print("\n=====================================")
        print("  WELCOME TO APEX BANKING PORTAL   ")
        print("=====================================")
        print("1. Log In Existing Account")
        print("2. Open New Bank Account")
        print("3. Shut Down Terminal")
        
        portal_choice = input("\nSelect an action (1-3): ").strip()
        if portal_choice == "1":
            session = login()
            if session:
                atm_dashboard(session)
        elif portal_choice == "2":
            create_account()
        elif portal_choice == "3":
            print("Shutting down core ATM application framework safely... Goodbye.")
            sys.exit()
        else:
            print("Invalid configuration choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
