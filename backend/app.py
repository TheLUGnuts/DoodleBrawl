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
        db.session.execute(text("ALTER TABLE character ADD COLUMN team_name VARCHAR(32) DEFAULT ''"))
        db.session.execute(text("ALTER TABLE character ADD COLUMN status VARCHAR(16) DEFAULT 'active'"))
        db.session.execute(text("ALTER TABLE user ADD COLUMN last_login_bonus FLOAT DEFAULT 0.0"))
        db.session.execute(text("ALTER TABLE user ADD COLUMN last_submission FLOAT DEFAULT 0.0"))
        db.session.commit()
        print("!-- ADDED COLUMNS TO TABLES --!")
    except Exception:
        db.session.rollback()

#Global variables
BATTLE_TIMER=180                            #3 minutes in seconds
CURRENT_TIMER = BATTLE_TIMER                #global time tracker
NEXT_MATCH_TEAMS = []                       #holds the [char1, char2] for upcoming fight.
TEAMS_DATA = []                             #hold specific team
ALL_FIGHTERS = []                           #holds all current fighters
CLIENT = Genclient(os.getenv('GEMINI_API')) #genclient class for API calling
DATA = ServerData(CLIENT)                   #Data handling class
FROZEN = False                              #For freezing the timer
CURRENT_BETS = []                           #List of dicts like so: {'user_id': id, 'fighter_id': id, 'amount': int}
MATCH_ODDS = {}                             #dict: {fighter_id: float_odds}
CURRENT_POOL = 0                            #the betting pool for this match
NEXT_MATCH_TYPE = "1v1"

def get_matchup_names():
    if not NEXT_MATCH_TEAMS:
        return None
    if NEXT_MATCH_TYPE == '1v1':
        return [c.name for c in NEXT_MATCH_TEAMS]
    else:
        return [team[0].team_name for team in NEXT_MATCH_TEAMS]

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
    global NEXT_MATCH_TYPE, NEXT_MATCH_TEAMS
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    schedule_next_match()
    names = []
    if NEXT_MATCH_TEAMS:
        if NEXT_MATCH_TYPE == '1v1':
             names = [c.name for c in NEXT_MATCH_TEAMS]
        else:
             names = [t[0].team_name for t in NEXT_MATCH_TEAMS]
    return jsonify({"status": "rematched", "new_match": names})

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
        'teams': [],
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
    global NEXT_MATCH_TEAMS, NEXT_MATCH_TYPE, CURRENT_POOL, MATCH_ODDS, CURRENT_BETS, ALL_FIGHTERS, TEAMS_DATA
    match_type = random.choices(['1v1', '2v2'], weights=[0.9, 0.1])[0]
    candidates = DATA.get_candidates_for_match(match_type)
    
    #fallback for 2v2s is handled in serverdata.
    if not candidates:
        match_type = '1v1' if match_type == '2v2' else '2v2'
        candidates = DATA.get_candidates_for_match(match_type)
        if not candidates:
            print("!-- NO FIGHTERS AVAILABLE --!")
            NEXT_MATCH_TEAMS = []
            return

    NEXT_MATCH_TYPE = match_type
    NEXT_MATCH_TEAMS = candidates

    #initialize the teams
    #calculate the odds of either fighter winning
    #this will be used in determining the *risk* of the bet
    #initialize a starting pool of money
    #we're going to create the starting pool by summing their popularities, then multiplying it by 100.
    if match_type == "1v1":
        p1, p2 = candidates[0], candidates[1]
        ############################
        team1_data = {"id": p1.id, "name": p1.name, "members": [p1.to_dict_display()]}
        team2_data = {"id": p2.id, "name": p2.name, "members": [p2.to_dict_display()]}
        #pool / betting calcs
        ############################
        score1 = (p1.wins + 1.0) / (p1.losses + 1.0)
        score2 = (p2.wins + 1.0) / (p2.losses + 1.0)
        total = score1 + score2
        MATCH_ODDS = {p1.id: max(1.1, round(total/score1, 2)), p2.id: max(1.1, round(total/score2, 2))}
        CURRENT_POOL = (p1.popularity + p2.popularity) * 100
        ############################
        combined_fighters = [p1, p2]
    elif match_type == "2v2":
        t1_group, t2_group = candidates[0], candidates[1]
        t1_name, t2_name = t1_group[0].team_name, t2_group[0].team_name
        ############################
        team1_data = {"id": t1_name, "name": t1_name, "members": [c.to_dict_display() for c in t1_group]}
        team2_data = {"id": t2_name, "name": t2_name, "members": [c.to_dict_display() for c in t2_group]}
        #pool / betting calcs
        ############################
        score1 = sum([(f.wins+1.0)/(f.losses+1.0) for f in t1_group]) / len(t1_group)
        score2 = sum([(f.wins+1.0)/(f.losses+1.0) for f in t2_group]) / len(t2_group)
        total = score1 + score2
        MATCH_ODDS = {t1_name: max(1.1, round(total/score1, 2)), t2_name: max(1.1, round(total/score2, 2))}
        CURRENT_POOL = sum([f.popularity for f in t1_group + t2_group]) * 100
        #############################
        combined_fighters = t1_group + t2_group
    TEAMS_DATA = [team1_data, team2_data]
    ALL_FIGHTERS = [c.to_dict_display() for c in combined_fighters]
    CURRENT_BETS = []
    #jsonify({"status": "rematched", "new_match": names})
    #emit the card to clients
    socketio.emit('match_scheduled', {
        'match_type': NEXT_MATCH_TYPE,
        'teams': TEAMS_DATA,
        'fighters': ALL_FIGHTERS,
        'starts_in': BATTLE_TIMER,
        'odds': MATCH_ODDS,
        'pool': CURRENT_POOL
    })
#conduct the battle between the selected fighters. Uses the genclient for the api call
def run_scheduled_battle():
    global NEXT_MATCH_TEAMS, NEXT_MATCH_TYPE
    if not NEXT_MATCH_TEAMS:
        return 0 
    
    if NEXT_MATCH_TYPE == '1v1':
        p1 = DATA.get_character(NEXT_MATCH_TEAMS[0].id)
        p2 = DATA.get_character(NEXT_MATCH_TEAMS[1].id)
        live_teams = [[p1], [p2]]
        
        t1_id, t1_name = p1.id, p1.name
        t2_id, t2_name = p2.id, p2.name
    elif NEXT_MATCH_TYPE == '2v2':
        team1 = [DATA.get_character(f.id) for f in NEXT_MATCH_TEAMS[0]]
        team2 = [DATA.get_character(f.id) for f in NEXT_MATCH_TEAMS[1]]
        live_teams = [team1, team2]
        
        t1_id, t1_name = team1[0].team_name, team1[0].team_name
        t2_id, t2_name = team2[0].team_name, team2[0].team_name

    #run API call
    result = CLIENT.run_match(live_teams, NEXT_MATCH_TYPE)
    
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

    winner_id_str = result.get('winner_id', '')
    if winner_id_str == t1_id or (NEXT_MATCH_TYPE == '1v1' and winner_id_str == live_teams[0][0].id):
        winner_team, loser_team = live_teams[0], live_teams[1]
        winner_name, winner_id = t1_name, t1_id
    else:
        winner_team, loser_team = live_teams[1], live_teams[0]
        winner_name, winner_id = t2_name, t2_id

    # Title Logic (1v1s ONLY)
    title_exchange_name = None
    if NEXT_MATCH_TYPE == '1v1' and loser_team[0].titles:
        title_on_line = loser_team[0].titles[0]
        loser_team[0].titles.remove(title_on_line)
        flag_modified(loser_team[0], "titles")
        winner_team[0].titles.append(title_on_line)
        flag_modified(winner_team[0], "titles")
        title_exchange_name = title_on_line
    #update win/loss records
    for f in winner_team: f.wins += 1
    for f in loser_team: f.losses += 1
    #run payouts
    total_payout = 0
    for bet in CURRENT_BETS:
        if bet['fighter_id'] == winner_id:
            user = User.query.get(bet['user_id'])
            if user:
                payout = int(bet['amount'] * MATCH_ODDS[winner_id])
                user.money += payout
                total_payout += payout

    #distribute manager cuts
    remaining_pool = max(0, CURRENT_POOL - total_payout)
    if remaining_pool > 0:
        win_cut, lose_cut = int(remaining_pool * 0.10), int(remaining_pool * 0.05)
        for f in winner_team:
            if f.manager_id and f.manager_id != "None":
                mgr = User.query.get(f.manager_id)
                if mgr: mgr.money += win_cut
        for f in loser_team:
            if f.manager_id and f.manager_id != "None":
                mgr = User.query.get(f.manager_id)
                if mgr: mgr.money += lose_cut

    DATA.commit()
    DATA.log_match_result(live_teams, winner_team[0], result.get('summary', ''), NEXT_MATCH_TYPE, title_exchange_name)

    teams_data = [
        {"id": t1_id, "name": t1_name, "members": [c.to_dict_display() for c in live_teams[0]]},
        {"id": t2_id, "name": t2_name, "members": [c.to_dict_display() for c in live_teams[1]]}
    ]
    
    flat_fighters = [c.to_dict_display() for sublist in live_teams for c in sublist]

    socketio.emit('match_result', {
        'match_type': NEXT_MATCH_TYPE,
        'teams': teams_data,
        'fighters': flat_fighters,
        'log': result.get('battle_log', []),
        'winner': winner_name,
        'winner_id': winner_id,
        'summary': result.get('summary', ''),
        'introduction': result.get('introduction', '')
    })
    
    NEXT_MATCH_TEAMS = []
    return len(result.get('battle_log', []))

##################################
#        SERVER HANDLERS         #
##################################

#socketio.emit('match_scheduled', {
#        'match_type': NEXT_MATCH_TYPE,
#        'teams': [team1_data, team2_data],
#        'fighters': [c.to_dict_display() for c in combined_fighters],
#        'starts_in': BATTLE_TIMER,
#        'odds': MATCH_ODDS,
#        'pool': CURRENT_POOL
#    })
#Grabs the current card info
#jsonify({"status": "rematched", "new_match": names})
@app.route('/api/card')
def return_current_card():
    global NEXT_MATCH_TEAMS, MATCH_ODDS, CURRENT_POOL, CURRENT_TIMER, TEAMS_DATA, ALL_FIGHTERS
    current_match = NEXT_MATCH_TEAMS

    if current_match is None:
        return jsonify({
            'fighters': [],
            'starts_in': 0,
            'status': 'waiting',
            'odds': {},
            'pool': 0
        })
    try:
        return jsonify({
            'match_type': NEXT_MATCH_TYPE,
            'teams': TEAMS_DATA,
            'fighters': ALL_FIGHTERS,
            'status': 'scheduled',
            'starts_in': BATTLE_TIMER,
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
    global CURRENT_TIMER, NEXT_MATCH_TEAMS, FROZEN
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
            next_names = get_matchup_names()
            socketio.emit('timer_update', {'time_left': CURRENT_TIMER,'next_match': next_names})
            if CURRENT_TIMER <= 0:
                with app.app_context():
                    CURRENT_TIMER = 0
                    socketio.emit('timer_update', {'time_left': CURRENT_TIMER,'next_match': next_names})
                    log_count = run_scheduled_battle() #run the match
                    if log_count is None: log_count = 0
                    #7 is for the duration of the introduction, three seconds for each log in the match, then 30 seconds to see the result.
                    animation_duration = 7 + (log_count * 3) + 30
                    socketio.sleep(animation_duration)     #so we see the throbber for one minute
                    CURRENT_TIMER = -1
                    socketio.emit('timer_update', {'time_left': CURRENT_TIMER,'next_match': next_names})
                    socketio.sleep(10)     #then scheduling announcement
                    schedule_next_match()  #schedule the next match
                CURRENT_TIMER = BATTLE_TIMER


#Starting up server, loading players and approval queue
print("!-- SERVER STARTING UP: LOADING CHARACTERS... --!")
print("!-- STARTING BATTLE LOOP... --!")
socketio.start_background_task(server_loop)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, use_reloader=False)
