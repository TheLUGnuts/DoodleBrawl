#jfr, cwf, tjc
#Created for the 2026 VCU 24HR Hackathon

import json, os, random, re
from flask_cors                                   import CORS
from components.genclient                    import Genclient
from components.character                    import Character
from dotenv                                import load_dotenv
from flask_socketio                     import SocketIO, emit
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
CHARACTERS = {}                                                         #dict of character objects
APPROVAL_QUEUE = {}                                                     #dict of submitted characters to be approved
NEXT_MATCH = None                                                       #holds the [char1, char2] for upcoming fight.
CLIENT = Genclient(os.getenv('GEMINI_API'))                             #genclient class for API calling
#Data paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  #current directory
DATA_DIR = os.path.join(BASE_DIR, 'assets/Data')                        #file ref where data is stored
IMAGE_DIR = os.path.join(BASE_DIR, 'assets/Images')                     #file ref where images are located
CHARACTER_FILE = os.path.join(DATA_DIR, 'characters.json')              #JSON file reference of character objects
QUEUE_FILE = os.path.join(DATA_DIR, 'queue.json')                       #approval queue of characters
OUTPUT_FILE = os.path.join(DATA_DIR, 'last_gen.json')                   #last generated response for debugging.
REJECTED_FILE = os.path.join(DATA_DIR, 'rejected.json')                 #file containing rejected images, their ID, and reason for rejection

##################################
#          DATA HANDLERS         #
##################################

#checks if a string has the word "Champion" and NOT "Former"
def is_champion(status):
    if re.findall("Champion", status) and not re.findall("Former", status):
        return True
    else:
        return False

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

#load the approval queue from the queue.json file
def load_queue():
    global APPROVAL_QUEUE 
    if not os.path.exists(QUEUE_FILE):
        print(f"!--- QUEUE FILE WASN'T FOUND AT {QUEUE_FILE}---!")
        return
    try:
        with open(QUEUE_FILE, 'r') as file:
            data = json.load(file)
            #create the character objects in memory form the file.
            for char_id, char_data in data.items():
                APPROVAL_QUEUE[char_id] = Character(id_or_data=char_id, data=char_data)
        print(f"$-- LOADED {len(APPROVAL_QUEUE)} CHARACTERS FOR APPROVAL QUEUE --$")
    except Exception as e:
        print(f"!-- ERROR LOADING APPROVAL QUEUE --!\n ERROR: {e}")

#save all characters to the characters.json file
def save_characters():
    try:
        data = {c_id: c.to_dict() for c_id, c in CHARACTERS.items()}
        with open(CHARACTER_FILE, 'w') as file:
            json.dump(data, file, indent=2)
        print(f"$-- CHARACTERS SAVED TO characters.json --$")
    except Exception as e:
        print(f"!-- ERROR SAVING CHARACTERS --!\n ERROR: {e}")

#save queued characters to queue.json
def save_queue():
    try:
        data = {c_id: c.to_dict() for c_id, c in APPROVAL_QUEUE.items()}
        with open(QUEUE_FILE, 'w') as file:
            json.dump(data, file, indent=2)
        print(f"$-- QUEUE SAVED TO queue.json --$")
    except Exception as e:
        print(f"!-- ERROR SAVING QUEUE --!\n ERROR: {e}")

#submit the current approval queue to the API for inappropriate content
def submit_queue_for_approval():
    global APPROVAL_QUEUE, CHARACTERS
    #only run the approval submission if theres at least 3 to add.
    if len(APPROVAL_QUEUE) < 3:
        return
    #submit the approval queue for AI approval
    results = CLIENT.submit_for_approval(APPROVAL_QUEUE)
    if not results:
        return
    ids_to_remove = []
    for char_id, decision in results.items():
        if char_id in APPROVAL_QUEUE:
            if decision.get('approved'):
                #Move to main game roster
                character = APPROVAL_QUEUE[char_id]
                CHARACTERS[char_id] = character
                print(f"$-- APPROVED: {char_id} --$")
            else:
                #Rejected, log it
                reason = decision.get('reason', 'Unknown')
                print(f"!-- REJECTED: {char_id} - Reason: {reason} --!")
                log_rejection(char_id, APPROVAL_QUEUE[char_id], reason)
            ids_to_remove.append(char_id)
    for char_id in ids_to_remove:
        del APPROVAL_QUEUE[char_id]
    save_characters()
    save_queue()

#log rejections
def log_rejection(char_id, char_obj, reason):
    rejected_data = {}
    if os.path.exists(REJECTED_FILE):
        try:
            with open(REJECTED_FILE, 'r') as f:
                rejected_data = json.load(f)
        except:
            rejected_data = {}
    #add the new rejection
    rejected_data[char_id] = {
        "id": char_id,
        "name": char_obj.name,
        "reason": reason,
        "image": char_obj.image_file # save the base64 string image
    }
    try:
        with open(REJECTED_FILE, 'w') as f:
            json.dump(rejected_data, f, indent=2)
        print(f"!-- LOGGED REJECTION FOR {char_id} --!")
    except Exception as e:
        print(f"!-- ERROR SAVING REJECTION: {e} --!")

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
    APPROVAL_QUEUE[c.id] = c
    print(f"$-- NEW CHARACTER ADDED TO APPROVAL QUEUE {data['id']} --$")
    emit('character_added', {'status': 'success', 'character': c.to_dict()})
    save_queue()

#chooses two random characters for the next match and schedules them to fight
#prioritizes new characters
def schedule_next_match():
    global NEXT_MATCH
    if len(CHARACTERS) < 2:
        print("!-- NOT ENOUGH FIGHTERS --!")
        return
    all_chars = list(CHARACTERS.values())
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
            if char_id in CHARACTERS:
                target = CHARACTERS[char_id]
                new_name = stats_data.pop('name', None) or stats_data.pop('Name', None) #Error with AI capitalizing the variable? Just being sure.
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

    winner_id = result.get('winner_id')
    if winner_id == NEXT_MATCH[0].id:
        winner_obj = NEXT_MATCH[0]
        loser_obj = NEXT_MATCH[1]
    else:
        winner_obj = NEXT_MATCH[1]
        loser_obj = NEXT_MATCH[0]

    winner_obj.wins += 1
    loser_obj.losses += 1

    #change title hands if one of them was a champion.
    if loser_obj.status and is_champion(loser_obj.status):
        title_name = loser_obj.status
        # The Winner takes the title
        winner_obj.status = title_name
        # The Loser becomes "Former <Title Name>"
        loser_obj.status = f"Former {title_name}"
        
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
    char_list = [c.to_dict() for c in CHARACTERS.values()]  # Get fighter data into list
    char_list = sorted(char_list, key=lambda x: x['wins'], reverse=True)  # Sort by wins
    char_list = char_list[char_start:char_end]  # Pull out top fighters

    return jsonify(char_list)

#Default app route
@app.route('/')
def index():
    return render_template('index.html')

#Main server loop. Timer counts down, when it hits zero
def server_loop():
    timer = BATTLE_TIMER
    with app.app_context():
        schedule_next_match()

    while True:
        socketio.sleep(1)
        if len(APPROVAL_QUEUE) >= 3:
            with app.app_context():
                submit_queue_for_approval()
        timer -= 1
        #emit the timer for clients
        socketio.emit('timer_update', {'time_left': timer,'next_match': [c.name for c in NEXT_MATCH] if NEXT_MATCH else None})
        if timer <= 0:
            with app.app_context():
                timer = 0
                socketio.emit('timer_update', {'time_left': timer,'next_match': [c.name for c in NEXT_MATCH] if NEXT_MATCH else None})
                run_scheduled_battle() #run the match
                socketio.sleep(60)     #so we see the throbber for one minute
                timer = -1
                socketio.emit('timer_update', {'time_left': timer,'next_match': [c.name for c in NEXT_MATCH] if NEXT_MATCH else None})
                socketio.sleep(60)     #then scheduling announcement
                schedule_next_match()  #schedule the next match
            timer = BATTLE_TIMER


#Starting up server, loading players and approval queue
print("!-- SERVER STARTING UP: LOADING CHARACTERS... --!")
load_characters()
load_queue()
print("!-- STARTING BATTLE LOOP... --!")
socketio.start_background_task(server_loop)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, use_reloader=False)
