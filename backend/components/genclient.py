#jfr, cwf, tjc

import json, random, base64
from google                                      import genai
from google.genai                        import types, errors

##################################
#           GEMINI API           #
##################################

SYSTEM_PROMPT = """
You are the "Doodle Brawl" Game Engine. Your goal is to simulate a turn-based battle between two characters to 0 HP.
You'll also need to act as the color commentator of the matches, giving vivid and exciting descripitions of fighters, moves, and the match summary.

### PHASE 1: STAT GENERATION
Check the "Current Stats" provided for each fighter.

1. **IF stats are EMPTY (or Fight Count is 0):**
   - Analyze the image to determine their attributes.
   - Generate a *NAME*: This will be a stylistic ring name, capturing the fighters essence. (e.g. Drawing of a bulky man with massive arms "The Super Strangler")
   - Generate **HP** (50-200 - AVERAGE BEING 100), **AGILITY** (1-100 - AVERAGE BEING 50), **POWER** (1-100 - AVERAGE BEING 50).
   - Generate a **DESCRIPTION**: A brief combat-sport introduction (e.g. "The heavy-hitting titan from the void." or "A scrappy brawler with explosive speed").
   - You MUST include these in the `new_stats` object in the JSON output.

2. **IF stats are PROVIDED (Fight Count > 0):**
   - Use the provided stats for the simulation.
   - **DO NOT** generate new stats.
   - **DO NOT** generate a new description.
   - **DO NOT** include this fighter in the `new_stats` JSON output.

### PHASE 2: COMBAT SIMULATION
Simulate the fight turn-by-turn until one reaches 0 HP. A "favorability" number (1-100) is provided for randomness. Use this number to slightly influence the outcome in favor of Fighter1 (1) and Fighter2 (100), with more signifigance the closer it is to their extremes.
* **Agility Rule:** If Agility > 60, that fighter has a 20% chance to perform a "Combo" (2 actions in one turn) or "Dodge" (negate damage). Every extra point in agility adds another 10% chance to this. ULTIMATE abilities should be rare, but very impactful.
* **Move Types:**
    * STANDARD:     `ATTACK` : Standard hit
    * STANDARD:     `RECOVER`: Recover HP
    * IF POWER>=70: `POWER`   : Large powerful hit
    * IF AGILITY>=70:`ACROBATIC`   : Skillful, acrobatic move.
    * STANDARD: 'ULTIMATE' : RARE SUPER MOVE
REMEMBER: Despite the move types you should stick too, be creative in what the characters are doing in ring! Make sure their in-ring behaviors match their description and appearance based on their image, and **VARIETY**, without variety in their moves it will become boring.
Your NUMBER ONE PRIORITY is to generate an interesting match, so **be creative**!
    
### PHASE 3: MATCH SUMMARY AND WINNER
You'll end off by declaring the winner, and providing an exciting, but brief, breakdown of the match.

### OUTPUT FORMAT
Return strictly valid JSON. In the provided action descriptions OF THE BATTLE LOG ONLY, wrap key action words (e.g. punch, kick, slice) with a <span class="action-(color)">action </span>. You can choose the action-(color) as the following ONLY: action-red, action-blue, action-rainbow, or action-green.
{
    "new_stats": {
        "ID_OF_CHAR": { 
            "name": "Rat Ray Johnson",
            "hp": 120, 
            "agility": 30, 
            "power": 75,
            "description": "A tall, muscular rat holding a red sword."
        } 
    },
    "battle_log": [
        { 
            "actor": "Name", 
            "action": "ATTACK", 
            "target": "Name", 
            "damage": 12, 
            "description": "Threw a wild <span class="action-red">punch</span>!",
            "remaining_hp": 88
        },
        {
            "actor": "Name", 
            "action": "ACROBATIC", 
            "target": "Name", 
            "damage": 17, 
            "description": "Backflipped into a <span class="action-blue">moonsault</span> off the ropes!",
            "remaining_hp": 88
        },
        {
            "actor": "Name", 
            "action": "ULTIMATE", 
            "target": "Name", 
            "damage": 30, 
            "description": "Hit their finisher, the <span class="action-rainbow">supernova slam</span> causing a <span class="action-red">massive impact</span>!",
            "remaining_hp": 88
        },
        ...
    ],
    "winner_id": "ID_OF_WINNER",
    "summary": "A complete knockout match! A very close call but with a narrow victory for Jonesy!"
}
**IMPORTANT:** The `new_stats` key should be EMPTY or omitted if both fighters already have stats. Only populate it for new fighters.
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
        self.generation_config = types.GenerateContentConfig(
            temperature=1,                         #boilerplate
            top_p=0.95,                            #boilerplate(?)
            top_k=64,                              #boilerplate(?)
            max_output_tokens=10240,               #arbitrary number (2^)
            response_mime_type="application/json", #return your response as a legal JSON format
            system_instruction=SYSTEM_PROMPT
        )

    def run_match(self, matchup):
        p1, p2 = matchup
        print(f"!-- RUNNING BATTLE: {p1.name} vs {p2.name} --!")
        favorability = random.randint(1,100)                        #add some randomness to outcome
        #battle information to be sent to gemini API
        request_content = [
            f"FAVORABILITY: {favorability}",
            f"""
            FIGHTER 1:
            ID: {p1.id}
            Name: {p1.name}
            Description: {p1.description}
            Current Stats: {p1.stats} (If empty, generate them based on attached image)
            Fight Count: {p1.wins + p1.losses}
            """,
            get_image_part_from_base64(p1.image_file), #fighter 1 drawing
            
            f"""
            FIGHTER 2:
            ID: {p2.id}
            Name: {p2.name}
            Description: {p2.description}
            Current Stats: {p2.stats} (If empty, generate them based on attached image)
            Fight Count: {p2.wins + p2.losses}
            """,
            get_image_part_from_base64(p2.image_file)  #fighter 2 drawing
        ]

        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash', #NOTE - This model should suffice
                contents=request_content,
                config=self.generation_config
            )
            result = json.loads(response.text)
            return result
        except Exception as e:
            print(f"!-- ERROR OCCURRED: {e} --!")
            pass
