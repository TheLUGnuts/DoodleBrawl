#jfr, cwf, tjc
#Created for the 2026 VCU 24HR Hackathon

import os, re, time, random
from flask_cors                                                    import CORS
from components.genclient                                     import Genclient
from sqlalchemy                                              import case, text
from components.account                                      import account_bp
from components.serverdata                                   import ServerData
from dotenv                                                 import load_dotenv
from sqlalchemy.orm.attributes                            import flag_modified
from flask_socketio                                      import SocketIO, emit
from components.dbmodel                      import db, Character, User, Match
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
app.register_blueprint(account_bp, url_prefix='/api/account')
db.init_app(app)

#this is to add a new column to the user table.
#this is used for safe migration of rows into the updated database.
with app.app_context():
    db.create_all()
    try:
        db.session.execute(text("ALTER TABLE user ADD COLUMN last_login_bonus FLOAT DEFAULT 0.0"))
        db.session.execute(text("ALTER TABLE user ADD COLUMN last_submission FLOAT DEFAULT 0.0"))
        db.session.commit()
        print("!-- ADDED COLUMNS TO USER TABLE --!")
    except Exception:
        db.session.rollback()

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

def is_champion(status):
    if re.findall("Champion", status) and not re.findall("Former", status):
        return True
    else:
        return False

##################################
#         DEBUG HANDLERS         #
##################################

#see if an incoming debug api request is from an admin
def is_admin_authorized():
    #if local development, bypass this
    if app.debug or "localhost" in API_URL:
        return True
        
    admin_ids = [i.strip() for i in os.getenv('ADMIN_IDS', '').split(',') if i.strip()]
    user_id = request.headers.get('X-User-ID')
    
    return user_id and user_id in admin_ids

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

#returns all characters, approved or not.
@app.route('/api/debug/characters', methods=['GET'])
def debug_get_characters():
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    chars = Character.query.all()
    #FIXME
    #THIS MAY BE VERY INEFFICIENT
    #this returns the base64 image of every single character in the roster
    #if we have a lot of fighters, this may be extremely bloated.
    return jsonify([c.to_dict_debug() for c in chars])

#edit the database entry of any character
@app.route('/api/debug/character/<char_id>', methods=['POST'])
def debug_update_character(char_id):
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    char = Character.query.get(char_id)
    
    if not char:
        return jsonify({"error": "Character not found"}), 404
        
    try:
        if 'name' in data: char.name = data['name']
        if 'description' in data: char.description = data['description']
        if 'alignment' in data: char.alignment = data['alignment']
        if 'popularity' in data: char.popularity = int(data['popularity'])
        if 'wins' in data: char.wins = int(data['wins'])
        if 'losses' in data: char.losses = int(data['losses'])
        if 'personality' in data: char.personality = data['personality']
        if 'is_approved' in data: char.is_approved = bool(data['is_approved'])
        if 'creator_id' in data: char.creator_id = data['creator_id']
        if 'creation_time' in data: char.creation_time = float(data['creation_time'])
        
        # Handle JSON fields explicitly
        if 'stats' in data: 
            char.stats = data['stats']
            flag_modified(char, "stats")
        if 'titles' in data:
            char.titles = data['titles']
            flag_modified(char, "titles")

        db.session.commit()
        print(f"!-- DEBUG: UPDATED CHARACTER {char.name} --!")
        return jsonify({"status": "success", "message": f"Updated {char.name}"})
        
    except Exception as e:
        db.session.rollback()
        print(f"!-- DEBUG UPDATE ERROR: {e} --!")
        return jsonify({"error": str(e)}), 500

#grabs all user accounts for the debug editor
@app.route('/api/debug/users', methods=['GET'])
def debug_get_users():
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403 
    users = User.query.all()
    #No to_dict method, so we just build it right here.
    #NOTE - It'd be simple to just add a to_dict to User.
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "money": u.money,
        "creation_time": u.creation_time,
        "last_submission": u.last_submission,
        "last_login_bonus": u.last_login_bonus,
        "portrait": u.portrait
    } for u in users])

#update a users database row
@app.route('/api/debug/user/<user_id>', methods=['POST'])
def debug_update_user(user_id):
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403 
    data = request.get_json()
    u = User.query.get(user_id)
    
    if not u:
        return jsonify({"error": "User not found"}), 404
        
    try:
        if 'username' in data: u.username = data['username']
        if 'money' in data: u.money = int(data['money'])
        if 'creation_time' in data: u.creation_time = float(data['creation_time'])
        if 'last_submission' in data: u.last_submission = float(data['last_submission'])
        if 'portrait' in data: u.portrait = data['portrait']

        db.session.commit()
        print(f"!-- DEBUG: UPDATED USER {u.username} --!")
        return jsonify({"status": "success", "message": f"Updated {u.username}"})
        
    except Exception as e:
        db.session.rollback()
        print(f"!-- DEBUG UPDATE ERROR: {e} --!")
        return jsonify({"error": str(e)}), 500

#grab matches from the matches table in the database
@app.route('/api/debug/matches', methods=['GET'])
def debug_get_matches():
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    matches = Match.query.order_by(Match.timestamp.desc()).all()
    return jsonify([m.to_dict_debug() for m in matches])

#grab information from a match in the match table
@app.route('/api/debug/match/<match_id>', methods=['POST'])
def debug_update_match(match_id):
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    m = Match.query.get(match_id)
    if not m: return jsonify({"error": "Match not found"}), 404
    try:
        if 'summary' in data: m.summary = data['summary']
        if 'winner_name' in data: m.winner_name = data['winner_name']
        if 'winner_id' in data: m.winner_id = data['winner_id']
        if 'match_type' in data: m.match_type = data['match_type']
        if 'is_title_bout' in data: m.is_title_bout = bool(data['is_title_bout'])
        if 'title_exchanged' in data: m.title_exchanged = data['title_exchanged']
        
        if 'match_data' in data:
            m.match_data = data['match_data']
            flag_modified(m, "match_data")
            
        db.session.commit()
        return jsonify({"status": "success", "message": f"Updated Match {m.id}"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug/<table_type>/<item_id>', methods=['DELETE'])
def debug_delete_item(table_type, item_id):
    if not is_admin_authorized(): return jsonify({"error": "Unauthorized"}), 403
    try:
        #route deletion to correct database table
        if table_type == 'character': item = Character.query.get(item_id)
        elif table_type == 'user': item = User.query.get(item_id)
        elif table_type == 'match': item = Match.query.get(item_id)
        else: return jsonify({"error": "Invalid table type"}), 400

        if not item: return jsonify({"error": "Item not found"}), 404
        
        db.session.delete(item)
        db.session.commit()
        print(f"!-- DEBUG: DELETED {table_type.upper()} {item_id} --!")
        return jsonify({"status": "success", "message": f"Deleted {table_type} {item_id}"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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

#Creates a leaderboard by sorting the top three fighters
@app.route('/api/roster', methods=['POST'])
def return_top_fighters():
    #pagination query
    data = request.get_json()
    page = data.get('page', 1)
    per_page = 10

    wl_ratio = case(
        (Character.losses == 0, Character.wins * 1.0),
        else_=(Character.wins * 1.0) / Character.losses
    )
    #just sorted by descending wins for now
    pagination = Character.query.filter_by(is_approved=True).order_by(wl_ratio.desc(), Character.wins.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify([c.to_dict_display() for c in pagination.items])

#returns a random assortment of user potraits
@app.route('/api/crowd')
def return_crowd():
    try:
        users_with_portraits = User.query.filter(User.portrait != None).all()
        selected_users = random.sample(users_with_portraits, min(len(users_with_portraits), 12))
        #returns username and portrait, making the portrait clickable
        return jsonify([{"username": u.username, "portrait": u.portrait} for u in selected_users])
    except Exception as e:
        print(f"!-- ERROR FETCHING CROWD: {e} --!")
        return jsonify([])
    
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
