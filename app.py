from flask import Flask, render_template, request, jsonify, session
from flasgger import Swagger
import lib

app = Flask(__name__)
Swagger(app)
app.secret_key = "6a94b15e9b77f948e3f82f7fa4c5c58a8c01acb510298cc0cc85e798ba2575d0"

@app.route("/")
def home():
    return render_template("index.html", title="Home", username="RN")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup", methods=["GET"])
def signup():
    return render_template("signup.html")

@app.route("/save", methods=["POST"])
def save():
    """
    User signup
    ---    
    tags:
      - Authentication
    parameters:
      - name: username
        in: body
        type: string
        required: true
      - name: password
        in: body
        type: string
        required: true
    responses:
      200:
        description: Signup successful
      400:
        description: Missing username or password
    """
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Missing username or password"
            }), 400

        print(f"Received signup - username: {username}, password: {password}")

        flag = lib.create_user(username, password)
        if not flag:
            return jsonify({
                "success": False,
                "message": "Username already exists"
            }), 400

        return jsonify({
            "success": True,
            "message": "Signup successful!",
            "data": {"username": username}
        }), 200

    except Exception as e:
        print("Error in /save:", e)
        return jsonify({
            "success": False,
            "message": "Server error",
            "error": str(e)
        }), 500

@app.route("/auth", methods=["POST"])
def auth():
    """
    User Login
    ---
    tags:
      - Authentication
    parameters:
      - name: username
        in: body
        type: string
        required: true
        description: The username of the user
      - name: password
        in: body
        type: string
        required: true
        description: The password of the user
    responses:
      200:
        description: Login successful
      400:
        description: Missing username or password
      401:
        description: Invalid credentials
      500:
        description: Server error
    """
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            return jsonify({"message": "Missing username or password"}), 400

        print(f"Received login - username: {username}, password: {password}")

        # Validate credentials
        if not lib.validate_login(username, password):
            return jsonify({"message": "Invalid Credential!"}), 401

        # Store username in session
        session["username"] = username
        print(session["username"])
        return jsonify({"message": "Login successful!"})
    except Exception as e:
        print("Error in /auth:", e)
        return jsonify({"message": "Server error", "error": str(e)}), 500

@app.route("/dashboard")
def dashboard():
    """
    Get User Dashboard Data
    ---
    tags:
      - Dashboard
    responses:
      200:
        description: Dashboard data retrieved successfully
        examples:
          application/json:
            user: rnrkrathod
            address: [...]
            pickup: [...]
      401:
        description: Unauthorized
    """
    if "username" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    username = session["username"]
    address = lib.get_addresses(username)
    pickup = lib.get_pick_ups(username)

    return jsonify({
        "user": username,
        "address": address,
        "pickup": pickup
    })

@app.route("/create_address", methods=["POST"])
def create_address():
    """
    Create a new address for a user
    ---
    parameters:
      - name: name
        in: query
        type: string
        required: true
        description: Full name of the user
      - name: email
        in: query
        type: string
        required: true
        description: Email address of the user
      - name: phone
        in: query
        type: string
        required: true
        description: Phone number
      - name: street
        in: query
        type: string
        required: true
        description: Street address
      - name: role
        in: query
        type: string
        required: true
        description: Role of the user
      - name: pincode
        in: query
        type: string
        required: true
        description: Pincode
    responses:
      201:
        description: Address created successfully
        examples:
          application/json:
            status: success
            message: Address created successfully
      400:
        description: Missing parameters
      404:
        description: User not found
    """
    if "username" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    data = request.get_json()
    username = session["username"]
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    street = data.get('street')
    role = data.get('role')
    pincode = data.get('pincode')
    if not all([name, email, phone, street, role, pincode]):
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    success = lib.create_address(username, name, email, phone, street, role, pincode)

    if success:
        return jsonify({"status": "success", "message": "Address created successfully"}), 201
    else:
        return jsonify({"status": "error", "message": "User not found"}), 404

@app.route('/create_pickup', methods=['POST'])
def create_pickup():
    """
    Create a new pickup entry
    ---
    parameters:
      - name: address_id
        in: body
        type: integer
        required: true
        description: ID of the address associated with the pickup
      - name: item
        in: body
        type: string
        required: true
        description: Name of the item to be picked up
      - name: weight
        in: body
        type: number
        format: float
        required: true
        description: Weight of the item in kg
      - name: date_start
        in: body
        type: string
        format: date
        required: true
        description: Start date for the pickup window (YYYY-MM-DD)
      - name: date_end
        in: body
        type: string
        format: date
        required: true
        description: End date for the pickup window (YYYY-MM-DD)
      - name: time_start
        in: body
        type: string
        required: true
        description: Start time for the pickup window (HH:MM)
      - name: time_end
        in: body
        type: string
        required: true
        description: End time for the pickup window (HH:MM)
    responses:
      201:
        description: Pickup created successfully
        examples:
          application/json:
            status: success
            pickup_id: 7
      400:
        description: Missing or invalid parameters
      401:
        description: Unauthorized access
      403:
        description: Address does not belong to the user
      500:
        description: Failed to create pickup due to server error
    """
    if "username" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    try:
        address_id = int(data.get('address_id'))
        item = data.get('item')
        weight = float(data.get('weight'))
        date_start = data.get('date_start')
        date_end = data.get('date_end')
        time_start = data.get('time_start')
        time_end = data.get('time_end')

        if not all([address_id, item, weight, date_start, date_end, time_start, time_end]):
            raise ValueError("Missing parameters")
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Missing or invalid parameters"}), 400

    user_addresses = lib.get_addresses(session["username"])
    valid_address_ids = [addr['id'] for addr in user_addresses]
    if address_id not in valid_address_ids:
        return jsonify({"status": "error", "message": "Address does not belong to the user"}), 403

    pickup_id = lib.create_pickup(address_id, item, weight, date_start, date_end, time_start, time_end)

    if pickup_id is not None:
        return jsonify({"status": "success", "pickup_id": pickup_id}), 201
    else:
        return jsonify({"status": "error", "message": "Failed to create pickup"}), 500

@app.route('/get_addresses', methods=['GET'])
def get_addresses():
    """
    Get all addresses for the logged-in user
    ---
    responses:
      200:
        description: List of addresses
        examples:
          application/json:
            - id: 1
              username: johndoe
              name: John Doe
              email: john@example.com
              phone_number: "1234567890"
              street: "123 Main St"
              role: "donor"
              pincode: "123456"
      401:
        description: Unauthorized access
    """
    if "username" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    username = session["username"]
    addresses = lib.get_addresses(username)
    return jsonify(addresses), 200

@app.route('/get_pickups', methods=['GET'])
def get_pickups():
    """
    Get all pickups for the logged-in user
    ---
    responses:
      200:
        description: List of pickups for the user
        examples:
          application/json:
            - id: 1
              address_id: 5
              item: "Steel"
              weight: 20.5
              scheduled_date_start: "2025-04-10"
              scheduled_date_end: "2025-04-12"
              scheduled_time_start: "10:00"
              scheduled_time_end: "14:00"
      401:
        description: Unauthorized access
    """
    if "username" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    username = session["username"]
    pickups = lib.get_pick_ups(username)
    return jsonify(pickups), 200

@app.route("/howwework")
def howwework():
    return "Work in progress!!"

@app.route("/aboutus")
def aboutus():
    return "I just a Proooject!!"

@app.route('/greet', methods=['GET'])
def greet():
    name = request.args.get('username', 'Guest')
    return f'Hello, {name}!'

if __name__ == "__main__":
    app.run(debug=True)
