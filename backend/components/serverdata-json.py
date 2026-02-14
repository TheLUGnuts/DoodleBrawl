#jfr, cwf, tjc

#THIS IS AN OLD BACKUP OF SERVERDATA USING LOCAL JSON FILES INSTEAD OF THE SQLITE DATABASE

import os, json, time, re
from components.character import Character

##################################
#          DATA HANDLERS         #
##################################

#Data paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  #current directory
DATA_DIR = os.path.join(BASE_DIR, 'assets/Data')                                         #file ref where data is stored
IMAGE_DIR = os.path.join(BASE_DIR, 'assets/Images')                                      #file ref where images are located
CHARACTER_FILE = os.path.join(DATA_DIR, 'characters.json')                               #JSON file reference of character objects
QUEUE_FILE = os.path.join(DATA_DIR, 'queue.json')                                        #approval queue of characters
OUTPUT_FILE = os.path.join(DATA_DIR, 'last_gen.json')                                    #last generated response for debugging.
REJECTED_FILE = os.path.join(DATA_DIR, 'rejected.json')                                  #file containing rejected images, their ID, and reason for rejection
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')                                    #the file path

class ServerData:
    def __init__(self, genclient):
        self.match_history = []                                              #match history array
        self.characters = {}                                                 #dict of character objects
        self.approval_queue = {}                                             #dict of submitted characters to be approved
        self.genclient = genclient                                           #gemini API client

    #########################
    #     LOADING FUNCs     #
    #########################

    #load the characters from the characters.json file
    def load_characters(self):
        if not os.path.exists(CHARACTER_FILE):
            print(f"!--- CHARACTER FILE WASN'T FOUND AT {CHARACTER_FILE}---!")
            return
        try:
            with open(CHARACTER_FILE, 'r') as file:
                data = json.load(file)
                #create the character objects in memory form the file.
                for char_id, char_data in data.items():
                    self.characters[char_id] = Character(id_or_data=char_id, data=char_data)
            print(f"$-- LOADED {len(self.characters)} CHARACTERS --$")
        except Exception as e:
            print(f"!-- ERROR LOADING CHARACTERS --!\n ERROR: {e}")

    #load the approval queue from the queue.json file
    def load_queue(self):
        if not os.path.exists(QUEUE_FILE):
            print(f"!--- QUEUE FILE WASN'T FOUND AT {QUEUE_FILE}---!")
            return
        try:
            with open(QUEUE_FILE, 'r') as file:
                data = json.load(file)
                #create the character objects in memory form the file.
                for char_id, char_data in data.items():
                    self.approval_queue[char_id] = Character(id_or_data=char_id, data=char_data)
            print(f"$-- LOADED {len(self.approval_queue)} CHARACTERS FOR APPROVAL QUEUE --$")
        except Exception as e:
            print(f"!-- ERROR LOADING APPROVAL QUEUE --!\n ERROR: {e}")
    
    #load match history
    def load_history(self):
        if not os.path.exists(HISTORY_FILE):
            return
        try:
            with open(HISTORY_FILE, 'r') as file:
                self.match_history = json.load(file)
            print(f"$-- LOADED {len(self.match_history)} PAST MATCHES --$")
        except Exception as e:
            print(f"!-- ERROR LOADING HISTORY: {e} --!")

    #########################
    #      SAVING FUNCs     #
    #########################

    def save_history(self):
        try:
            with open(HISTORY_FILE, 'w') as file:
                json.dump(self.match_history, file, indent=2)
        except Exception as e:
            print(f"!-- ERROR SAVING HISTORY: {e} --!")

    #save all characters to the characters.json file
    def save_characters(self):
        try:
            data = {c_id: c.to_dict() for c_id, c in self.characters.items()}
            with open(CHARACTER_FILE, 'w') as file:
                json.dump(data, file, indent=2)
            print(f"$-- CHARACTERS SAVED TO characters.json --$")
        except Exception as e:
            print(f"!-- ERROR SAVING CHARACTERS --!\n ERROR: {e}")

    #save queued characters to queue.json
    def save_queue(self):
        try:
            data = {c_id: c.to_dict() for c_id, c in self.approval_queue.items()}
            with open(QUEUE_FILE, 'w') as file:
                json.dump(data, file, indent=2)
            print(f"$-- QUEUE SAVED TO queue.json --$")
        except Exception as e:
            print(f"!-- ERROR SAVING QUEUE --!\n ERROR: {e}")

    #########################
    #    GenClient FUNCs    #
    #########################

    #submit the current approval queue to the API for inappropriate content
    def submit_queue_for_approval(self):
        #only run the approval submission if theres at least 3 to add.
        if len(self.approval_queue) < 3:
            return
        #submit the approval queue for AI approval
        results = self.genclient.submit_for_approval(self.approval_queue)
        if not results:
            return
        ids_to_remove = []
        for char_id, decision in results.items():
            if char_id in self.approval_queue:
                if decision.get('approved'):
                    #Move to main game roster
                    character = self.approval_queue[char_id]
                    self.characters[char_id] = character
                    print(f"$-- APPROVED: {char_id} --$")
                else:
                    #Rejected, log it
                    reason = decision.get('reason', 'Unknown')
                    print(f"!-- REJECTED: {char_id} - Reason: {reason} --!")
                    self.log_rejection(char_id, self.approval_queue[char_id], reason)
                ids_to_remove.append(char_id)
        for char_id in ids_to_remove:
            del self.approval_queue[char_id]
        self.save_characters()
        self.save_queue()

    #########################
    #     Logging FUNCs     #
    #########################

    def log_match_result(self, teams, winner, summary, match_type="1v1", title_change=None):
        #create the teams for when we add future team matches. 1v1 matches will just have one fighter in each team
        formatted_teams = []
        for team in teams:
            team_data = [{"id": f.id, "name": f.name} for f in team]
            formatted_teams.append(team_data)

        #the history json entry
        entry = {
            "timestamp": time.time(),
            "match_type": match_type,           # "1v1", "TAG", "GAUNTLET", etc.
            "is_title_bout": title_change is not None,
            "title_exchanged": title_change if title_change else False, #false if retained, a string if changed
            "teams": formatted_teams,
            "winner_id": winner.id,
            "display_text": summary #match summary
        }

        self.match_history.append(entry)
        self.save_history()

    #log rejections
    def log_rejection(self, char_id, char_obj, reason):
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