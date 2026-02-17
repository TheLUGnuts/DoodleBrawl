#jfr, cwf, tjc

from flask import Blueprint, request, jsonify
from components.dbmodel import db, User, Character
import secrets, time

account_bp = Blueprint('account', __name__)

@account_bp.route('/create', methods=['POST'])
def create_account():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    username = data.get('username', "")
    if not re.match(r"^[a-zA-Z0-9]+$", username):
        return jsonify({"error": "Username can only contain letters and numbers!"}), 400
    portrait = data.get('portrait') #expecting a base64 string
    if not username or not portrait:
        return jsonify({"error": "Username and Portrait are required."}), 400
    new_id = None
    while True:
        test_id = "".join([str(secrets.randbelow(10)) for _ in range(16)])
        if not User.query.get(test_id):
            new_id = test_id
            break
    new_user = User(
        id=new_id,
        username=username,
        portrait=portrait,
        creation_time=time.time(),
        money=100
    )
    try:
        db.session.add(new_user)
        db.session.commit()
        print(f"$-- NEW ACCOUNT CREATED: {username} with ID [{new_id}]")
        return jsonify({
            "status": "success",
            "account_id": new_id,
            "message": "Account created. Please save your ID!"
        })
    except Exception as e:
        db.session.rollback()
        print(f"!-- ACCOUNT CREATION ERROR: {e} --!")
        return jsonify({"error": "Database error during account creation"}), 500
    
@account_bp.route('/login', methods=['POST'])
def login_account():
    data = request.get_json()
    account_id = data.get('account_id')
    if not account_id:
        return jsonify({"error": "Account ID required"}), 400
    user = User.query.get(account_id)
    if user:
        bonus_awarded = False
        if time.time() - user.last_login_bonus >= 86400:
            user.money += 200
            user.last_login_bonus = time.time()
            db.session.commit()
            bonus_awarded = True
            print(f"$-- DAILY BONUS: Awarded $200 to {user.username} --$")

        created_chars = Character.query.filter_by(creator_id=user.id).all()
        managed_chars = user.characters

        return jsonify({
            "status": "success",
            "id": user.id,
            "username": user.username,
            "money": user.money,
            "portrait": user.portrait,
            "creation_time": user.creation_time,
            "bonus_awarded": bonus_awarded,
            "created_characters": [c.to_dict() for c in created_chars],
            "managed_characters": [c.to_dict() for c in managed_chars]
        })
    else:
        return jsonify({"error": "Invalid Account ID"}), 401

#returns a publicly viewable profile to avoid sending any IDs
@account_bp.route('/profile/<username>', methods=['GET'])
def get_public_profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    #only return approved characters
    public_chars = Character.query.filter_by(creator_id=user.id, is_approved=True).all()
    
    return jsonify({
        "status": "success",
        "username": user.username,
        "portrait": user.portrait,
        "creation_time": user.creation_time,
        "money": user.money,
        "characters": [c.to_dict_display() for c in public_chars] 
    })