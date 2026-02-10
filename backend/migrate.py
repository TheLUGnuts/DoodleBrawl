import json, os
from app import app
from components.dbmodel import db, Character, Match, User

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'assets/Data') 
CHAR_FILE = os.path.join(DATA_DIR, 'characters.json')
QUEUE_FILE = os.path.join(DATA_DIR, 'queue.json')
HIST_FILE = os.path.join(DATA_DIR, 'history.json')

def migrate():
    with app.app_context():
        db.create_all()
        try:
            if os.path.exists(CHAR_FILE):
                with open(CHAR_FILE, 'r') as f:
                    data = json.load(f)
                    print(f"CHARACTER FILE: {len(data.items())}")
                    for c_id, c_data in data.items():
                        if not Character.query.get(c_id):
                            new_char = Character(
                                id=c_id,
                                name=c_data.get('name', 'Unknown'),
                                description=c_data.get('description', ''),
                                personality=c_data.get('personality', 'Unknown'),
                                height=c_data.get('height', "Unknown"),
                                weight=c_data.get('weight', "Unknown"),
                                stats=c_data.get('stats', {}),
                                wins=c_data.get('wins', 0),
                                losses=c_data.get('losses', 0),
                                image_file=c_data.get('image_file', ''),
                                status=c_data.get('status', 'Rookie'),
                                is_approved=True # It was in characters.json, so it's approved
                            )
                            print(f"ADDING {c_data.get('name')}")
                            db.session.add(new_char)
            print(f"STARTING APPROVAL QUEUE")
            #migrate approval queue
            if os.path.exists(QUEUE_FILE):
                with open(QUEUE_FILE, 'r') as f:
                    data = json.load(f)
                    print(f"QUEUE FILE COUNT: {len(data.items())}")
                    for c_id, c_data in data.items():
                        if not Character.query.get(c_id):
                            new_char = Character(
                                id=c_id,
                                name=c_data.get('name', 'Unknown'),
                                image_file=c_data.get('image_file', ''),
                                is_approved=False # It was in queue, so NOT approved
                            )
                            print(f"ADDING {c_data.get('name')}")
                            db.session.add(new_char)

            print(f"STARTING HISTORY")
            #migrate history
            if os.path.exists(HIST_FILE):
                with open(HIST_FILE, 'r') as f:
                    data = json.load(f)
                    for entry in data:
                        new_match = Match(
                            timestamp=entry.get('timestamp'),
                            match_type=entry.get('match_type', '1v1'),
                            summary=entry.get('display_text', ''),
                            winner_id=entry.get('winner_id'),
                            is_title_bout=entry.get('is_title_bout', False),
                            title_exchanged=str(entry.get('title_exchanged')) if entry.get('title_exchanged') else None,
                            match_data={"teams": entry.get('teams', [])}
                        )
                        db.session.add(new_match)
        except Exception as e:
            print(e)

        db.session.commit()
        print("Migration Complete! SQLite DB created.")

if __name__ == "__main__":
    migrate()