#jfr, cwf, tjc

from flask import Blueprint, request, jsonify
from components.dbmodel import db, User, Character, Team
from sqlalchemy.orm.attributes import flag_modified
import secrets, time, re

account_bp = Blueprint('account', __name__)

@account_bp.route('/create', methods=['POST'])
def create_account():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    username = data.get('username', "")
    if not re.match(r"^[a-zA-Z0-9]+$", username):
        return jsonify({"error": "Username can only contain letters and numbers!"}), 400
    #make sure the username isn't already being used.
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "That username is already taken! Please choose another."}), 400
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
        teams = user.teams

        return jsonify({
            "status": "success",
            "id": user.id,
            "username": user.username,
            "money": user.money,
            "portrait": user.portrait,
            "creation_time": user.creation_time,
            "bonus_awarded": bonus_awarded,
            "created_characters": [c.to_dict_display() for c in created_chars],
            "managed_characters": [c.to_dict() for c in managed_chars],
            "teams": [t.to_dict() for t in teams]
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
    public_chars = Character.query.filter_by(manager_id=user.id, is_approved=True).all()
    return jsonify({
        "status": "success",
        "username": user.username,
        "portrait": user.portrait,
        "creation_time": user.creation_time,
        "money": user.money,
        "characters": [c.to_dict_display() for c in public_chars] 
    })

#perform managerial actions on managed fighters
@account_bp.route('/manage_fighter', methods=['POST'])
def manage_fighter():
    data = request.get_json()
    account_id = data.get('account_id')
    fighter_id = data.get('fighter_id')
    action = data.get('action')

    user = User.query.get(account_id)
    fighter = Character.query.get(fighter_id)

    if not user or not fighter: return jsonify({"error": "Invalid user or fighter"}), 400
    if fighter.manager_id != user.id: return jsonify({"error": "You do not manage this fighter."}), 403

    def remove_from_current_team():
        if fighter.team_id:
            old_team = Team.query.get(fighter.team_id)
            if old_team and old_team.member_ids and fighter.id in old_team.member_ids:
                # JSON columns return copies, so we must extract, edit, and re-assign
                old_members = list(old_team.member_ids)
                old_members.remove(fighter.id)
                old_team.member_ids = old_members
                flag_modified(old_team, "member_ids") # Tells SQLAlchemy to save the JSON update
        fighter.team_id = None
        fighter.team_name = ""
    #Current actions:
    #'pull' - Pull them from being able to fight
    #'activate' - Put them back into the active roster
    #'retire' - Permanently take them out of the active roster.
    #'release' - Revoke your managerial status over a character, making them a free-agent.
    #'team' - Assign the fighter to a team to employ them in multi-man battles.
    if action == 'pull': 
        fighter.status = 'inactive'
    elif action == 'activate': 
        fighter.status = 'active'
    elif action == 'retire': 
        fighter.status = 'retired'
        fighter.manager_id = 'None'
        remove_from_current_team()
    elif action == 'release': 
        fighter.manager_id = 'None'
        fighter.status = 'active'
        remove_from_current_team()
    elif action == 'team':
        team_id = data.get('team_id')
        if not team_id:
            remove_from_current_team()
        else:
            remove_from_current_team() 
            
            new_team = Team.query.get(team_id)
            if new_team:
                fighter.team_id = new_team.id
                fighter.team_name = new_team.name if new_team.name else f"Team {new_team.id}"
                new_members = list(new_team.member_ids) if new_team.member_ids else []
                if fighter.id not in new_members:
                    new_members.append(fighter.id)
                    new_team.member_ids = new_members
                    flag_modified(new_team, "member_ids")
    else:
        return jsonify({"error": "Invalid action."}), 400
    db.session.commit()
    return jsonify({"status": "success", "message": f"Action '{action}' applied successfully!"})

#create a new team
@account_bp.route('/create_team', methods=['POST'])
def create_team():
    data = request.get_json()
    manager_id = data.get('account_id')
    team = Team(
        manager_id=manager_id
    )
    db.session.add(team)
    db.session.commit()
    return jsonify({"status": "success", "message": f"New team created!"})

#perform managerial actions on teams
@account_bp.route('/manage_team', methods=['POST'])
def manage_team():
    data = request.get_json()
    account_id = data.get('account_id') #we need to make sure the user performing the action has the authority too
    team_id = data.get('team_id')
    action = data.get('action')

    user = User.query.get(account_id)
    team = Team.query.get(team_id)
    #safety checks
    if not user or not team: return jsonify({"error": "Invalid user or team"}), 400
    if team.manager_id != user.id: return jsonify({"error": "You do not manage this team."}), 403
    #FIXME
