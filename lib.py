import sqlite3
import hashlib

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            name TEXT,
            email TEXT,
            phone_number TEXT,
            street TEXT,
            role TEXT,
            pincode TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            name TEXT PRIMARY KEY,
            price REAL NOT NULL,
            volume_per_kg REAL NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pick_up (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            weight REAL NOT NULL,
            scheduled_date_start TEXT NOT NULL,
            scheduled_date_end TEXT NOT NULL,
            scheduled_time_start TEXT NOT NULL,
            scheduled_time_end TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (address_id) REFERENCES addresses(id),
            FOREIGN KEY (item) REFERENCES items(name)
        );
    ''')

    conn.commit()
    conn.close()
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
def create_user(username: str, password: str) -> bool:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                       (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
def create_address(username: str, name: str, email: str,
                   phone: str, street: str,
                   role: str, pincode: str) -> bool:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute('''
        INSERT INTO addresses (username, name, email, phone_number, street, role, pincode)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, name, email, phone, street, role, pincode))

    conn.commit()
    conn.close()
    return True
def validate_login(username: str, password: str) -> bool:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0] == hash_password(password):
        return True
    return False
def get_all_users() -> list[tuple[str, str]]:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return users  
def get_addresses(username: str) -> list[dict]:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, email, phone_number, street, role, pincode
        FROM addresses
        WHERE username = ?
    ''', (username,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "phone_number": row[3],
            "street": row[4],
            "role": row[5],
            "pincode": row[6],
        }
        for row in rows
    ]
def delete_address(address_id: int) -> bool:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM addresses WHERE id = ?", (address_id,))
    changes = cursor.rowcount 

    conn.commit()
    conn.close()

    return changes > 0
def update_password(username: str, new_password: str) -> bool:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if not cursor.fetchone():
        conn.close()
        return False  

    hashed_password = hash_password(new_password)
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))
    conn.commit()
    conn.close()
    return True
def create_item(name: str, price: float, volume_per_kg: float) -> bool:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO items (name, price, volume_per_kg)
            VALUES (?, ?, ?)
        ''', (name, price, volume_per_kg))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  
    finally:
        conn.close()
def delete_item(item: str) -> bool:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM items WHERE name = ?', (item,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()

    return deleted
def get_price(item: str) -> float | None:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('SELECT price FROM items WHERE name = ?', (item,))
    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None
def update_price(item: str, new_price: float) -> bool:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('UPDATE items SET price = ? WHERE name = ?', (new_price, item))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()

    return updated
def create_pickup(address_id: int, item: str, weight: float,
                  date_start: str, date_end: str,
                  time_start: str, time_end: str) -> int | None:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO pick_up (
                address_id, item, weight,
                scheduled_date_start, scheduled_date_end,
                scheduled_time_start, scheduled_time_end
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (address_id, item, weight, date_start, date_end, time_start, time_end))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print("DB Error:", e)
        return None
    finally:
        conn.close()
def update_pickup_schedule(pickup_id: int,
                           new_date_start: str, new_date_end: str,
                           new_time_start: str, new_time_end: str) -> bool:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE pick_up
            SET scheduled_date_start = ?, scheduled_date_end = ?,
                scheduled_time_start = ?, scheduled_time_end = ?
            WHERE id = ?
        ''', (new_date_start, new_date_end, new_time_start, new_time_end, pickup_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
def update_pickup(pickup_id: int, address_id: int, item: str,
                  weight: float, date_start: str,
                  date_end: str, time_start: str,
                  time_end: str, status: str) -> bool:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE pick_up
            SET address_id = ?, item = ?, weight = ?,
                scheduled_date_start = ?, scheduled_date_end = ?,
                scheduled_time_start = ?, scheduled_time_end = ?,
                status = ?
            WHERE id = ?
        ''', (address_id, item, weight, date_start, date_end,
              time_start, time_end, status, pickup_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
def update_pickup_status(pickup_id: int, new_status: str) -> bool:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE pick_up
            SET status = ?
            WHERE id = ?
        ''', (new_status, pickup_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
def main():
    while True:
        print("\nChoose an option:")
        print("1. Create User")
        print("2. Validate Login")
        print("3. Update Password")
        print("4. Create Address")
        print("5. Show All Addresses for User")
        print("6. Delete Address")
        print("7. Create Item")
        print("8. Delete Item")
        print("9. Get Item Price")
        print("10. Update Item Price")
        print("11. Create Pickup")
        print("12. Update Pickup")
        print("13. Update Pickup Schedule")
        print("14. Update Pickup Status")
        print("15. Show All Users")
        print("16. Get Pickups")
        print("0. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            username = input("Username: ")
            password = input("Password: ")
            print("Created:", create_user(username, password))

        elif choice == "2":
            username = input("Username: ")
            password = input("Password: ")
            print("Valid Login:", validate_login(username, password))

        elif choice == "3":
            username = input("Username: ")
            new_pass = input("New Password: ")
            print("Password Updated:", update_password(username, new_pass))

        elif choice == "4":
            username = input("Username: ")
            name = input("Name: ")
            email = input("Email: ")
            phone = input("Phone: ")
            street = input("Street: ")
            role = input("Role: ")
            pincode = input("Pincode: ")
            print("Address Created:", create_address(username, name, email, phone, street, role, pincode))

        elif choice == "5":
            username = input("Username: ")
            addresses = get_addresses(username)
            for addr in addresses:
                print(addr)

        elif choice == "6":
            addr_id = int(input("Address ID to delete: "))
            print("Deleted:", delete_address(addr_id))

        elif choice == "7":
            name = input("Item name: ")
            price = float(input("Price: "))
            volume = float(input("Volume per kg: "))
            print("Item Created:", create_item(name, price, volume))

        elif choice == "8":
            name = input("Item name to delete: ")
            print("Item Deleted:", delete_item(name))

        elif choice == "9":
            name = input("Item name: ")
            print("Price:", get_price(name))

        elif choice == "10":
            name = input("Item name: ")
            new_price = float(input("New price: "))
            print("Price Updated:", update_price(name, new_price))

        elif choice == "11":
            addr_id = int(input("Address ID: "))
            item = input("Item: ")
            weight = float(input("Weight: "))
            date_start = input("Date Start (YYYY-MM-DD): ")
            date_end = input("Date End (YYYY-MM-DD): ")
            time_start = input("Time Start (HH:MM): ")
            time_end = input("Time End (HH:MM): ")
            print("Pickup ID:", create_pickup(addr_id, item, weight, date_start, date_end, time_start, time_end))

        elif choice == "12":
            pickup_id = int(input("Pickup ID: "))
            addr_id = int(input("Address ID: "))
            item = input("Item: ")
            weight = float(input("Weight: "))
            date_start = input("Date Start (YYYY-MM-DD): ")
            date_end = input("Date End (YYYY-MM-DD): ")
            time_start = input("Time Start (HH:MM): ")
            time_end = input("Time End (HH:MM): ")
            status = input("Status: ")
            print("Pickup Updated:", update_pickup(pickup_id, addr_id, item, weight, date_start, date_end, time_start, time_end, status))

        elif choice == "13":
            pickup_id = int(input("Pickup ID: "))
            date_start = input("New Date Start (YYYY-MM-DD): ")
            date_end = input("New Date End (YYYY-MM-DD): ")
            time_start = input("New Time Start (HH:MM): ")
            time_end = input("New Time End (HH:MM): ")
            print("Schedule Updated:", update_pickup_schedule(pickup_id, date_start, date_end, time_start, time_end))

        elif choice == "14":
            pickup_id = int(input("Pickup ID: "))
            new_status = input("New Status: ")
            print("Status Updated:", update_pickup_status(pickup_id, new_status))

        elif choice == "15":
            users = get_all_users()
            for user in users:
                print(user)

        elif choice == "16":
            username = input("Username: ")
            pickups = get_pick_ups(username)
            for pickup in pickups:
                print(pickup)

        elif choice == "20" :
            print(get_all_pick_up())

        elif choice == "0":
            print("Exiting.")
            break

        else:
            print("Invalid choice. Try again.")
def get_all_items() -> list[dict]:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, volume_per_kg FROM items")
    rows = cursor.fetchall()
    conn.close()

    return [
        {"name": row[0], "price": row[1], "volume_per_kg": row[2]}
        for row in rows
    ]
def get_all_pick_up() -> list[dict]:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, address_id, item, weight,
               scheduled_date_start, scheduled_date_end,
               scheduled_time_start, scheduled_time_end,
               status, created_at
        FROM pick_up
    ''')
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "address_id": row[1],
            "item": row[2],
            "weight": row[3],
            "scheduled_date_start": row[4],
            "scheduled_date_end": row[5],
            "scheduled_time_start": row[6],
            "scheduled_time_end": row[7],
            "status": row[8],
            "created_at": row[9]
        }
        for row in rows
    ]
def get_all_address() -> list[dict]:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, name, email, phone_number, street, role, pincode
        FROM addresses
    ''')
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "username": row[1],
            "name": row[2],
            "email": row[3],
            "phone_number": row[4],
            "street": row[5],
            "role": row[6],
            "pincode": row[7]
        }
        for row in rows
    ]
def get_address(address_id: int) -> dict | None:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, name, email, phone_number, street, role, pincode
        FROM addresses
        WHERE id = ?
    ''', (address_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "username": row[1],
            "name": row[2],
            "email": row[3],
            "phone_number": row[4],
            "street": row[5],
            "role": row[6],
            "pincode": row[7]
        }
    return None
def get_pick_ups(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute('''
        SELECT 
            id,
            address_id,
            item,
            weight,
            scheduled_date_start,
            scheduled_date_end,
            scheduled_time_start,
            scheduled_time_end,
            status,
            created_at
        FROM pick_up
        WHERE address_id IN (
            SELECT id FROM addresses WHERE username = ?
        )
    ''', (username,))

    rows = c.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "address_id": row[1],
            "item": row[2],
            "weight": row[3],
            "scheduled_date_start": row[4],
            "scheduled_date_end": row[5],
            "scheduled_time_start": row[6],
            "scheduled_time_end": row[7],
            "status": row[8],
            "created_at": row[9],
        }
        for row in rows
    ]
init_db()