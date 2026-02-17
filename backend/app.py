#jfr, cwf, tjc
#Created for the 2026 VCU 24HR Hackathon

import os, re, time, random
from flask_cors                                                    import CORS
from components.genclient                                     import Genclient
from components.public                                        import public_bp
from components.account                                      import account_bp
from components.serverdata                                   import ServerData
from sqlalchemy                                              import case, text
from components.account                                      import account_bp
from components.serverdata                                   import ServerData
from dotenv                                                 import load_dotenv
from sqlalchemy.orm.attributes                            import flag_modified
from flask_socketio                                      import SocketIO, emit
from components.dbmodel                      import db, Character, User, Match
from components.debug                     import debug_bp, is_admin_authorized
from flask                     import Flask, render_template, jsonify, request


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
#Initialize our flask blueprints for API decomposition
app.register_blueprint(account_bp, url_prefix='/api/account')
app.register_blueprint(debug_bp, url_prefix='/api/debug')
app.register_blueprint(public_bp, url_prefix='/api')
db.init_app(app)

#this is to add a new column to the user table.
#this is used for safe migration of rows into the updated database.
with app.app_context():
    db.create_all()
    try:
        #NOTE - Whenever a new column is added make sure it GOES ON TOP! Otherwise it'll throw a normally harmless "duplicate column" error and never add the next ones.
        db.session.execute(text("ALTER TABLE character ADD COLUMN status VARCHAR(16) DEFAULT 'active'"))
        db.session.execute(text("ALTER TABLE user ADD COLUMN last_login_bonus FLOAT DEFAULT 0.0"))
        db.session.execute(text("ALTER TABLE user ADD COLUMN last_submission FLOAT DEFAULT 0.0"))
        db.session.commit()
        print("!-- ADDED COLUMNS TO TABLES --!")
    except Exception:
        db.session.rollback()
    try:
        db.session.execute(text("UPDATE character SET manager_id = creator_id WHERE manager_id = 'None' OR manager_id IS NULL"))
        db.session.commit()
        print("!-- BACKFILLED MANAGER IDs FOR EXISTING CHARACTERS --!")
    except Exception as e:
        db.session.rollback()
        print(f"!-- ERROR BACKFILLING MANAGERS: {e} --!")

#Global variables
BATTLE_TIMER=180                            #3 minutes in seconds
CURRENT_TIMER = BATTLE_TIMER                #global time tracker
NEXT_MATCH = None                           #holds the [char1, char2] for upcoming fight.
CLIENT = Genclient(os.getenv('GEMINI_API')) #genclient class for API calling
DATA = ServerData(CLIENT)                   #Data handling class
FROZEN = False                              #For freezing the timer
CURRENT_BETS = []                           #List of dicts like so: {'user_id': id, 'fighter_id': id, 'amount': int}
MATCH_ODDS = {}                             #dict: {fighter_id: float_odds}
CURRENT_POOL = 0                            #the betting pool for this match

##################################
#         DEBUG HANDLERS         #
##################################

@app.route('/api/debug/skip', methods=['POST'])
def debug_skip_timer():
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    global CURRENT_TIMER
    #set the timer for the next battle to start to 5 seconds
    CURRENT_TIMER = 5
    print("!-- DEBUG: SKIPPING TIMER TO 5s --!")
    return jsonify({"status": "skipped", "time_left": CURRENT_TIMER})

@app.route('/api/debug/freeze', methods=['POST'])
def debug_freeze_timer():
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    global FROZEN
    FROZEN = not FROZEN
    print(f"!-- FROZEN TIMER : {FROZEN} --!")
    return jsonify({"status": "frozen", "is_frozen": FROZEN})

@app.route('/api/debug/rematch', methods=['POST'])
def debug_new_matchup():
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    #schedule a new match, instantly
    schedule_next_match()
    return jsonify({"status": "rematched", "new_match": [c.name for c in NEXT_MATCH]})

@app.route('/api/debug/randomize_alignments', methods=['POST'])
def debug_randomize_alignments():
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    count = DATA.randomize_alignments()
    return jsonify({"status": "success", "count": count, "message": "Alignments randomized!"})

#test all actions
@app.route('/api/debug/test_actions', methods=['POST'])
def debug_test_actions():
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    #grab any two approved fighters
    chars = Character.query.filter_by(is_approved=True).limit(2).all()
    if len(chars) < 2:
        return jsonify({"error": "Need at least 2 fighters in DB."}), 400
    p1, p2 = chars[0], chars[1]
    #pause the arena timer momentarily
    global FROZEN
    FROZEN = True
    #scripted sequence to showcase all actions
    test_log = [
        { "actor": p1.name, "action": "ATTACK", "description": f"{p1.name} throws a basic <span class='action-red'>attack</span>!" },
        { "actor": p2.name, "action": "DODGE", "description": f"{p2.name} swiftly <span class='action-blue'>dodges</span> the attack!" },
        { "actor": p1.name, "action": "RECOVER", "description": f"{p1.name} steps back to <span class='action-green'>recover</span> HP." },
        { "actor": p2.name, "action": "POWER", "description": f"{p2.name} winds up a <span class='action-purple'>powerful</span> strike!" },
        { "actor": p1.name, "action": "AGILITY", "description": f"{p1.name} performs an <span class='action-orange'>acrobatic</span> flip!" },
        { "actor": p2.name, "action": "ULTIMATE", "description": f"{p2.name} channels raw magical energy for an <span class='action-rainbow'>ULTIMATE</span> attack!" }
    ]
    #emit to clients.
    socketio.emit('match_result', {
        'fighters': [p1.to_dict_display(), p2.to_dict_display()],
        'log': test_log,
        'winner': p2.name,
        'winner_id': p2.id,
        'summary': "This was a simulated debug showcase of all combat animations!",
        'introduction': "Welcome to the Action Animation Showcase!"
    })
    return jsonify({"status": "success", "message": "Triggered UI Action Showcase. Timer frozen."})

##################################
#        FRONTEND HANDLERS       #
##################################

#handles a user placing a bet
#a bet requires three things:
#1. A consideration (your stake in the bet)
#2. A risk (the chance)
#3. A prize
#We are using the pari-mutuel sportsbook style.
#this means we have a starting house pool, then the pool largens as people place bets.
@socketio.on("place_bet")
def handle_bet(data):
    global CURRENT_POOL, CURRENT_BETS, MATCH_ODDS
    user_id = data.get('user_id')
    fighter_id = data.get('fighter_id')
    amount = int(data.get('amount', 0))

    if amount <= 0:
        return {'status': 'error', 'message': 'Invalid bet amount.'}
    user = User.query.get(user_id)
    if not user or user.money < amount:
        return {'status': 'error', 'message': 'Insufficient funds!'}
    
    odds = MATCH_ODDS.get(fighter_id, 1.1)

    #liability is how much we must payout. We have to calculate this so nobody goes over the pool and loses money.
    current_fighter_liability = sum(b['amount'] for b in CURRENT_BETS if b['fighter_id'] == fighter_id) * odds
    new_total_liability = current_fighter_liability + (amount * odds)
    #bets must NOT make us exceed total liability
    if new_total_liability > (CURRENT_POOL + amount):
        safe_divisor = max(0.1, odds - 1.0) #prevent division by zero
        max_add = int((CURRENT_POOL - current_fighter_liability) / safe_divisor)
        return {
            'status': 'error', 
            'message': f'The prize pool is too small to cover that payout! Maximum additional wager: ${max(0, max_add)}'
        }

    #apply bet
    existing_bet = next((b for b in CURRENT_BETS if b['user_id'] == user_id), None)
    
    if existing_bet:
        # prevent "hedging" the bet
        if existing_bet['fighter_id'] != fighter_id:
            return {'status': 'error', 'message': 'You cannot bet on both fighters!'}
        user.money -= amount
        existing_bet['amount'] += amount
        total_bet_amount = existing_bet['amount']
    else:
        user.money -= amount
        CURRENT_BETS.append({
            'user_id': user.id,
            'fighter_id': fighter_id,
            'amount': amount
        })
        total_bet_amount = amount

    CURRENT_POOL += amount
    db.session.commit()
    print(f"$-- BET PLACED BY {user.username} OF {amount} ON {fighter_id}! --$")
    emit('pool_update', {'pool': CURRENT_POOL}, broadcast=True)
    return {
        'status': 'success', 
        'new_balance': user.money, 
        'total_wagered': total_bet_amount 
    }

#handles frontend submission of a new character
#converts their information into JSON format using the character class
@socketio.on('submit_character')
def accept_new_character(data):
    if not data: return
    
    #log in
    creator_id = data.get('creator_id')
    if not creator_id or creator_id == "Unknown":
        return {'status': 'error', 'message': 'You must be logged in to submit a fighter!'}
    #valid user
    user = User.query.get(creator_id)
    if not user:
        return {'status': 'error', 'message': 'Invalid user account.'}
    #pay up
    if user.money < 100:
        return {'status': 'error', 'message': 'Insufficient funds! Submitting a fighter costs $100.'}
    
    time_since_last = time.time() - user.last_submission
    if time_since_last < 300:
        remaining = int(300 - time_since_last)
        minutes, seconds = divmod(remaining, 60)
        return {
            'status': 'error', 
            'message': f'Cooldown active! Please wait {minutes}m {seconds}s before submitting another fighter.'
        }
    
    char_id = data.get('id')
    image_base = data.get('imageBase')
    name = data.get('name') or "???"

    #create new DB Object
    c = Character(
        id=char_id,
        image_file=image_base,
        name=name,
        creator_id=creator_id if creator_id else "Unknown",
        manager_id=creator_id if creator_id else "None", 
        status="active",
        is_approved=False #is_approved=False means it will be put into the approval queue.
    )
    
    user.last_submission = time.time()
    user.money -= 100

    db.session.add(c)
    db.session.commit()
    
    print(f"$-- NEW CHARACTER ADDED TO DB QUEUE {char_id} --$")
    emit('character_added', {'status': 'success', 'character': c.to_dict()})

#chooses two random characters for the next match and schedules them to fight
#prioritizes new characters
def schedule_next_match():
    global NEXT_MATCH, CURRENT_POOL, MATCH_ODDS, CURRENT_BETS
    candidates = DATA.get_candidates_for_match()
    
    if not candidates:
        print("!-- NOT ENOUGH FIGHTERS --!")
        NEXT_MATCH = None
        return

    NEXT_MATCH = candidates
    print(f"!-- NEXT MATCH: {NEXT_MATCH[0].name} vs {NEXT_MATCH[1].name} --!")

    p1 = DATA.get_character(NEXT_MATCH[0].id)
    p2 = DATA.get_character(NEXT_MATCH[1].id)
    #calculate the odds of either fighter winning
    #this will be used in determining the *risk* of the bet
    score1 = (p1.wins + 1.0) / (p1.losses + 1.0)
    score2 = (p2.wins + 1.0) / (p2.losses + 1.0)
    total_score = score1 + score2
    odds1 = max(1.1, round(total_score / score1, 2))
    odds2 = max(1.1, round(total_score / score2, 2))
    MATCH_ODDS = {p1.id : odds1, p2.id : odds2}
    
    #initialize a starting pool of money
    #we're going to create the starting pool by summing their popularities, then multiplying it by 10.
    p1_popularity = p1.popularity if p1.popularity else 1
    p2_popularity = p2.popularity if p2.popularity else 1
    total_popularity = p1_popularity + p2_popularity
    CURRENT_POOL = total_popularity * 100
    CURRENT_BETS = []

    #emit the card to clients
    socketio.emit('match_scheduled', {
        'fighters': [c.to_dict_display() for c in NEXT_MATCH],
        'starts_in': BATTLE_TIMER,
        'odds': MATCH_ODDS,
        'pool': CURRENT_POOL
    })

#conduct the battle between the selected fighters. Uses the genclient for the api call
def run_scheduled_battle():
    global NEXT_MATCH
    if not NEXT_MATCH:
        return 0 
    
    p1 = DATA.get_character(NEXT_MATCH[0].id)
    p2 = DATA.get_character(NEXT_MATCH[1].id)
    
    if not p1 or not p2:
        print("!-- ERROR: Fighters not in DB? --!")
        return
    live_match = [p1, p2]

    #run API call
    result = CLIENT.run_match(live_match)
    
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
    if winner_id == p1.id:
        winner_obj = p1
        loser_obj = p2
    else:
        winner_obj = p2
        loser_obj = p1

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

    #Resolving wagers
    for bet in CURRENT_BETS:
        if bet['fighter_id'] == winner_obj.id:
            user = User.query.get(bet['user_id'])
            if user:
                payout = int(bet['amount'] * MATCH_ODDS[winner_obj.id])
                user.money += payout
                print(f"$-- USER {user.username} HAS WON ${payout}! --$")
    
    DATA.commit() #save all DB changes

    #save the match to match history
    bout_teams = [[p1], [p2]]
    DATA.log_match_result(
        teams=bout_teams,
        winner=winner_obj,
        summary=result.get('summary', "Match Concluded."),
        match_type="1v1",
        title_change=title_exchange_name
    )
    #emit the result to clients
    socketio.emit('match_result', {
        'fighters': [c.to_dict_display() for c in live_match],
        'log': result.get('battle_log', []),
        'winner': winner_obj.name,
        'winner_id': winner_obj.id,
        'summary': result.get('summary', ''),
        'introduction': result.get('introduction', '')
    })
    
    print(f"$-- MATCH FINISHED - WINNER {winner_obj.name} --$")
    NEXT_MATCH = None
    #return the number of logs to the server so we can allocate enough time for the match to play out.
    return len(result.get('battle_log', []))

##################################
#        SERVER HANDLERS         #
##################################

#Grabs the current card info
@app.route('/api/card')
def return_current_card():
    global NEXT_MATCH, MATCH_ODDS, CURRENT_POOL, CURRENT_TIMER
    current_match = NEXT_MATCH
    if current_match is None:
        return jsonify({
            'fighters': [],
            'starts_in': 0,
            'status': 'waiting',
            'odds': {},
            'pool': 0
        })
    try:
        fighters_data = [c.to_dict_display() for c in current_match]
        return jsonify({
            'fighters': fighters_data,
            'starts_in': BATTLE_TIMER,
            'status': 'scheduled',
            'odds': MATCH_ODDS,
            'pool': CURRENT_POOL
        })
    except Exception as e:
        print(f"!-- ERROR SERVING CARD: {e} --!")
        return jsonify({'error': str(e)}), 500
    
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
                    log_count = run_scheduled_battle() #run the match
                    if log_count is None: log_count = 0
                    #7 is for the duration of the introduction, three seconds for each log in the match, then 30 seconds to see the result.
                    animation_duration = 7 + (log_count * 3) + 30
                    socketio.sleep(animation_duration)     #so we see the throbber for one minute
                    CURRENT_TIMER = -1
                    socketio.emit('timer_update', {'time_left': CURRENT_TIMER,'next_match': [c.name for c in NEXT_MATCH] if NEXT_MATCH else None})
                    socketio.sleep(10)     #then scheduling announcement
                    schedule_next_match()  #schedule the next match
                CURRENT_TIMER = BATTLE_TIMER


#Starting up server, loading players and approval queue
print("!-- SERVER STARTING UP: LOADING CHARACTERS... --!")
print("!-- STARTING BATTLE LOOP... --!")
socketio.start_background_task(server_loop)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, use_reloader=False)
