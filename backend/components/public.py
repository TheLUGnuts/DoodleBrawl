#jfr, cwf, tjc
#to be used for publicly accessible API routes.
#the fighter roster is a good example.
import random
from sqlalchemy import case
from flask import Blueprint, request, jsonify
from components.dbmodel import db, User, Character

public_bp = Blueprint('public', __name__)

#grabs roster data using a "display" dictioniary, excluding certain information.
@public_bp.route('/roster', methods=['POST'])
def return_top_fighters():
    data = request.get_json()
    page = data.get('page', 1)
    per_page = 10
    wl_ratio = case(
        (Character.losses == 0, Character.wins * 1.0),
        else_=(Character.wins * 1.0) / Character.losses
    )
    #sorts descending by w/l ratio then by wins
    pagination = Character.query.filter_by(is_approved=True).order_by(wl_ratio.desc(), Character.wins.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify([c.to_dict_display() for c in pagination.items])

#grabs a "crowd" made up of random user portraits (unusued for now)
@public_bp.route('/crowd')
def return_crowd():
    try:
        users_with_portraits = User.query.filter(User.portrait != None).all()
        selected_users = random.sample(users_with_portraits, min(len(users_with_portraits), 12))
        return jsonify([{"username": u.username, "portrait": u.portrait} for u in selected_users])
    except Exception as e:
        print(f"!-- ERROR FETCHING CROWD: {e} --!")
        return jsonify([])