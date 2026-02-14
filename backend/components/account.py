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
    
    username = data.get('username')
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
        created_chars = Character.query.filter_by(creator_id=user.id).all()
        managed_chars = user.characters

        return jsonify({
            "status": "success",
            "id": user.id,
            "username": user.username,
            "money": user.money,
            "portrait": user.portrait,
            "creation_time": user.creation_time,
            "created_characters": [c.to_dict() for c in created_chars],
            "managed_characters": [c.to_dict() for c in managed_chars]
        })
    else:
        return jsonify({"error": "Invalid Account ID"}), 401