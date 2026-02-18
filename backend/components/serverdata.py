#jfr, cwf, tjc

import os, json, time, random
from sqlalchemy.sql.expression import func
from components.dbmodel import db, Character, Match

##################################
#          DATA HANDLERS         #
##################################

#data paths
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
        #returns all approved characters
        return Character.query.filter_by(is_approved=True).all()
    
    def get_queue(self):
        #returns all unapproved characters
        queue = Character.query.filter_by(is_approved=False).all()
        if os.path.exists(REJECTED_FILE):
            try:
                with open(REJECTED_FILE, 'r') as f:
                    rejected_data = json.load(f)
                # Ignore them if they are in the rejected ledger
                queue = [c for c in queue if str(c.id) not in rejected_data]
            except Exception as e:
                print(f"!-- ERROR READING REJECTED LIST: {e} --!")
        return queue

    def get_candidates_for_match(self):
        #find fresh meat (fighters with 0 total fights)
        fresh_meat = Character.query.filter_by(is_approved=True, status='active').filter(
            (Character.wins + Character.losses) == 0
        ).all()

        if len(fresh_meat) >= 2:
            print(f"!-- PRIORITY MATCH: FOUND {len(fresh_meat)} NEW FIGHTERS --!")
            return random.sample(fresh_meat, 2)
        
        elif len(fresh_meat) == 1:
            print("!-- PRIORITY MATCH: 1 NEW FIGHTER FOUND --!")
            p1 = fresh_meat[0]
            #select two random characters
            p2 = Character.query.filter_by(is_approved=True, status='active').filter(
                Character.id != p1.id
            ).order_by(func.random()).first()
            
            if p2:
                return [p1, p2]
        
        #fully random if theres no fresh meat
        count = Character.query.filter_by(is_approved=True, status='active').count()
        if count < 2:
            return None
            
        return Character.query.filter_by(is_approved=True, status='active').order_by(func.random()).limit(2).all()

    #########################
    #      SAVING FUNCs     #
    #########################
    
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
        queue = self.get_queue() #unapproved characters
        if len(queue) < 2:
            return

        print(f"!-- SUBMITTING {len(queue)} IMAGES FOR APPROVAL --!")
        
        # Convert list of objs to dict {id: obj} for the genclient
        queue_dict = {c.id: c for c in queue}
        results = self.genclient.submit_for_approval(queue_dict)
        if not results:
            return

        ids_processed = []
        for char_id, decision in results.items():
            character = Character.query.get(char_id)
            if not character: continue

            if decision.get('approved'):
                character.is_approved = True
                print(f"$-- APPROVED: {char_id} --$")
            else:
                # Rejected
                reason = decision.get('reason', 'Unknown')
                print(f"!-- REJECTED: {char_id} - Reason: {reason} --!")
                self.log_rejection(char_id, character, reason)
                character.description = f"REJECTED BY MODERATION: {reason}"
            ids_processed.append(char_id)
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
            "image": char_obj.image_file 
        }
        
        try:
            with open(REJECTED_FILE, 'w') as f:
                json.dump(rejected_data, f, indent=2)
            print(f"!-- LOGGED REJECTION FOR {char_id} --!")
        except Exception as e:
            print(f"!-- ERROR SAVING REJECTION: {e} --!")

    #########################
    #     DEBUG FUNCs       #
    #########################

    def randomize_alignments(self):
        all_chars = Character.query.all()
        options = ["Good", "Evil", "Neutral"]
        
        count = 0
        for char in all_chars:
            char.alignment = random.choice(options)
            count += 1
            
        self.commit()
        print(f"!-- RANDOMIZED ALIGNMENTS FOR {count} CHARACTERS --!")
        return count