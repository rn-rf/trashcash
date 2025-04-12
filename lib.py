import sqlite3, uuid, json, bcrypt
from datetime import datetime
from typing import Optional


def validate_datetime(date_str: str, time_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False
def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'individual'
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
            items_json TEXT NOT NULL, 
            scheduled_date_start TEXT NOT NULL,
            scheduled_date_end TEXT NOT NULL,
            scheduled_time_start TEXT NOT NULL,
            scheduled_time_end TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (address_id) REFERENCES addresses(id)
        )
    ''')
    #items_json should store items divided by , no need to use dict example "steel, iron" 

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drive (
            id TEXT PRIMARY KEY,
            pick_up_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            is_complete INTEGER DEFAULT 0,
            out_for_pick_up INTEGER DEFAULT 0,
            get_pick_up INTEGER DEFAULT 0,
            out_for_delivery INTEGER DEFAULT 0,
            delivered INTEGER DEFAULT 0,
            FOREIGN KEY (pick_up_id) REFERENCES pick_up(id),
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')

    conn.commit()
    conn.close()
def create_user(username: str, password: str, role: str = "Individual") -> bool:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
            (username, hash_password(password), role)
        )
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
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()
def validate_login(username: str, password: str) -> str:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT password, role FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result and bcrypt.checkpw(password.encode(), result[0].encode()):
        return result[1]
    return "invalid"
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
def create_drive(pick_up_id: int, username: str) -> bool:
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM pick_up WHERE id = ?", (pick_up_id,))
            if not cursor.fetchone():
                return False 
            
            drive_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO drive (id, pick_up_id, username)
                VALUES (?, ?, ?)
            ''', (drive_id, pick_up_id, username))
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Error creating drive: {e}")
            return False
def update_drive_status(drive_id: str, field: str, value: bool) -> bool:
    valid_fields = {'is_complete', 'out_for_pick_up', 'get_pick_up', 
                   'out_for_delivery', 'delivered'}
    if field not in valid_fields:
        raise ValueError("Invalid field name for drive status")
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute(f'''
            UPDATE drive
            SET {field} = ?
            WHERE id = ?
        ''', (int(value), drive_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
def get_drive(drive_id: str) -> dict | None:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, pick_up_id, username, is_complete, 
               out_for_pick_up, get_pick_up, out_for_delivery, delivered
        FROM drive
        WHERE id = ?
    ''', (drive_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "pick_up_id": row[1],
            "username": row[2],
            "is_complete": bool(row[3]),
            "out_for_pick_up": bool(row[4]),
            "get_pick_up": bool(row[5]),
            "out_for_delivery": bool(row[6]),
            "delivered": bool(row[7])
        }
    return None
def get_drives_by_username(username: str) -> list[dict]:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, pick_up_id, is_complete, out_for_pick_up, 
               get_pick_up, out_for_delivery, delivered
        FROM drive
        WHERE username = ?
    ''', (username,))
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "id": row[0],
        "pick_up_id": row[1],
        "is_complete": bool(row[2]),
        "out_for_pick_up": bool(row[3]),
        "get_pick_up": bool(row[4]),
        "out_for_delivery": bool(row[5]),
        "delivered": bool(row[6])
    } for row in rows]
def get_all_drives() -> list[dict]:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, pick_up_id, username, is_complete, 
               out_for_pick_up, get_pick_up, out_for_delivery, delivered
        FROM drive
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "id": row[0],
        "pick_up_id": row[1],
        "username": row[2],
        "is_complete": bool(row[3]),
        "out_for_pick_up": bool(row[4]),
        "get_pick_up": bool(row[5]),
        "out_for_delivery": bool(row[6]),
        "delivered": bool(row[7])
    } for row in rows]
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
        print("17. Create Drive")
        print("18. Update Drive Status")
        print("19. Get Drive Info")
        print("20. Get All Drives")
        print("21. Get Drives by Username")
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
            print(get_all_items())

        elif choice == "10":
            name = input("Item name: ")
            new_price = float(input("New price: "))
            print("Price Updated:", update_price(name, new_price))

        elif choice == "11":  
            address_id = int(input("Address ID: "))
            items = []
            while True:
                item_name = input("Item name (or 'done' to finish): ").strip()
                if item_name.lower() == 'done':
                    break
                if not get_price(item_name):  
                    print(f"Error: Item '{item_name}' doesn't exist!")
                    continue
                # weight = float(input(f"Weight for {item_name} (kg): "))
                items.append(item_name)
            
            if items:
                date_start = input("Start Date (YYYY-MM-DD): ")
                date_end = input("End Date (YYYY-MM-DD): ")
                time_start = input("Start Time (HH:MM): ")
                time_end = input("End Time (HH:MM): ")
                
                pickup_id = create_pickup(
                    address_id, items,
                    date_start, date_end,
                    time_start, time_end
                )
                print(f"Pickup created with ID: {pickup_id}" if pickup_id else "Failed!")

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

        elif choice == "99" :
            print(get_all_pick_up())

        elif choice == "17":
            pick_up_id = int(input("Pickup ID: "))
            username = input("Username: ")
            print("Drive Created:", create_drive(pick_up_id, username))

        elif choice == "18":
            drive_id = input("Drive ID: ")
            print("Available fields: is_complete, out_for_pick_up, get_pick_up, out_for_delivery, delivered")
            field = input("Field to update: ")
            value = input("Set to (1/0 or True/False): ").lower() in ['1', 'true', 't']
            print("Status Updated:", update_drive_status(drive_id, field, value))

        elif choice == "19":
            drive_id = input("Drive ID: ")
            drive = get_drive(drive_id)
            print(drive if drive else "Drive not found")

        elif choice == "20":
            drives = get_all_drives()
            for drive in drives:
                print(drive)

        elif choice == "21":
            username = input("Username: ")
            drives = get_drives_by_username(username)
            for drive in drives:
                print(drive)

        elif choice == "0":
            print("Exiting.")
            break

        else:
            print("Invalid choice. Try again.")
def test_all_functions():
    """Test all database functions with predefined values"""
    init_db()
    
    test_user1 = "test_user1"
    test_password1 = "password123"
    test_user2 = "test_user2"
    test_password2 = "secure!456"
    
    test_address = {
        "username": test_user1,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "123-456-7890",
        "street": "123 Main St",
        "role": "Individual",
        "pincode": "12345"
    }
    
    test_item1 = {"name": "TestItem1", "price": 10.5, "volume": 1.2}
    test_item2 = {"name": "TestItem2", "price": 15.0, "volume": 2.0}
    
    def print_result(test_name, success):
        color = "\033[92m" if success else "\033[91m"
        symbol = "✓" if success else "✗"
        print(f"{color}{symbol} Test: {test_name}\033[0m")

    try:
        print("\n=== Testing User Functions ===")
        print_result("Create User 1", create_user(test_user1, test_password1))
        print_result("Create Duplicate User", not create_user(test_user1, "anypass"))  # Should fail
        
        print_result("Valid Login", validate_login(test_user1, test_password1) != "invalid")
        print_result("Invalid Login", validate_login("non_existent", "wrongpass") == "invalid")
        
        print("\n=== Testing Address Functions ===")
        print_result("Create Valid Address", create_address(**test_address))
        print_result("Create Invalid User Address", not create_address("non_existent", "name", "a@b.c", "123", "street", "role", "pincode"))
        
        print("\n=== Testing Item Functions ===")
        print_result("Create Item 1", create_item(test_item1["name"], test_item1["price"], test_item1["volume"]))
        print_result("Create Duplicate Item", not create_item(test_item1["name"], 12, 1.5))  # Should fail
        
        print("\n=== Testing Pickup Functions ===")
        valid_items = [{"name": test_item1["name"], "weight": 5.0}]
        invalid_items = [{"name": "NonExistentItem", "weight": 1.0}]
        
        pickup_id = create_pickup(
            address_id=1,
            items=valid_items,
            date_start="2023-01-01",
            date_end="2023-01-01",
            time_start="09:00",
            time_end="12:00"
        )
        print_result("Create Valid Pickup", pickup_id is not None)
        
        print_result("Create Invalid Pickup", create_pickup(1, invalid_items, "2023-01-01", "2023-01-01", "09:00", "12:00") is None)
        
        print("\n=== Testing Drive Functions ===")
        print_result("Create Valid Drive", create_drive(pickup_id, test_user1))
        print_result("Create Invalid Drive", not create_drive(9999, "non_existent_user"))  # Invalid pickup/user
        
        print("\n=== Testing Update Functions ===")
        print_result("Update Password", update_password(test_user1, "new_password"))
        print_result("Verify New Password", validate_login(test_user1, "new_password") != "invalid")
        
        print("\n=== Testing Deletion Functions ===")
        print_result("Delete Valid Address", delete_address(1))
        print_result("Delete Invalid Address", not delete_address(999))
        
        print_result("Delete Valid Item", delete_item(test_item1["name"]))
        print_result("Delete Invalid Item", not delete_item("NonExistentItem"))
        
    finally:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username LIKE 'test_%'")
        cursor.execute("DELETE FROM items WHERE name LIKE 'TestItem%'")
        conn.commit()
        conn.close()
def validate_items_exist(item_names: list[str]) -> bool:
    """Check if all items exist in the database"""
    if not item_names:
        return False
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        placeholders = ', '.join(['?'] * len(item_names))
        query = f"SELECT COUNT(*) FROM items WHERE name IN ({placeholders})"
        cursor.execute(query, item_names)
        count = cursor.fetchone()[0]
        return count == len(item_names)

def get_pick_ups(username: str) -> list[dict]:
    """
    Retrieve all pickups associated with a given username by checking:
    1. Addresses linked to the username
    2. Pickups linked to those addresses
    
    Args:
        username: The username to search for
    
    Returns:
        List of pickup dictionaries (empty list if no matches found)
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id FROM addresses 
            WHERE username = ?
        ''', (username,))
        address_ids = [row[0] for row in cursor.fetchall()]
        
        if not address_ids:
            return []
        
        cursor.execute('''
            SELECT 
                p.id,
                p.address_id,
                p.items_json,
                p.scheduled_date_start,
                p.scheduled_date_end,
                p.scheduled_time_start,
                p.scheduled_time_end,
                p.status,
                p.created_at
            FROM pick_up p
            WHERE p.address_id IN ({})
            ORDER BY p.created_at DESC
        '''.format(','.join(['?']*len(address_ids))), address_ids)
        
        pickups = []
        for row in cursor.fetchall():
            pickups.append({
                "id": row[0],
                "address_id": row[1],
                "items": [item.strip() for item in row[2].split(',')] if row[2] else [],
                "scheduled_date_start": row[3],
                "scheduled_date_end": row[4],
                "scheduled_time_start": row[5],
                "scheduled_time_end": row[6],
                "status": row[7],
                "created_at": row[8]
            })
            
        return pickups
        
    finally:
        conn.close()

def create_pickup(
    address_id: int,
    items: list[str],
    date_start: str,
    date_end: str,
    time_start: str,
    time_end: str,
    status: str = 'scheduled'
) -> Optional[int]:
    if not validate_items_exist(items):
        print("Some items do not exist.")
        return None

    items_str = ", ".join(items)

    try:
        datetime.strptime(date_start, '%Y-%m-%d')
        datetime.strptime(date_end, '%Y-%m-%d')
        datetime.strptime(time_start, '%H:%M')
        datetime.strptime(time_end, '%H:%M')
        
        with sqlite3.connect('users.db') as conn:
            conn.execute('PRAGMA foreign_keys = ON')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO pick_up (
                    address_id,
                    items_json,
                    scheduled_date_start,
                    scheduled_date_end,
                    scheduled_time_start,
                    scheduled_time_end,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                address_id,
                items_str,
                date_start,
                date_end,
                time_start,
                time_end,
                status
            ))
            
            conn.commit()
            return cursor.lastrowid
            
    except ValueError as e:
        print(f"Invalid date/time format: {e}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    
    return None

def get_pickup_items(pickup_id: int) -> list[str]:
    """Retrieve items from a pickup as a list of strings"""
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT items_json FROM pick_up WHERE id = ?
        ''', (pickup_id,))
        result = cursor.fetchone()
        if result and result[0]:
            return [item.strip() for item in result[0].split(',')]
        return []

def get_user_role(username: str) -> Optional[str]:
    """
    Retrieve the role of a user from the database
    
    Args:
        username: The username to look up
        
    Returns:
        The role as a string if user exists, None otherwise
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT role FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def get_all_pick_up() -> list[dict]:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, address_id, items_json, 
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
            "items": [item.strip() for item in row[2].split(',')] if row[2] else [],
            "scheduled_date_start": row[3],
            "scheduled_date_end": row[4],
            "scheduled_time_start": row[5],
            "scheduled_time_end": row[6],
            "status": row[7],
            "created_at": row[8]
        }
        for row in rows
    ]
init_db()