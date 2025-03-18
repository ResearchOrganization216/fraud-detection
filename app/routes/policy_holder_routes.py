from flask import Blueprint, request, jsonify
from config import Config
from google.oauth2 import service_account
from google.cloud import storage
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from app.types.policy_holder import PolicyHolder
import uuid, datetime

policy_holder_bp = Blueprint('policy_holder_bp', __name__)

# Set up Google Cloud Storage client using configuration values.
# If KEY_PATH is provided (e.g., in local development) use it; in production on GKE you may leave it empty.
if Config.KEY_PATH:
    credentials = service_account.Credentials.from_service_account_file(Config.KEY_PATH)
    storage_client = storage.Client(credentials=credentials, project=Config.PROJECT_ID)
else:
    storage_client = storage.Client(project=Config.PROJECT_ID)

@policy_holder_bp.route('/register', methods=['POST'])
def register_policy_holder():
    # Expect a multipart/form-data request.
    username = request.form.get('username')
    email = request.form.get('email')
    policy_id = request.form.get('policyID')
    password = request.form.get('password')
    created_user = request.form.get('created_user', 'system')
    
    # Validate required fields.
    if not username or not email or not policy_id or not password:
        return jsonify({"error": "username, email, policyID, and password are required"}), 400

    # Generate a UUID for this record (this will also prefix the image filename).
    record_uuid = str(uuid.uuid4())
    
    # Hash the provided password.
    password_hash = generate_password_hash(password)

    # Process profile image if provided.
    file = request.files.get('profile_image')
    image_url = None
    if file:
        try:
            bucket = storage_client.bucket(Config.BUCKET_NAME)
            # Prepend the UUID to the filename and store it under "user_attachments"
            new_filename = f"user_attachments/{record_uuid}_{file.filename}"
            blob = bucket.blob(new_filename)
            blob.upload_from_file(file)
            image_url = blob.public_url
        except Exception as e:
            return jsonify({"error": "Failed to upload profile image: " + str(e)}), 500

    # Create a new PolicyHolder record.
    # Use record_uuid for the UUID field and a truncated version for USER_CODE (ensuring it fits within 20 chars)
    new_policy_holder = PolicyHolder(
        USER_CODE = record_uuid[:20],
        USER_NAME = username,
        UUID = record_uuid,
        USER_EMAIL = email,
        USER_PASSWORD_HASH = password_hash,
        USER_IMAGE_PATH = image_url,
        USER_STATUS = 'P',  # Default status is "P"
        POLICY_ID = policy_id,
        CREATED_USER_CODE = created_user,
        CREATED_DATE = datetime.datetime.utcnow()
    )

    try:
        db.session.add(new_policy_holder)
        db.session.commit()
        return jsonify({
            "message": "Policy holder registered successfully",
            "user_code": new_policy_holder.USER_CODE
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error: " + str(e)}), 500

@policy_holder_bp.route('/login', methods=['POST'])
def login_policy_holder():
    data = request.get_json()
    if not data:
        print("Missing JSON data")
        return jsonify({"error": "Missing JSON data"}), 400

    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        print("Email and/or password not provided")
        return jsonify({"error": "Email and password are required"}), 400

    # Query the database for a policy holder with the given email.
    policy_holder = PolicyHolder.query.filter_by(USER_EMAIL=email).first()
    
    if not policy_holder:
        print("No policy holder found for email:", email)
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Check if the password matches.
    if not check_password_hash(policy_holder.USER_PASSWORD_HASH, password):
        print("Password mismatch for email:", email)
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Check the user's status.
    if policy_holder.USER_STATUS.upper() == "P":
        print("Account pending for email:", email)
        return jsonify({"message": "Your account is still in pending state. Try again later"}), 200
    
    if policy_holder.USER_STATUS.upper() == "A":
        print("Login successful for email:", email)
        return jsonify({
            "message": "Login successful",
            "username": policy_holder.USER_NAME,
            "email": policy_holder.USER_EMAIL,
            "policyID": policy_holder.POLICY_ID,
            "image_path": policy_holder.USER_IMAGE_PATH
        }), 200

    print("Falling through: invalid credentials for email:", email)
    return jsonify({"error": "Invalid credentials"}), 401