#jfr, cwf, tjc
#routes for the debug api.
#these are locked to admin usage only.
import os
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm.attributes import flag_modified
from components.dbmodel import db, User, Character, Match, Team

##################################
#         DEBUG HANDLERS         #
##################################

debug_bp = Blueprint('debug', __name__)
#is the user submitting this an admin?
def is_admin_authorized():
    # If local development, bypass this
    if current_app.debug or "localhost" in os.getenv('VITE_SOCKET_URL', ''):
        return True
    admin_ids = [i.strip() for i in os.getenv('ADMIN_IDS', '').split(',') if i.strip()]
    user_id = request.headers.get('X-User-ID')
    return user_id and user_id in admin_ids

#grabs all the character information from the database.
@debug_bp.route('/characters', methods=['GET'])
def debug_get_characters():
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    characters = Character.query.all()
    return jsonify([character.to_dict_debug() for character in characters])

#grabs all the teams
@debug_bp.route('/teams', methods=['GET'])
def debug_get_teams():
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403 
    teams = Team.query.all()
    print(f"{teams[0].to_dict()}")
    return jsonify([team.to_dict() for team in teams])

@debug_bp.route('/team/<team_id>', methods=['POST'])
def debug_update_team(team_id):
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    team = Team.query.get(team_id)
    if not team: return jsonify({"error": "Team not found"}), 404
    try:
        if 'name' in data: team.name = data['name']
        if 'description' in data: team.description = data['description']
        if 'manager_id' in data: team.manager_id = data['manager_id']
        if 'wins' in data: team.wins = int(data['wins'])
        if 'losses' in data: team.losses = int(data['losses'])
        if 'popularity' in data: team.popularity = int(data['popularity'])
        if 'member_ids' in data:
            team.member_ids = data['member_ids']
            flag_modified(team, "member_ids")
            
        db.session.commit()
        print(f"!-- DEBUG: UPDATED TEAM {team.id} --!")
        return jsonify({"status": "success", "message": f"Updated Team {team.id}"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
#updates a characters database entry
@debug_bp.route('/character/<char_id>', methods=['POST'])
def debug_update_character(char_id):
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    char = Character.query.get(char_id)
    if not char: return jsonify({"error": "Character not found"}), 404
    try:
        if 'name' in data: char.name = data['name']
        if 'description' in data: char.description = data['description']
        if 'alignment' in data: char.alignment = data['alignment']
        if 'popularity' in data: char.popularity = int(data['popularity'])
        if 'wins' in data: char.wins = int(data['wins'])
        if 'losses' in data: char.losses = int(data['losses'])
        if 'personality' in data: char.personality = data['personality']
        if 'is_approved' in data: char.is_approved = bool(data['is_approved'])
        if 'team_name' in data: char.team_name = data['team_name']
        if 'team_id' in data: char.team_name = data['team_id']
        if 'status' in data: char.status = data['status']
        if 'creator_id' in data: char.creator_id = data['creator_id']
        if 'manager_id' in data: char.manager_id = data['manager_id']
        if 'creation_time' in data: char.creation_time = float(data['creation_time'])
        if 'stats' in data: 
            char.stats = data['stats']
            flag_modified(char, "stats")
        if 'titles' in data:
            char.titles = data['titles']
            flag_modified(char, "titles")
        db.session.commit()
        print(f"!-- DEBUG: UPDATED CHARACTER {char.name} --!")
        return jsonify({"status": "success", "message": f"Updated {char.name}"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

#grabs the list of all users from the user table
@debug_bp.route('/users', methods=['GET'])
def debug_get_users():
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403 
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "money": u.money,
        "creation_time": u.creation_time,
        "last_submission": u.last_submission,
        "last_login_bonus": u.last_login_bonus,
        "portrait": u.portrait
    } for u in users])

#grabs all the info on a user based on their ID
@debug_bp.route('/user/<user_id>', methods=['POST'])
def debug_update_user(user_id):
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403 
    data = request.get_json()
    user = User.query.get(user_id)
    if not user: return jsonify({"error": "User not found"}), 404
    try:
        if 'username' in data: user.username = data['username']
        if 'money' in data: user.money = int(data['money'])
        if 'creation_time' in data: user.creation_time = float(data['creation_time'])
        if 'last_submission' in data: user.last_submission = float(data['last_submission'])
        if 'last_login_bonus' in data: user.last_login_bonus = float(data['last_login_bonus'])
        if 'portrait' in data: user.portrait = data['portrait']
        db.session.commit()
        print(f"!-- DEBUG: UPDATED USER {user.username} --!")
        return jsonify({"status": "success", "message": f"Updated {user.username}"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

#grabs all the match history
@debug_bp.route('/matches', methods=['GET'])
def debug_get_matches():
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    matches = Match.query.order_by(Match.timestamp.desc()).all()
    return jsonify([match.to_dict_debug() for match in matches])

#recalls a matches info based on the match id
@debug_bp.route('/match/<match_id>', methods=['POST'])
def debug_update_match(match_id):
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    match = Match.query.get(match_id)
    if not match: return jsonify({"error": "Match not found"}), 404
    try:
        if 'summary' in data: match.summary = data['summary']
        if 'winner_name' in data: match.winner_name = data['winner_name']
        if 'winner_id' in data: match.winner_id = data['winner_id']
        if 'match_type' in data: match.match_type = data['match_type']
        if 'is_title_bout' in data: match.is_title_bout = bool(data['is_title_bout'])
        if 'title_exchanged' in data: match.title_exchanged = data['title_exchanged']
        
        if 'match_data' in data:
            match.match_data = data['match_data']
            flag_modified(match, "match_data")
            
        db.session.commit()
        return jsonify({"status": "success", "message": f"Updated Match {match.id}"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

#deletes a row from a table, given the table and identifier
@debug_bp.route('/<table_type>/<item_id>', methods=['DELETE'])
def debug_delete_item(table_type, item_id):
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    try:
        if table_type == 'character': item = Character.query.get(item_id)
        elif table_type == 'user': item = User.query.get(item_id)
        elif table_type == 'match': item = Match.query.get(item_id)
        elif table_type == 'team': item = Team.query.get(item_id)
        else: return jsonify({"error": "Invalid table type"}), 400
        if not item: return jsonify({"error": "Item not found"}), 404
        db.session.delete(item)
        db.session.commit()
        print(f"!-- DEBUG: DELETED {table_type.upper()} {item_id} --!")
        return jsonify({"status": "success", "message": f"Deleted {table_type} {item_id}"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500