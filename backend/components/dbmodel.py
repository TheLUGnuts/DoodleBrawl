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
    id = db.Column(db.String(16), primary_key=True)                                                 #Unique 16-digit ID
    creation_time = db.Column(db.Float, default=time.time)                                          #Time of user creation
    portrait = db.Column(db.Text)                                                                   #User portrait, stored as a base64 text
    username = db.Column(db.String(32))                                                             #Username of account
    money = db.Column(db.Integer, default=100)                                                      #how much money the user has
    last_submission = db.Column(db.Float, default=0.0)                                              #when did the user last submit a character, used for 5min cooldown
    last_login_bonus = db.Column(db.Float, default=0.0)                                             #timer for tracking login bonus reward
    #One user may manage many characters
    characters = db.relationship('Character', backref='manager', lazy=True)                         #who this user 'manages'

    def image_data(self):
        return {
            "image_file": self.image_file
        }
    
class Character(db.Model):
    #identifiers/meta
    id = db.Column(db.String(36), primary_key=True)                                                 #UUID
    name = db.Column(db.String(64), nullable=False, unique=True)                                    #name of this character
    creation_time = db.Column(db.Float, default=time.time)                                          #time the character was created
    image_file = db.Column(db.Text, nullable=False)                                                 #the drawing of the character.
    
    creator_id = db.Column(db.String(16), nullable=True, default="Unknown")                         #who made this?
    manager_id = db.Column(db.String(16), db.ForeignKey('user.id'), nullable=True, default="None")  #who is their manager?

    #bio
    description = db.Column(db.Text, default="Mysterious Challenger!")                              #description of character
    personality = db.Column(db.String(16), default="Unknown")                                       #how this character conducts themselves
    alignment = db.Column(db.String(20), default="Unknown")                                         #what titles do they hold
    titles = db.Column(JSON, default=list)                                                          #list of strings
    popularity = db.Column(db.Integer, default=1)                                                   #how popular is this character (based on generated stats, not influenced by humans yet)
    status = db.Column(db.String(16), default="active")                                             #what is the status of this character? active, retired, injured
    team_name = db.Column(db.String(32), default="", unique=True)                                   #name of the team they are apart of.

    #combat stats, stored as a json still
    stats = db.Column(JSON, default=dict)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)

    #flags
    is_approved = db.Column(db.Boolean, default=False)

    #return the username of who created this character
    def get_creator_name(self):
        if self.creator_id and self.creator_id != "Unknown":
            user = User.query.get(self.creator_id)
            return user.username if user else "Unknown"
        return "Unknown"
    #return the portrait of the creator of this character
    def get_creator_portrait(self):
        if self.creator_id and self.creator_id != "Unknown":
            user = User.query.get(self.creator_id)
            return user.portrait if user else None
        return None
    #return the username of who manages this character
    def get_manager_name(self):
        if self.manager_id and self.manager_id != "None":
            user = User.query.get(self.manager_id)
            return user.username if user else "None"
        return "None"
    #return the portrait of the manager of this character
    def get_manager_portrait(self):
        if self.manager_id and self.manager_id != "Unknown":
            user = User.query.get(self.manager_id)
            return user.portrait if user else None
        return None

    
    #general dict containing everything except for exact user/manager IDs
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "creation_time": self.creation_time,
            "stats": self.stats,
            "wins": self.wins,
            "losses": self.losses,
            "status": self.status,
            "description": self.description,
            "personality": self.personality,
            "team_name": self.team_name,
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
            "status": self.status,
            "is_approved": self.is_approved,
            "description": self.description,
            "image_file": self.image_file,
            "team_name": self.team_name,
            "creator_name": self.get_creator_name(),
            "creator_portrait": self.get_creator_portrait(),
            "manager_name": self.get_manager_name(),
            "manager_portrait": self.get_manager_portrait(),
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
            "status": self.status,
            "team_name": self.team_name,
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

    def to_dict_display(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "match_type": self.match_type,
            "summary": self.summary,
            "winner_name": self.winner_name,
            "winner_id": self.winner_id,
            "is_title_bout": self.is_title_bout,
            "title_exchanged": self.title_exchanged
        }

    def to_dict_debug(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "match_type": self.match_type,
            "summary": self.summary,
            "winner_name": self.winner_name,
            "winner_id": self.winner_id,
            "match_data": self.match_data,
            "is_title_bout": self.is_title_bout,
            "title_exchanged": self.title_exchanged
        }



