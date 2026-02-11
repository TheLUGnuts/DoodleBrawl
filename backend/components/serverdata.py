#jfr, cwf, tjc

import os, json, time, random
from components.dbmodel import db, Character, Match
from sqlalchemy.sql.expression import func

##################################
#          DATA HANDLERS         #
##################################

#Data paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'assets/Data')
REJECTED_FILE = os.path.join(DATA_DIR, 'rejected.json')

class ServerData:
    def __init__(self, genclient):
        self.genclient = genclient 

    #########################
    #      FETCH FUNCs      #
    #########################

    def get_character(self, char_id):
        return Character.query.get(char_id)

    def get_roster(self):
        """Returns all approved characters."""
        return Character.query.filter_by(is_approved=True).all()
    
    def get_queue(self):
        """Returns all unapproved characters."""
        return Character.query.filter_by(is_approved=False).all()

    def get_candidates_for_match(self):
        """
        Smart logic to find fighters for the next match.
        Prioritizes fresh meat (0 fights).
        """
        # 1. Look for Fresh Meat (0 fights)
        fresh_meat = Character.query.filter_by(is_approved=True).filter(
            (Character.wins + Character.losses) == 0
        ).all()

        if len(fresh_meat) >= 2:
            print(f"!-- PRIORITY MATCH: FOUND {len(fresh_meat)} NEW FIGHTERS --!")
            return random.sample(fresh_meat, 2)
        
        elif len(fresh_meat) == 1:
            print("!-- PRIORITY MATCH: 1 NEW FIGHTER FOUND --!")
            p1 = fresh_meat[0]
            # Get a random opponent that isn't p1
            # func.random() works with SQLite
            p2 = Character.query.filter_by(is_approved=True).filter(
                Character.id != p1.id
            ).order_by(func.random()).first()
            
            if p2:
                return [p1, p2]
        
        # 2. If no fresh meat, fully random
        count = Character.query.filter_by(is_approved=True).count()
        if count < 2:
            return None
            
        return Character.query.filter_by(is_approved=True).order_by(func.random()).limit(2).all()

    #########################
    #      SAVING FUNCs     #
    #########################
    
    # NOTE: With SQLite, we generally just call db.session.commit() in the main logic,
    # but we can add helper wrappers here if needed.
    
    def commit(self):
        try:
            db.session.commit()
        except Exception as e:
            print(f"!-- DB COMMIT ERROR: {e} --!")
            db.session.rollback()

    #########################
    #    GenClient FUNCs    #
    #########################

    def submit_queue_for_approval(self):
        # 1. Get unapproved characters
        queue = self.get_queue()
        
        # Only run if we have a batch (e.g., 3 or more, or just run it on whatever)
        if len(queue) < 3:
            return

        print(f"!-- SUBMITTING {len(queue)} IMAGES FOR APPROVAL --!")
        
        # Convert list of objs to dict {id: obj} for the genclient
        queue_dict = {c.id: c for c in queue}
        
        # 2. Send to AI
        results = self.genclient.submit_for_approval(queue_dict)
        
        if not results:
            return

        # 3. Process Results
        ids_processed = []
        for char_id, decision in results.items():
            character = Character.query.get(char_id)
            if not character: continue

            if decision.get('approved'):
                character.is_approved = True
                print(f"$-- APPROVED: {char_id} --$")
            else:
                # Rejected - Delete from DB and Log
                reason = decision.get('reason', 'Unknown')
                print(f"!-- REJECTED: {char_id} - Reason: {reason} --!")
                self.log_rejection(char_id, character, reason)
                db.session.delete(character)
            
            ids_processed.append(char_id)

        # 4. Save changes
        self.commit()

    #########################
    #     Logging FUNCs     #
    #########################

    def log_match_result(self, teams, winner, summary, match_type="1v1", title_change=None):
        # Format teams for JSON storage
        formatted_teams = []
        for team in teams:
            team_data = [{"id": f.id, "name": f.name} for f in team]
            formatted_teams.append(team_data)

        new_match = Match(
            timestamp=time.time(),
            match_type=match_type,
            is_title_bout=(title_change is not None),
            title_exchanged=title_change if title_change else None,
            match_data={"teams": formatted_teams}, # Stores the team composition
            winner_id=winner.id,
            winner_name=winner.name,
            summary=summary
        )

        db.session.add(new_match)
        self.commit()

    def log_rejection(self, char_id, char_obj, reason):
        # We still use a JSON file for rejections since we didn't make a Rejection Table
        rejected_data = {}
        if os.path.exists(REJECTED_FILE):
            try:
                with open(REJECTED_FILE, 'r') as f:
                    rejected_data = json.load(f)
            except:
                rejected_data = {}
        
        rejected_data[char_id] = {
            "id": char_id,
            "name": char_obj.name,
            "reason": reason,
            # For DB objects, image_file is the base64 string
            "image": char_obj.image_file 
        }
        
        try:
            with open(REJECTED_FILE, 'w') as f:
                json.dump(rejected_data, f, indent=2)
            print(f"!-- LOGGED REJECTION FOR {char_id} --!")
        except Exception as e:
            print(f"!-- ERROR SAVING REJECTION: {e} --!")