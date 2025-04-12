from flask import Flask, render_template, request, jsonify, session
from flasgger import Swagger
import lib, json

app = Flask(__name__)
Swagger(app)
app.secret_key = "6a94b15e9b77f948e3f82f7fa4c5c58a8c01acb510298cc0cc85e798ba2575d0"

@app.route('/')
def home():
    if 'username' not in session:
        return render_template('index.html')
    if session["role"]=="individual" or session["role"]=="Individual":
        return render_template('dashboard.html')
    return render_template('c-board.html')

@app.route('/logout')
def logout():
    session.clear()
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/update')
def update():
    return render_template('update.html')

@app.route('/requests')
def requests():
    return render_template('request.html')

@app.route('/collect_history')
def collector_history():
    return render_template('collector_history.html')

@app.route('/aboutus')
def about():
    return render_template('about.html')

@app.route('/load')
def load():
    username = session['username']
    return jsonify({
        "user": username,
        "items": lib.get_all_items(),
        "addresses": lib.get_addresses(username),
        "pickups": lib.get_pick_ups(username)
    })
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup", methods=["GET"])
def signup():
    return render_template("signup.html")

@app.route("/save", methods=["POST"])
def save(): 
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        iscollector = bool(data.get("iscollector"))

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Missing username or password"
            }), 400

        print(f"Received signup - username: {username}, password: {password}, iscollector: {iscollector}")

        if iscollector:
            flag = lib.create_user(username, password, "collector")
        else:
            flag = lib.create_user(username, password, "individual")

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
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            return jsonify({"message": "Missing username or password"}), 400

        print(f"Received login - username: {username}, password: {password}")
        flag = lib.validate_login(username, password)
        if flag=="invalid":
            return jsonify({"message": "Invalid Credential!"}), 401

        session["username"] = username
        role = lib.get_user_role(username)
        session["role"] = role

        return jsonify({"message": "Login successful!"})
    except Exception as e:
        print("Error in /auth:", e)
        return jsonify({"message": "Server error", "error": str(e)}), 500

@app.route("/create_address", methods=["POST"])
def create_address():
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
    if "username" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    try:
        address_id = int(data['address_id'])
        user_addresses = lib.get_addresses(session["username"])
        valid_address_ids = [addr['id'] for addr in user_addresses]
        if address_id not in valid_address_ids:
            return jsonify({"error": "Invalid address"}), 403

        items = data['items']
        # if not items or not isinstance(items, list) or not all(isinstance(i, str) for i in items):
        #     return jsonify({"error": "Items must be a list of strings"}), 400

        # if not lib.validate_items_exist(items):
        #     return jsonify({"error": "Invalid item(s) in list"}), 400

        pickup_id = lib.create_pickup(
            address_id=address_id,
            items=[items],  
            date_start=data['date_start'],
            date_end=data['date_end'],
            time_start=data['time_start'],
            time_end=data['time_end']
        )

        if pickup_id:
            return jsonify({
                "status": "success",
                "pickup_id": pickup_id
            }), 201
        return jsonify({"error": "Failed to create pickup"}), 500

    except KeyError as e:
        return jsonify({"error": f"Missing parameter: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
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
    tags:
      - Pickups
    responses:
      200:
        description: List of pickups with items
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              address_id:
                type: integer
                example: 5
              items:
                type: array
                items:
                  type: object
                  properties:
                    name:
                      type: string
                      example: "Paper"
                    weight:
                      type: number
                      format: float
                      example: 5.2
              scheduled_date_start:
                type: string
                example: "2023-10-01"
              scheduled_date_end:
                type: string
                example: "2023-10-01"
              scheduled_time_start:
                type: string
                example: "09:00"
              scheduled_time_end:
                type: string
                example: "12:00"
              status:
                type: string
                example: "scheduled"
              created_at:
                type: string
                example: "2023-09-25 14:30:00"
      401:
        description: Unauthorized access
    """
    if "username" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    username = session["username"]
    raw_pickups = lib.get_pick_ups(username)
    
    parsed_pickups = []
    for pickup in raw_pickups:
        parsed = dict(pickup)
        parsed['items'] = json.loads(pickup['items_json'])
        del parsed['items_json']
        parsed_pickups.append(parsed)
    
    return jsonify(parsed_pickups), 200

@app.route('/create_drive', methods=['POST'])
def create_drive():
    """
    Create a new drive entry
    ---
    tags:
      - Drives
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            pick_up_id:
              type: integer
              example: 5
    responses:
      201:
        description: Drive created successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            drive_id:
              type: string
              example: "a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p"
      400:
        description: Invalid pickup ID or user
      401:
        description: Unauthorized
    """
    if "username" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    try:
        username = session["username"]
        pick_up_id = int(data['pick_up_id'])
        
        pickups = lib.get_pick_ups(username)
        valid_pickup_ids = [p['id'] for p in pickups]
        if pick_up_id not in valid_pickup_ids:
            return jsonify({"error": "Invalid pickup ID"}), 400

        success = lib.create_drive(pick_up_id, username)
        if success:
            return jsonify({
                "status": "success",
                "drive_id": lib.get_drives_by_username(username)[-1]['id']
            }), 201
        return jsonify({"error": "Drive creation failed"}), 400
        
    except KeyError:
        return jsonify({"error": "Missing pick_up_id"}), 400
    except ValueError:
        return jsonify({"error": "Invalid pickup ID format"}), 400

@app.route('/drive/<drive_id>', methods=['GET'])
def get_drive(drive_id):
    """
    Get drive details by ID
    ---
    tags:
      - Drives
    parameters:
      - name: drive_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Drive details
        schema:
          type: object
          properties:
            id:
              type: string
              example: "a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p"
            pick_up_id:
              type: integer
              example: 5
            username:
              type: string
              example: "user123"
            status_flags:
              type: object
              properties:
                is_complete:
                  type: boolean
                  example: false
                out_for_pick_up:
                  type: boolean
                  example: true
                get_pick_up:
                  type: boolean
                  example: false
                out_for_delivery:
                  type: boolean
                  example: false
                delivered:
                  type: boolean
                  example: false
      404:
        description: Drive not found
    """
    drive = lib.get_drive(drive_id)
    if not drive:
        return jsonify({"error": "Drive not found"}), 404
    return jsonify(drive), 200

@app.route('/drive/<drive_id>/status', methods=['PUT'])
def update_drive_status(drive_id):
    """
    Update drive status flags
    ---
    tags:
      - Drives
    parameters:
      - name: drive_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            field:
              type: string
              enum: [is_complete, out_for_pick_up, get_pick_up, out_for_delivery, delivered]
              example: "out_for_pick_up"
            value:
              type: boolean
              example: true
    responses:
      200:
        description: Status updated
      400:
        description: Invalid field name
      404:
        description: Drive not found
    """
    data = request.get_json()
    try:
        field = data['field']
        value = data['value']
        if lib.update_drive_status(drive_id, field, value):
            return jsonify({"status": "success"}), 200
        return jsonify({"error": "Drive not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/drives', methods=['GET'])
def get_all_drives():
    """
    Get all drives (admin only)
    ---
    tags:
      - Drives
    responses:
      200:
        description: List of all drives
        schema:
          type: array
          items:
            $ref: '#/definitions/Drive'
      403:
        description: Forbidden (non-admin access)
    """
    if "username" not in session or lib.validate_login(session["username"], "") != "admin":
        return jsonify({"error": "Forbidden"}), 403
        
    drives = lib.get_all_drives()
    return jsonify(drives), 200

@app.route("/address")
def address():
    return render_template("address.html")

@app.route('/handle_address', methods=['GET', 'POST'])
def handle_addresses():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    username = session['username']

    if request.method == 'POST':
        data = request.get_json()
        required_fields = ['name', 'email', 'phone', 'street', 'role', 'pincode']
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        success = lib.create_address(
            username=username,
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            street=data['street'],
            role=data['role'],
            pincode=data['pincode']
        )

        if not success:
            return jsonify({"error": "Failed to create address"}), 400
            
        return jsonify({"message": "Address created successfully"}), 201

    if request.method == 'GET':
        addresses = lib.get_addresses(username)
        return jsonify({"addresses": addresses}), 200

@app.route("/schedule")
def schedule():
    return render_template("schedule.html")

@app.route("/track")
def track():
    return render_template("track.html")

@app.route('/greet', methods=['GET'])
def greet():
    name = request.args.get('username', 'Guest')
    return f'Hello, {name}!'

if __name__ == "__main__":
    app.run(debug=True)
