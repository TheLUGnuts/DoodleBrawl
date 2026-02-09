#jfr, cwf, tjc

import json, random, base64
from google                 import genai
from google.genai           import types

##################################
#           GEMINI API           #
##################################

APPROVAL_SYSTEM_PROMPT="""
You are a Content Safety Moderator for a "Doodle Brawl" game. 
Your job is to analyze the provided images and flag them for safety.
You must strictly reject any image containing:
1. Sexual content, nudity, or sexually suggestive poses/anatomy.
2. Hate symbols, racism, or discriminatory imagery.
3. Excessive gore or disturbing violence (cartoon violence is okay, realistic/gory is not).
4. Offensive text or slurs.
5. Images that are excessively lazy, not particularly of poor quality, but clearly lacking in effort. This includes empty/blank submissions.

Output strictly valid JSON in the following format:
{
    "results": {
        "CHAR_ID_1": { "approved": true },
        "CHAR_ID_2": { "approved": false, "reason": "Contains nudity" }
    }
}
"""

BATTLE_SYSTEM_PROMPT = """
You are the "Doodle Brawl" Game Engine. Your goal is to simulate a turn-based battle between two characters to 0 HP.
You act as both the Referee and the Color Commentator.
Fighter 1 is in the blue corner, Fighter 2 is in the red corner.
A "Temperature" (1-100) and "Favorability" (1-100) are provided to influence chaos and winner bias.

### PHASE 1: DATA ANALYSIS & GENERATION
Analyze the input data for both fighters. You must handle "New" and "Existing" fighters differently.

**A. NEW FIGHTERS (Fight Count == 0)**
If a fighter has 0 fights, you MUST generate their full profile based on their image:
1.  **Name:** A stylistic ring name (e.g. "The Super Strangler").
2.  **Combat Stats:** HP (50-200, Avg 100), Agility (1-100), Power (1-100).
3.  **Bio Stats:** Description, Personality (1 word), Height (e.g. "6ft2"), Weight (e.g. "220lbs").
4.  **Action:** Place this FULL object into the `new_stats` JSON key.

**B. EXISTING FIGHTERS (Fight Count > 0)**
If a fighter is established, you must NOT change their Combat Stats (HP/Agility/Power), but you may need to backfill missing bio data.
1.  **Backfill Missing Data:** If Height, Weight, or Personality are listed as "Unknown", generate them based on the image.
2.  **Status Evolution:** If Temperature > 75, you may update their `status` (e.g., "Rookie" -> "Fan Favorite"). **EXCEPTION:** Never change a status if it contains "Champion".
3.  **Action:** Place these specific updates (Height, Weight, Status) into the `updated_stats` JSON key.

### PHASE 2: COMBAT SIMULATION
Simulate the fight turn-by-turn until one reaches 0 HP. 
* **Favorability:** 1 = Favors Fighter 1 heavily. 100 = Favors Fighter 2 heavily. 50 = Neutral.
* **Agility Rule:** If Agility > 60, fighter has a 20% chance to "Combo" (2 moves) or "Dodge" (0 dmg taken).
* **Move Variety:** Use a mix of `ATTACK`, `RECOVER`, `POWER` (High Dmg, requires Power > 70), `ACROBATIC` (Agility > 70), and `ULTIMATE` (Rare finisher).
* **Narrative:** Be creative! Use the fighter's visual appearance and personality to flavor their moves. (e.g., A wizard shouldn't just "punch", they should "cast a hex").

### PHASE 3: MATCH SUMMARY
Declare a winner and provide a summary.
* **Championships:** If a fighter is a "Champion", this is a Title Fight. Treat it with high stakes.

### OUTPUT FORMAT
Return strictly valid JSON. 
In `battle_log` descriptions, wrap key verbs in `<span className="action-(color)">verb</span>`. 
Colors: red, blue, green, yellow, purple, pink, orange, brown, black, rainbow (Ultimates only).

**JSON STRUCTURE EXAMPLE:**
{
    "new_stats": {
        "CHAR_ID_1": { 
            "name": "Fresh Rookie",
            "hp": 100, 
            "agility": 50, 
            "power": 50,
            "description": "A new challenger approaches.",
            "personality": "Eager",
            "height": "5ft9",
            "weight": "160lbs"
        } 
    },
    "updated_stats": {
        "CHAR_ID_2": {
            "height": "6ft5", 
            "weight": "280lbs",
            "personality": "Gruff",
            "status": "Grizzled Veteran"
        }
    },
    "introduction": "Ladies and gentlemen...",
    "battle_log": [
        { 
            "actor": "Name", 
            "action": "ATTACK", 
            "damage": 12, 
            "description": "Threw a wild <span class='action-red'>punch</span>!",
            "remaining_hp": 88
        }
    ],
    "winner_id": "ID_OF_WINNER",
    "summary": "A close match..."
}
"""

#converts a base64 string into Gemini API parts (necessary for API generation)
def get_image_part_from_base64(base64_string):
    if not base64_string:
        return None

    #strip data uri header, if it exists
    if "base64," in base64_string:
        base64_string = base64_string.split("base64,")[1]
    
    try:
        #turn into bytes
        image_bytes = base64.b64decode(base64_string)
        #return this as a part object for gemini
        return types.Part.from_bytes(data=image_bytes, mime_type="image/png")
    except Exception as e:
        print(f"!-- ERROR DECODING BASE64 IMAGE: {e} --!")
        return None
        
class Genclient():
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.battle_generation_config = types.GenerateContentConfig(
            temperature=1,                         #boilerplate
            top_p=0.95,                            #boilerplate(?)
            top_k=64,                              #boilerplate(?)
            max_output_tokens=10240,               #arbitrary number
            response_mime_type="application/json", #return your response as a legal JSON format
            system_instruction=BATTLE_SYSTEM_PROMPT
        )
        self.approval_generation_config = types.GenerateContentConfig(
            temperature=1,                         #boilerplate
            top_p=0.95,                            #boilerplate(?)
            top_k=64,                              #boilerplate(?)
            max_output_tokens=10240,               #arbitrary number
            response_mime_type="application/json", #return your response as a legal JSON format
            system_instruction=APPROVAL_SYSTEM_PROMPT
        )

    #submit a queue of character images for approval.
    def submit_for_approval(self, queue):
        if not queue:
            print("!-- QUEUE EMPTY, NOTHING FOR APPROVAL PROCESS --!")
            return {}
        print(f"!-- SUBMITTING {len(queue)} IMAGES FOR APPROVAL --!")
        #create request content, interleaving ID and image (base64)
        request_content = ["Analyze these images based on the ID provided above them:"]
        for char_id, char_obj in queue.items():
            #add ID
            request_content.append(f"ID: {char_id}")
            #add image
            img_part = get_image_part_from_base64(char_obj.image_file)
            if img_part:
                request_content.append(img_part)
            else:
                request_content.append("[IMAGE DATA MALFORMED - REJECT]")
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=request_content,
                config=self.approval_generation_config
            )
            result = json.loads(response.text)
            return result.get('results', {})
        except Exception as e:
            print(f"!-- ERROR DURING APPROVAL PROCESS: {e} --!")
            return {}

    #run the match by setting up the api submission content
    def run_match(self, matchup):
        p1, p2 = matchup
        favorability = random.randint(1,100) #add some randomness to outcome
        temperature = random.randint(1,100)  #add some randomness to outcome
        print(f"!-- RUNNING BATTLE: {p1.name} vs {p2.name} WITH FAVORABILITY, TEMPERATURE: {favorability}, {temperature} --!")
        #battle information to be sent to gemini API
        request_content = [
            f"FAVORABILITY: {favorability}",
            f"TEMPERATURE: {temperature}"
            f"""
            FIGHTER 1:
            ID: {p1.id}
            Name: {p1.name}
            Description: {p1.description}
            Height: {p1.height if p1.height else "Unknown"}
            Weight: {p1.weight if p1.weight else "Unknown"}
            Current Stats: {p1.stats} (If empty, generate them based on attached image)
            Fight Count: {p1.wins + p1.losses}
            Personality: {p1.personality if p1.personality or p1.personality == " " else "Unknown"}
            status: {p1.status}
            """,
            get_image_part_from_base64(p1.image_file), #fighter 1 drawing
            
            f"""
            FIGHTER 2:
            ID: {p2.id}
            Name: {p2.name}
            Description: {p2.description}
            Height: {p2.height if p2.height else "Unknown"}
            Weight: {p2.weight if p2.weight else "Unknown"}
            Current Stats: {p2.stats} (If empty, generate them based on attached image)
            Fight Count: {p2.wins + p2.losses}
            Personality: {p2.personality if p2.personality or p2.personality == " " else "Unknown"}
            status: {p2.status}
            """,
            get_image_part_from_base64(p2.image_file)  #fighter 2 drawing
        ]
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash', #NOTE - This model should suffice
                contents=request_content,
                config=self.battle_generation_config
            )
            result = json.loads(response.text)
            return result
        except Exception as e:
            print(f"!-- ERROR OCCURRED: {e} --!")
            pass
