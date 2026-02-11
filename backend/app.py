#jfr, cwf, tjc
#Created for the 2026 VCU 24HR Hackathon

import json, os, random, re, time, secrets
from components.dbmodel                            import db, Character, Match
from flask_cors                                                    import CORS
from components.genclient                                     import Genclient
from components.serverdata                                   import ServerData
from dotenv                                                 import load_dotenv
from flask_socketio                                      import SocketIO, emit
from flask                     import Flask, render_template, jsonify, request
from flask_login import LoginManager, login_user, current_user, login_required
from sqlalchemy.orm.attributes import flag_modified


#################################
#          DOODLE BRAWL         #
#################################

load_dotenv()                                                           #load the env variables
API_URL = os.getenv('VITE_SOCKET_URL')
app = Flask(__name__,                                                   #launch the flask app
    static_folder="../Frontend/dist/assets",
    template_folder="../Frontend/dist",
    static_url_path="/assets")
app.config['SECRET_KEYS'] = os.getenv('SECRET_KEY')                     #secret key for CORS prevention, taken from .env file
CORS(app)                                                               #Apply the CORS prevention onto the flask app
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:5173", f"{API_URL}"]) #begin sockets for listening and sending out info

#SQLite database initialitzation
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///doodlebrawl.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

#Global variables
BATTLE_TIMER=180                                                        #3 minutes in seconds
CURRENT_TIMER = BATTLE_TIMER                                            #global time tracker
NEXT_MATCH = None                                                       #holds the [char1, char2] for upcoming fight.
CLIENT = Genclient(os.getenv('GEMINI_API'))                             #genclient class for API calling
DATA = ServerData(CLIENT)                                               #Data handling class
FROZEN = False                                                          #For freezing the timer

def is_champion(status):
    if re.findall("Champion", status) and not re.findall("Former", status):
        return True
    else:
        return False

##################################
#         DEBUG HANDLERS         #
##################################

@app.route('/api/debug/skip', methods=['POST'])
def debug_skip_timer():
    if not app.debug and "localhost" not in API_URL:
        return
    global CURRENT_TIMER
    #set the timer for the next battle to start to 10 seconds
    CURRENT_TIMER = 5
    print("!-- DEBUG: SKIPPING TIMER TO 10s --!")
    return jsonify({"status": "skipped", "time_left": CURRENT_TIMER})

@app.route('/api/debug/freeze', methods=['POST'])
def debug_freeze_timer():
    if not app.debug and "localhost" not in API_URL:
        return
    global FROZEN
    FROZEN = not FROZEN
    print(f"!-- FROZEN TIMER : {FROZEN} --!")
    return jsonify({"status": "frozen", "is_frozen": FROZEN})

@app.route('/api/debug/rematch', methods=['POST'])
def debug_new_matchup():
    if not app.debug and "localhost" not in API_URL:
        return
    #schedule a new match, instantly
    schedule_next_match()
    return jsonify({"status": "rematched", "new_match": [c.name for c in NEXT_MATCH]})

@app.route('/api/debug/randomize_alignments', methods=['POST'])
def debug_randomize_alignments():
    if not app.debug and "localhost" not in API_URL:
        return jsonify({"error": "Debug mode only"}), 403
        
    count = DATA.randomize_alignments()
    return jsonify({"status": "success", "count": count, "message": "Alignments randomized!"})

##################################
#        FRONTEND HANDLERS       #
##################################

#handles frontend submission of a new character
#converts their information into JSON format using the character class
@socketio.on('submit_character')
def accept_new_character(data):
    if not data: return
    
    char_id = data.get('id')
    image_base = data.get('imageBase')
    name = data.get('name') or "???"

    # Create new DB Object
    c = Character(
        id=char_id,
        image_file=image_base,
        name=name,
        is_approved=False # Default to False (Queue)
    )
    
    db.session.add(c)
    db.session.commit()
    
    print(f"$-- NEW CHARACTER ADDED TO DB QUEUE {char_id} --$")
    emit('character_added', {'status': 'success', 'character': c.to_dict()})

#chooses two random characters for the next match and schedules them to fight
#prioritizes new characters
def schedule_next_match():
    global NEXT_MATCH
    candidates = DATA.get_candidates_for_match()
    
    if not candidates:
        print("!-- NOT ENOUGH FIGHTERS --!")
        NEXT_MATCH = None
        return

    NEXT_MATCH = candidates
    print(f"!-- NEXT MATCH: {NEXT_MATCH[0].name} vs {NEXT_MATCH[1].name} --!")

    #emit the card to clients
    socketio.emit('match_scheduled', {
        'fighters': [c.to_dict() for c in NEXT_MATCH],
        'starts_in': BATTLE_TIMER,
    })

#conduct the battle between the selected fighters. Uses the genclient for the api call
def run_scheduled_battle():
    global NEXT_MATCH
    if not NEXT_MATCH:
        return

    #run API call
    result = CLIENT.run_match(NEXT_MATCH)
    
    #initializing a new character
    if 'new_stats' in result and result['new_stats']:
        for char_id, stats_data in result['new_stats'].items():
            target = DATA.get_character(char_id)
            if target:
                # add the basic fields
                if 'name' in stats_data: target.name = stats_data.pop('name')
                if 'Name' in stats_data: target.name = stats_data.pop('Name')
                if 'description' in stats_data: target.description = stats_data.pop('description')
                if 'personality' in stats_data: target.personality = stats_data.pop('personality')
                if 'alignment' in stats_data: target.alignment = stats_data.pop('alignment')
                if 'popularity' in stats_data: target.popularity = stats_data.pop('popularity')

                #update the JSON Stats column
                #we assign a new dict to make sure SQLalchemy detects the change
                current_stats = dict(target.stats)
                current_stats.update(stats_data)
                target.stats = current_stats
                flag_modified(target, "stats") #explicitly flag JSON as modified

                print(f"Generated stats for {target.name}")

    if 'updated_stats' in result and result['updated_stats']:
        for char_id, char_data in result['updated_stats'].items():
            target = DATA.get_character(char_id)
            if target:
                print(f"$-- UPDATING CHARACTER: {char_id} --$")
                if 'alignment' in char_data: target.alignment = char_data['alignment']
                if 'popularity' in char_data: target.popularity = char_data['popularity']
                if 'personality' in char_data: target.personality = char_data['personality']

    winner_id = result.get('winner_id')
    if winner_id == NEXT_MATCH[0].id:
        winner_obj = NEXT_MATCH[0]
        loser_obj = NEXT_MATCH[1]
    else:
        winner_obj = NEXT_MATCH[1]
        loser_obj = NEXT_MATCH[0]

    title_exchange_name = None
    #does the loser have a title
    loser_titles = list(loser_obj.titles) if loser_obj.titles else []
    
    if len(loser_titles) > 0:
        #take the first title
        title_on_line = loser_titles[0]
        #remove from loser
        loser_titles.remove(title_on_line)
        loser_obj.titles = loser_titles
        flag_modified(loser_obj, "titles")
        #give to winner
        winner_titles = list(winner_obj.titles) if winner_obj.titles else []
        winner_titles.append(title_on_line)
        winner_obj.titles = winner_titles
        flag_modified(winner_obj, "titles")
        #a title has been exchanged
        title_exchange_name = title_on_line
        print(f"!-- TITLE CHANGE: {winner_obj.name} won {title_on_line} --!")
    
    #winner retains
    elif winner_obj.titles:
        title_exchange_name = False 

    winner_obj.wins += 1
    loser_obj.losses += 1
    
    DATA.commit() #save all DB changes

    #save the match to match history
    bout_teams = [[NEXT_MATCH[0]], [NEXT_MATCH[1]]]
    DATA.log_match_result(
        teams=bout_teams,
        winner=winner_obj,
        summary=result.get('summary', "Match Concluded."),
        match_type="1v1",
        title_change=title_exchange_name
    )
    #emit the result to clients
    socketio.emit('match_result', {
        'fighters': [c.to_dict() for c in NEXT_MATCH],
        'log': result.get('battle_log', []),
        'winner': winner_obj.name,
        'summary': result.get('summary', ''),
        'introduction': result.get('introduction', '')
    })
    
    print(f"$-- MATCH FINISHED - WINNER {winner_obj.name} --$")
    NEXT_MATCH = None

##################################
#        SERVER HANDLERS         #
##################################

#Grabs the current card info
@app.route('/api/card')
def return_current_card():
    global NEXT_MATCH
    current_match = NEXT_MATCH
    if current_match is None:
        return jsonify({
            'fighters': [],
            'starts_in': 0,
            'status': 'waiting'
        })
    try:
        fighters_data = [c.to_dict() for c in current_match]
        return jsonify({
            'fighters': fighters_data,
            'starts_in': BATTLE_TIMER,
            'status': 'scheduled'
        })
    except Exception as e:
        print(f"!-- ERROR SERVING CARD: {e} --!")
        return jsonify({'error': str(e)}), 500

#Creates a leaderboard by sorting the top three fighters
@app.route('/api/roster', methods=['POST'])
def return_top_fighters():
    #pagination query
    data = request.get_json()
    page = data.get('page', 1)
    per_page = 5
    
    #just sorted by descending wins for now
    pagination = Character.query.filter_by(is_approved=True).order_by(Character.wins.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify([c.to_dict() for c in pagination.items])

#Default app route
@app.route('/')
def index():
    return render_template('index.html')

#Main server loop. Timer counts down, when it hits zero
def server_loop():
    global CURRENT_TIMER, NEXT_MATCH, FROZEN
    with app.app_context():
        schedule_next_match()

    while True:
        socketio.sleep(1)
        with app.app_context():
            if len(DATA.get_queue()) > 2:
                DATA.submit_queue_for_approval()
        if not FROZEN:
            CURRENT_TIMER -= 1
            #emit the timer for clients
            socketio.emit('timer_update', {'time_left': CURRENT_TIMER,'next_match': [c.name for c in NEXT_MATCH] if NEXT_MATCH else None})
            if CURRENT_TIMER <= 0:
                with app.app_context():
                    CURRENT_TIMER = 0
                    socketio.emit('timer_update', {'time_left': CURRENT_TIMER,'next_match': [c.name for c in NEXT_MATCH] if NEXT_MATCH else None})
                    run_scheduled_battle() #run the match
                    socketio.sleep(60)     #so we see the throbber for one minute
                    CURRENT_TIMER = -1
                    socketio.emit('timer_update', {'time_left': CURRENT_TIMER,'next_match': [c.name for c in NEXT_MATCH] if NEXT_MATCH else None})
                    socketio.sleep(60)     #then scheduling announcement
                    schedule_next_match()  #schedule the next match
                CURRENT_TIMER = BATTLE_TIMER


#Starting up server, loading players and approval queue
print("!-- SERVER STARTING UP: LOADING CHARACTERS... --!")
print("!-- STARTING BATTLE LOOP... --!")
socketio.start_background_task(server_loop)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, use_reloader=False)
