#jfr, cwf, tjc

# This class will define SQLite tables

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column
import time

db = SQLAlchemy()

#user accounts use a Mullvad-style 16 digit number for account identification.
#easy to track and easy to remember/copy
class User(UserMixin, db.Model):
    id = db.Column(db.String(16), primary_key=True)                          #Unique 16-digit ID
    creation_time = db.Column(db.Float, default=time.time)                   #Time of user creation
    portrait = db.Column(db.Text)                                            #User portrait, stored as a base64 text
    username = db.Column(db.String(32))                                      #Username of account
    money = db.Column(db.Integer, default=100)                               #how much money the user has
    last_submission = db.Column(db.Float, default=0.0)
    #One user may manage many characters
    characters = db.relationship('Character', backref='manager', lazy=True)  #who this user 'manages'

    def image_data(self):
        return {
            "image_file": self.image_file
        }
    
class Character(db.Model):
    #identifiers/meta
    id = db.Column(db.String(36), primary_key=True)                          #UUID
    name = db.Column(db.String(64), nullable=False)                          #name of this character
    creation_time = db.Column(db.Float, default=time.time)                   #time the character was created
    image_file = db.Column(db.Text, nullable=False)                          #the drawing of the character.
    #who made this
    creator_id = db.Column(db.String(16), nullable=True, default="Unknown")

    #bio
    description = db.Column(db.Text, default="Mysterious Challenger!")       #description of character
    personality = db.Column(db.String(16), default="Unknown")                
    alignment = db.Column(db.String(20), default="Unknown") 
    titles = db.Column(JSON, default=list)                                   #list of strings
    manager_id = db.Column(db.String(16), db.ForeignKey('user.id'), nullable=True, default="None")
    popularity = db.Column(db.Integer, default=1)

    #combat stats, stored as a json still
    stats = db.Column(JSON, default=dict)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)

    #flags
    is_approved = db.Column(db.Boolean, default=False)

    def get_creator_name(self):
        if self.creator_id and self.creator_id != "Unknown":
            user = User.query.get(self.creator_id)
            return user.username if user else "Unknown"
        return "Unknown"

    def get_manager_name(self):
        if self.manager_id and self.manager_id != "None":
            user = User.query.get(self.manager_id)
            return user.username if user else "None"
        return "None"
    
    #general dict containing everything except for exact user/manager IDs
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "creation_time": self.creation_time,
            "stats": self.stats,
            "wins": self.wins,
            "losses": self.losses,
            "description": self.description,
            "personality": self.personality,
            "image_file": self.image_file,
            "creator_name": self.get_creator_name(),
            "manager_name": self.get_manager_name(),
            "popularity": self.popularity,
            "alignment": self.alignment,
            "is_approved": self.is_approved,
            "titles": self.titles
        }
    
    #dict used for displaying fighters. Doesn't include stats or IDs
    #this should be used for roster and arena views so we don't accidentally reveal character stats.
    def to_dict_display(self):
        return {
            "id": self.id,
            "name": self.name,
            "wins": self.wins,
            "losses": self.losses,
            "description": self.description,
            "image_file": self.image_file,
            "creator_name": self.get_creator_name(),
            "manager_name": self.get_manager_name(),
            "popularity": self.popularity,
            "alignment": self.alignment,
            "titles": self.titles
        }
    
    #dict with everything, including user/manager IDs
    def to_dict_debug(self):
        return {
            "id": self.id,
            "name": self.name,
            "creation_time": self.creation_time,
            "stats": self.stats,
            "wins": self.wins,
            "losses": self.losses,
            "description": self.description,
            "personality": self.personality,
            "image_file": self.image_file,
            "creator_id": self.creator_id,
            "manager_id": self.manager_id,
            "popularity": self.popularity,
            "alignment": self.alignment,
            "is_approved": self.is_approved,
            "titles": self.titles
        }

#Match history db
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)                #id of the match. this is just sequential
    timestamp = db.Column(db.Float, default=time.time)          #timestamp of when the match happened
    match_type = db.Column(db.String(16), default="1v1")        #what kind of match, usually just a 1v1
    summary = db.Column(db.Text)                                #the summary of the match
    winner_name = db.Column(db.String(64))                      
    winner_id = db.Column(db.String(36))                        
    match_data = db.Column(JSON, default=dict)                  #JSON containing the teams
    is_title_bout = db.Column(db.Boolean, default=False)        #was this for a title?
    title_exchanged = db.Column(db.String(36), nullable=True)   #what title was exchanged, if one was?




