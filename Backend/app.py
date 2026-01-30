#jfr, cwf, tjc

import json, os, random, time, base64
from components import character
from google import genai
from flask_cors import CORS
from dotenv import load_dotenv
from google.genai import types, errors
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

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
API_KEY = os.getenv('GEMINI_API') 

BATTLE_INTREVAL=300 # 5 minutes in seconds

#data paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))       #current directory
DATA_DIR = os.path.join(BASE_DIR, 'assets/Data')            #file ref where data is stored
IMAGE_DIR = os.path.join(BASE_DIR, 'assets/Images')         #file ref where images are located
CHARACTER_FILE = os.path.join(DATA_DIR, 'characters.json')  #JSON file reference of character objects
characters = {}                                             #dict of character objects
NEXT_MATCH = None                                           #holds the [char1, char2] for upcoming fight.

##################################
#           GEMINI API           #
##################################

#FIXME Update move types.
SYSTEM_PROMPT = """
You are the "Doodle Brawl" Game Engine. Your goal is to simulate a turn-based battle between two characters to 0 HP.

### PHASE 1: STAT GENERATION
Analyze the provided images for both fighters.
IF a fighter has `fight_count: 0` (stats are empty/null), you MUST generate stats based on their visual appearance:
1.  **HP (50-200):** Low for small/fragile, High for big/armored. (Avg 100)
2.  **AGILITY (1-10):** Low for heavy/clunky, High for sleek/athletic. (Avg 5)
3.  **POWER (1-20):** Low for weak, High for dangerous/weapon-wielding. (Avg 10)

### PHASE 2: COMBAT SIMULATION
Simulate the fight turn-by-turn until one reaches 0 HP.
* **Agility Rule:** If Agility > 6, that character has a 30% chance to perform a "Combo" (2 actions in one turn) or "Dodge" (negate damage).
* **Move Types:**
    * `ATTACK`: Standard hit (Power +/- variance).
    * `RECOVER`: Recover HP (rare).
    * ``

### OUTPUT FORMAT
Return strictly valid JSON.
{
    "new_stats": {
        "ID_OF_CHAR": { "hp": 120, "agility": 3, "power": 15 } 
        // Only include keys for characters that needed NEW stats generated.
    },
    "battle_log": [
        { 
            "actor": "Name", 
            "action": "ATTACK", 
            "target": "Name", 
            "damage": 12, 
            "description": "Threw a wild punch!",
            "remaining_hp": 88
        },
        ...
    ],
    "winner_id": "ID_OF_WINNER"
}
"""

#loads image from disk to be sent to gemini API
def get_character_image_part(filename):
    path = os.path.join(IMAGE_DIR, filename)
    if not os.path.exists(path):
        return None
    
    with open(path, "rb") as f:
        image_data = f.read()
    
    #return it in the png format the api needs
    return types.Part.from_bytes(data=image_data, mime_type="image/png")

generation_config = types.GenerateContentConfig(
    temperature=1,                         #boilerplate
    top_p=0.95,                            #boilerplate(?)
    top_k=64,                              #boilerplate(?)
    max_output_tokens=10240,               #arbitrary number (2^)
    responses_mime_type="application/json" #return your response as a legal JSON format
    system_instruction=SYSTEM_PROMPT
)

##################################
#          DATA HANDLERS         #
##################################

#load the characters from the characters.json file
def load_characters():
    global characters 
    if not os.path.exists(CHARACTER_FILE):
        print(f"!--- CHARACTER FILE WASN'T FOUND AT {CHARACTER_FILE}---!")
        return
    try:
        with open(CHARACTER_FILE, 'r') as file:
            data = json.load(file)
            #create the character objects in memory form the file.
            for char_id, char_data in data.items():
                characters[char_id] = Character(char_data)
        print(f"$-- LOADED {len(characters)} CHARACTERS --$")
    except Exception as e:
        print(f"!-- ERROR LOADING CHARACTERS --!\n ERROR: {e}")

#save all characters to the characters.json file
def save_characters():
    try:
        data = {c_id: c.to_dict() for c_id, c in characters.items()}
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

    if 'id' not in data:
        data['id'] = str(len(characters) + 1)

    c = Character(data)
    #Assumed order of the submitted character data dictionary
    #1.Image File Ref 2.Stats 3.Wins 4.Losses 5.Character Name
    characters[c.id] = c
    save_characters()
    emit('character_added', {'status': 'success', 'character': c.to_dict()})

#chooses two random characters for the next match and schedules them to fight
def schedule_next_match():
    global NEXT_MATCH
    if len(characters) < 2:
        print("!-- NOT ENOUGH FIGHTERS --!")
        return
    #select 2 random characters from the characters list to fight.
    NEXT_MATCH = random.sample(list(characters.values()), 2)
    
    #send match 'card' to frontend
    socketio.emit('match_scheduled', {
        'fighters': [c.to_dict() for c in NEXT_MATCH],
        'starts_in': BATTLE_INTERVAL
    })
    print(f"$-- MATCH SCHEDULED: {NEXT_MATCH[0].name} vs {NEXT_MATCH[1].name} --$")

def run_scheduled_battle():
    global NEXT_MATCH
    if not NEXT_MATCH:
        return

    p1, p2 = NEXT_MATCH
    print(f"!-- RUNNING BATTLE: {p1.name} vs {p2.name} --!")

    #battle information to be sent to gemini API
    request_content = [
        f"""
        FIGHTER 1:
        ID: {p1.id}
        Name: {p1.name}
        Current Stats: {p1.stats} (If empty, generate them based on attached image)
        Fight Count: {p1.wins + p1.losses}
        """,
        get_character_image_part(p1.image_file), #fighter 1 drawing
        
        f"""
        FIGHTER 2:
        ID: {p2.id}
        Name: {p2.name}
        Current Stats: {p2.stats} (If empty, generate them based on attached image)
        Fight Count: {p2.wins + p2.losses}
        """,
        get_character_image_part(p2.image_file)  #fighter 2 drawing
    ]

    try:
        #send API call to gemini
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=request_content,
            config=generation_config
        )
        
        result = json.loads(response.text)
        
        # if new stats were provided, update the character with them
        if 'new_stats' in result and result['new_stats']:
            for char_id, new_stats in result['new_stats'].items():
                if char_id in characters:
                    characters[char_id].stats = new_stats
                    print(f"Updated stats for {characters[char_id].name}: {new_stats}")
            save_characters()

        #updates players win/loss
        winner_id = result.get('winner_id')
        if winner_id == p1.id:
            p1.wins += 1
            p2.losses += 1
        elif winner_id == p2.id:
            p2.wins += 1
            p1.losses += 1
        save_characters()

        #emit to clients
        socketio.emit('battle_result', {
            'fighters': [p1.to_dict(), p2.to_dict()],
            'log': result['battle_log'],
            'winner': winner_id
        })

    except Exception as e:
        print(f"!-- BATTLE ERROR: {e}")
    
    #clear the match
    NEXT_MATCH = None

def apply_character_updates():
    pass

##################################
#        SERVER HANDLERS         #
##################################

@app.route('/')
def index():
    return render_template('index.html')

def battle_loop():
    timer = BATTLE_INTERVAL
    with app.app_context():
        schedule_next_match()

    while True:
        socketio.sleep(1)
        timer -= 1
        
        #emit the timer for clients
        socketio.emit('timer_update', {
            'time_left': timer,
            'next_match': [c.name for c in NEXT_MATCH] if NEXT_MATCH else None
        })
        
        if timer <= 0:
            with app.app_context():
                run_scheduled_battle() #run the match
                schedule_next_match()  #schedule the next match
            timer = BATTLE_INTERVAL

if __name__ == '__main__':
    load_characters()
    #start battle loop
    socketio.start_background_task(battle_loop)
    socketio.run(app, debug=True, port=5000)


