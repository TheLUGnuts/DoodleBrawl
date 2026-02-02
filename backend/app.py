#jfr, cwf, tjc
#Created for the 2026 VCU 24HR Hackathon

import json, os, random, base64
from flask_cors                                   import CORS
from components.genclient                    import Genclient
from components.character                    import Character
from dotenv                                import load_dotenv
from flask_socketio                     import SocketIO, emit
from flask             import Flask, render_template, jsonify

#################################
#          DOODLE BRAWL         #
#################################

load_dotenv()

app = Flask(__name__,
    static_folder="../Frontend/dist/assets",
    template_folder="../Frontend/dist",
    static_url_path="/assets")
#Cross Origin Resource Sharing prevention
app.config['SECRET_KEYS'] = os.getenv('SECRET_KEY')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

#Global variables
BATTLE_TIMER=180 # 3 minutes in seconds
CHARACTERS = {}                                                              #dict of character objects
NEXT_MATCH = None                                                            #holds the [char1, char2] for upcoming fight.
CLIENT = Genclient(os.getenv('GEMINI_API'))                                  #genclient class for API calling

#data paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))       #current directory
DATA_DIR = os.path.join(BASE_DIR, 'assets/Data')                             #file ref where data is stored
IMAGE_DIR = os.path.join(BASE_DIR, 'assets/Images')                          #file ref where images are located
CHARACTER_FILE = os.path.join(DATA_DIR, 'characters.json')                   #JSON file reference of character objects
OUTPUT_FILE = os.path.join(DATA_DIR, 'last_gen.json')                        #last generated response for debugging.

##################################
#          DATA HANDLERS         #
##################################

#load the characters from the characters.json file
def load_characters():
    global CHARACTERS 
    if not os.path.exists(CHARACTER_FILE):
        print(f"!--- CHARACTER FILE WASN'T FOUND AT {CHARACTER_FILE}---!")
        return
    try:
        with open(CHARACTER_FILE, 'r') as file:
            data = json.load(file)
            #create the character objects in memory form the file.
            for char_id, char_data in data.items():
                CHARACTERS[char_id] = Character(id_or_data=char_id, data=char_data)
        print(f"$-- LOADED {len(CHARACTERS)} CHARACTERS --$")
    except Exception as e:
        print(f"!-- ERROR LOADING CHARACTERS --!\n ERROR: {e}")

#save all characters to the characters.json file
def save_characters():
    try:
        data = {c_id: c.to_dict() for c_id, c in CHARACTERS.items()}
        with open(CHARACTER_FILE, 'w') as file:
            json.dump(data, file, indent=2)
        print(f"$-- CHARACTERS SAVED TO characters.json --$")
    except Exception as e:
        print(f"!-- ERROR SAVING CHARACTERS --!\n ERROR: {e}")

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
    CHARACTERS[c.id] = c
    print(f"$-- NEW CHARACTER ADDED {data['id']} with name {data['name']} --$")
    save_characters()
    emit('character_added', {'status': 'success', 'character': c.to_dict()})

#chooses two random characters for the next match and schedules them to fight
def schedule_next_match():
    global NEXT_MATCH
    if len(CHARACTERS) < 2:
        print("!-- NOT ENOUGH FIGHTERS --!")
        return
    #select 2 random characters from the characters list to fight.
    NEXT_MATCH = random.sample(list(CHARACTERS.values()), 2)
    print(f"{NEXT_MATCH}")
    #send match 'card' to frontend
    socketio.emit('match_scheduled', {
        'fighters': [c.to_dict() for c in NEXT_MATCH],
        'starts_in': BATTLE_TIMER,

    })
    print(f"$-- MATCH SCHEDULED: {NEXT_MATCH[0].name} vs {NEXT_MATCH[1].name} --$")

def run_scheduled_battle():
    global NEXT_MATCH
    if not NEXT_MATCH:
        return
    #run API call
    result = CLIENT.run_match(NEXT_MATCH)
    # if new stats were provided, update the character with them
    if 'new_stats' in result and result['new_stats']:
        for char_id, stats_data in result['new_stats'].items():
            if char_id in CHARACTERS:
                target = CHARACTERS[char_id]
                new_name = stats_data.pop('name', None) or stats_data.pop('Name', None) #Error with AI capping the variable? Just being sure.
                if new_name:
                    target.name = new_name
                    print(f"Name added: {target.name} onto {target.id}")
                if 'description' in stats_data:
                    target.description = stats_data.pop('description') 
                    print(f"Updated description for {target.name}")
                target.stats = stats_data
                print(f"Updated stats for {target.name}: {target.stats}")
    with open(OUTPUT_FILE, 'w') as file:
        json.dump(result, file, indent=2)

    #updates players win/loss
    winner_id = result.get('winner_id')
    if winner_id == NEXT_MATCH[0]:
        NEXT_MATCH[0].wins += 1
        NEXT_MATCH[1].losses += 1
    elif winner_id == NEXT_MATCH[1]:
        NEXT_MATCH[1].wins += 1
        NEXT_MATCH[0].losses += 1

    #save all updates to characters
    save_characters()

    #emit to clients
    socketio.emit('match_result', {
        'fighters': [c.to_dict() for c in NEXT_MATCH],
        'log': result['battle_log'],
        'winner': CHARACTERS[winner_id].name,
        'summary': result['summary']
    })
    print(f"$-- MATCH FINISHED - WINNER {CHARACTERS[winner_id].name} --$")
    NEXT_MATCH = None

##################################
#        SERVER HANDLERS         #
##################################

@app.route('/card')
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

@app.route('/')
def index():
    return render_template('index.html')

def battle_loop():
    timer = BATTLE_TIMER
    with app.app_context():
        schedule_next_match()
    
    if TEST:
        timer = 10

    while True:
        socketio.sleep(1)
        timer -= 1
        
        #emit the timer for clients
        socketio.emit('timer_update', {'time_left': timer,'next_match': [c.name for c in NEXT_MATCH] if NEXT_MATCH else None})
        
        if timer <= 0:
            with app.app_context():
                timer = 0
                socketio.emit('timer_update', {'time_left': timer,'next_match': [c.name for c in NEXT_MATCH] if NEXT_MATCH else None})
                run_scheduled_battle() #run the match
                timer = -1
                socketio.emit('timer_update', {'time_left': timer,'next_match': [c.name for c in NEXT_MATCH] if NEXT_MATCH else None})
                socketio.sleep(120)
                schedule_next_match()  #schedule the next match
            timer = BATTLE_TIMER

print("!-- SERVER STARTING UP: LOADING CHARACTERS... --!")
load_characters()
print("!-- STARTING BATTLE LOOP... --!")
socketio.start_background_task(battle_loop)

if __name__ == '__main__':
    TEST = True
    socketio.run(app, debug=True, port=5000, use_reloader=False)
