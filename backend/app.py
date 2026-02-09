#jfr, cwf, tjc
#Created for the 2026 VCU 24HR Hackathon

import json, os, random, re, time, secrets
from flask_cors                                            import CORS
from components.genclient                             import Genclient
from components.character                             import Character
from components.serverdata                           import ServerData
from dotenv                                         import load_dotenv
from flask_socketio                              import SocketIO, emit
from flask             import Flask, render_template, jsonify, request

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

#Global variables
BATTLE_TIMER=180                                                        #3 minutes in seconds
CURRENT_TIMER = BATTLE_TIMER                                            #global time tracker
CHARACTERS = {}                                                         #dict of character objects
APPROVAL_QUEUE = {}                                                     #dict of submitted characters to be approved
NEXT_MATCH = None                                                       #holds the [char1, char2] for upcoming fight.
CLIENT = Genclient(os.getenv('GEMINI_API'))                             #genclient class for API calling
MATCH_HISTORY = []                                                      #the in-memory list
DATA = ServerData(CLIENT)                                               #Data handling class

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
    CURRENT_TIMER = 10
    print("!-- DEBUG: SKIPPING TIMER TO 10s --!")
    return jsonify({"status": "skipped", "time_left": CURRENT_TIMER})

@app.route('/api/debug/rematch', methods=['POST'])
def debug_new_matchup():
    if not app.debug and "localhost" not in API_URL:
        return
    #schedule a new match, instantly
    schedule_next_match()
    return jsonify({"status": "rematched", "new_match": [c.name for c in NEXT_MATCH]})

##################################
#        FRONTEND HANDLERS       #
##################################

#handles frontend submission of a new character
#converts their information into JSON format using the character class
@socketio.on('submit_character')
def accept_new_character(data):
    if not data:
        print(f"!-- NO DATA RECEIVED {data} --!")
    if not data['id']:
        print(f"!-- ID NOT FOUND IN DATA: {data} --!")
    if not data['imageBase']:
        print(f"!-- IMAGE NOT FOUND IN DATA: {data} --!")
    if not data['name']:
        char_name = "???"

    c = Character(data['id'], data['imageBase'], char_name)
    #Assumed order of the submitted character data dictionary
    #1.Image File Ref 2.Stats 3.Wins 4.Losses 5.Character Name
    DATA.approval_queue[c.id] = c
    print(f"$-- NEW CHARACTER ADDED TO APPROVAL QUEUE {data['id']} --$")
    emit('character_added', {'status': 'success', 'character': c.to_dict()})
    DATA.save_queue()

#chooses two random characters for the next match and schedules them to fight
#prioritizes new characters
def schedule_next_match():
    global NEXT_MATCH
    if len(DATA.characters) < 2:
        print("!-- NOT ENOUGH FIGHTERS --!")
        return
    all_chars = list(DATA.characters.values())
    #find new characters
    fresh_meat = [c for c in all_chars if (c.wins + c.losses) == 0]
    #prioritize new characters
    if len(fresh_meat) >= 2:
        print(f"!-- PRIORITY MATCH: FOUND {len(fresh_meat)} NEW FIGHTERS --!")
        NEXT_MATCH = random.sample(fresh_meat, 2)
    elif len(fresh_meat) == 1:
        print("!-- PRIORITY MATCH: 1 NEW FIGHTER FOUND --!")
        p1 = fresh_meat[0]
        #select a random other opponent
        veterans = [c for c in all_chars if c.id != p1.id]
        p2 = random.choice(veterans)
        NEXT_MATCH = [p1, p2]
    #select two random fighters
    else:
        NEXT_MATCH = random.sample(all_chars, 2)
    print(f"{NEXT_MATCH}")

    #send match 'card' to frontend
    socketio.emit('match_scheduled', {
        'fighters': [c.to_dict() for c in NEXT_MATCH],
        'starts_in': BATTLE_TIMER,
    })
    print(f"$-- MATCH SCHEDULED: {NEXT_MATCH[0].name} vs {NEXT_MATCH[1].name} --$")

#conduct the battle between the selected fighters. Uses the genclient for the api call
def run_scheduled_battle():
    global NEXT_MATCH
    if not NEXT_MATCH:
        return
    #run API call
    result = CLIENT.run_match(NEXT_MATCH)
    # if new stats were provided, update the character with them
    if 'new_stats' in result and result['new_stats']:
        for char_id, stats_data in result['new_stats'].items():
            if char_id in DATA.characters:
                target = DATA.characters[char_id]
                new_name = stats_data.pop('name', None) or stats_data.pop('Name', None) #Error with AI capitalizing the variable? Just being sure.
                if new_name:
                    target.name = new_name
                    print(f"Name added: {target.name} onto {target.id}")
                if 'description' in stats_data:
                    target.description = stats_data.pop('description') 
                    print(f"Updated description for {target.name}")
                target.stats = stats_data
                print(f"Updated stats for {target.name}: {target.stats}")

    if 'updated_stats' in result and result['updated_stats']:
        for char_id, char_data in result['updated_stats'].items():
            if char_id in DATA.characters:
                print(f"$-- UPDATING CHARACTER: {char_id} --$")
                DATA.characters[char_id].update_values(char_data)

    with open(OUTPUT_FILE, 'w') as file:
        json.dump(result, file, indent=2)

    winner_id = result.get('winner_id')
    if winner_id == NEXT_MATCH[0].id:
        winner_obj = NEXT_MATCH[0]
        loser_obj = NEXT_MATCH[1]
    else:
        winner_obj = NEXT_MATCH[1]
        loser_obj = NEXT_MATCH[0]

    title_exchange_name = None
    if is_champion(loser_obj.status) or is_champion(winner_obj.status):
        #if the loser was the champion, give the title to the winner
        if is_champion(loser_obj.status):
            title_exchange_name = loser_obj.status
            winner_obj.status = title_exchange_name
            loser_obj.status = f"Former {title_exchange_name}"
        else:
            title_exchange_name = False

    winner_obj.wins += 1
    loser_obj.losses += 1
    DATA.save_characters()

    bout_teams = [
        [NEXT_MATCH[0]],
        [NEXT_MATCH[1]]
    ]

    DATA.log_match_result(
        teams=bout_teams,
        winner=winner_obj,
        summary=result.get('summary', "Match Concluded."),
        match_type="1v1",
        title_change=title_exchange_name
    )

    #wrap up the match and send the result to all the clients
    socketio.emit('match_result', {
        'fighters': [c.to_dict() for c in NEXT_MATCH],
        'log': result['battle_log'],
        'winner': DATA.characters[winner_id].name,
        'summary': result['summary'],
        'introduction': result['introduction']
    })
    print(f"$-- MATCH FINISHED - WINNER {DATA.characters[winner_id].name} --$")
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
    # Number of fighters to feature on the leaderboard
    NUM_FIGHTERS = 5

    # Get page number
    data = request.get_json()
    page = data.get('page', 1)
    per_page = NUM_FIGHTERS
    #per_page = data.get('num_per_page', 5)  # Maybe use this later to give a variable number of fighters per page

    # Find indicies of characters to return
    char_start = (page - 1) * per_page
    char_end = char_start + per_page

    # Find top fighters
    char_list = [c.to_dict() for c in DATA.characters.values()]  # Get fighter data into list
    char_list = sorted(char_list, key=lambda x: (x['wins']+1)/(x['losses']+1), reverse=True)  # Sort by wins
    char_list = char_list[char_start:char_end]  # Pull out top fighters

    return jsonify(char_list)

#Default app route
@app.route('/')
def index():
    return render_template('index.html')

#Main server loop. Timer counts down, when it hits zero
def server_loop():
    global CURRENT_TIMER, NEXT_MATCH
    with app.app_context():
        schedule_next_match()

    while True:
        socketio.sleep(1)

        if len(DATA.approval_queue) >= 3:
            with app.app_context():
                DATA.submit_queue_for_approval()

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
DATA.load_characters()
DATA.load_queue()
DATA.load_history()
print("!-- STARTING BATTLE LOOP... --!")
socketio.start_background_task(server_loop)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, use_reloader=False)
