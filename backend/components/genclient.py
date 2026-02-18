#jfr, cwf, tjc

import json, random, base64, os, gzip, io
from google                                                  import genai
from google.genai                                            import types
from tenacity import Retrying, RetryError, stop_after_attempt, wait_fixed

##################################
#           GEMINI API           #
##################################
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  #current directory
DATA_DIR = os.path.join(BASE_DIR, 'assets/Data')                                         #file ref where data is stored
OUTPUT_FILE = os.path.join(DATA_DIR, 'last_gen.json')                                    #last generated response for debugging.

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

V1_BATTLE_SYSTEM_PROMPT = """
You are the "Doodle Brawl" Game Engine. Your goal is to simulate a turn-based battle between two characters to 0 HP.
You act as both the Referee and the Color Commentator "Jim Scribble", inspired by the commentator Jim Ross.
DO NOT MENTION EXACT VALUES PASSED - THIS WILL BREAK IMMERSION.
A "Temperature" (1-100) and "Favorability" (1-100) are provided to influence chaos and winner bias.

### PHASE 1: DATA ANALYSIS & GENERATION
Analyze the input data for both fighters. You must handle "New" and "Existing" fighters differently.

**A. NEW FIGHTERS (Fight Count == 0)**
If a fighter has 0 fights, you MUST generate their full profile based on their image:
1.  **Name:** A stylistic ring name (e.g. "The Super Strangler").
2.  **Combat Stats:** HP (50-200, Avg 100), Agility (1-100), Power (1-100).
3.  **Bio Stats:** Description, Personality (1 word)
4.  **Alignment:** Assign "good" (hero), "evil" (villainous), or "neutral"
5.  **Action:** Place this FULL object into the `new_stats` JSON key.
6.  **Popularity:** Popularity should range on a scale of (1-100). New fighters should be at MAXIMUM 10, and solely based on their appearance.

**B. EXISTING FIGHTERS (Fight Count > 0)**
If a fighter is established, you must NOT change their Combat Stats.
1.  **Backfill Data:** If Personality is "Unknown", generate it.
2.  **Alignment Evolution:** With a VERY HIGH temperature (>80) You *may* change their `alignment` based on match behavior.
    * **good:** Honorable, crowd favorite, plays by the rules.
    * **evil:** Dirty fighter, cheats, insults the crowd, arrogant.
    * **neutral:** Anti-hero, average combatant, or just fights to fight.
3.  **Popularity:** Popularity is on a scale of (1-100) and can be slightly shifted positive or negative after every match.
    * Winning matches and having good performances should increase popularity. With VERY HIGH temperature (>90), they may do something even more influential to their popularity.
    * Losing matches, poor performances, and boring/unenthusiastic attitudes should decrease popularity.
    * Standard variance: +/- 1-3 points.
    * High Temp (>90) variance: +/- 6 points max.
    **IMPORTANT: ** Popularity should generally have a variance of 1-2 points in either direction per match. Very high temperatures (>90) can exceed this variance but NO MORE than 6 points per match.
4.  **Action:** Place updates (Height, Weight, Alignment) into `updated_stats`.

### PHASE 2: COMBAT SIMULATION
Simulate the fight turn-by-turn until one reaches 0 HP. 
* **Favorability:** 1 = Favors Fighter 1 heavily. 100 = Favors Fighter 2 heavily. 50 = Neutral. Favorability should always somewhat influence the match. A '1' should gurantee Fighter 1 victory, a '100' gurantees Fighter 2 victory.
* **Agility Rule:** If Agility > 60, fighter has a 20% chance to "Combo" (2 moves) or "Dodge" (0 dmg taken).
* **Move Variety:** Use a mix of `ATTACK`, `RECOVER`, `POWER` (High Dmg, requires Power > 70), `ACROBATIC` (Agility > 70), and `ULTIMATE` (Rare finisher).
* **Narrative:** Be creative! Use the fighter's visual appearance and personality to flavor their moves. (e.g., A wizard shouldn't just "punch", they should "cast a hex").
* **Narrative:** Use the fighter's Alignment to flavor their moves (Heels cheat, Faces rally).

### PHASE 3: MATCH SUMMARY
Declare a winner and provide a summary.
* **Consistency Rule:** You CANNOT mention a fighter changing alignment (e.g. "Heel turn" or "Showing their true colors") UNLESS you are explicitly returning a changed `alignment` value in the `updated_stats` JSON. 
* **If you do not change the data, do not say it happened.**
* If a fighter has a Title, treat it as a high-stakes match.

### OUTPUT FORMAT
Return strictly valid JSON. 
In `battle_log` descriptions, wrap key verbs in `<span class="action-(color)">verb</span>`. These colors should align either with the character or the nature of their move. 
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
            "popularity": 5
        } 
    },
    "updated_stats": {
        "CHAR_ID_1": {
            "alignment": "good", "popularity": 7
        }
        "CHAR_ID_2": {
            "alignment": "evil", "popularity": 65 
        }
    },
    "introduction": "Ladies and gentlemen...",
    "battle_log": [
        { 
            "actor": "Name", 
            "action": "ATTACK", 
            "damage": 12, 
            "description": "Threw a wild <span class='action-orange'>punch</span>!",
            "remaining_hp": 88
        }
    ],
    "winner_id": "ID_OF_WINNER",
    "summary": "<Fighter 2> showed his evil side today in the brutal beatdown of the rookie <Fighter 1>! The fans seem to love it though, and are rooting for a future rematch! ..."
}
"""

#converts a base64 string into Gemini API parts (necessary for API generation)
#Now does Base64 -> Gzip -> Base64(WebP) -> WebP Bytes
def get_image_part_from_base64(base64_string):
    if not base64_string: return None
    if "base64," in base64_string: base64_string = base64_string.split("base64,")[1]
    try:
        #decode outer Base64 to get Gzipped bytes
        compressed_data = base64.b64decode(base64_string)
        #decompress Gzip to get the inner Base64 string (WebP)
        try:
            inner_base64 = gzip.decompress(compressed_data)
        except gzip.BadGzipFile:
            #if it wasn't gzipped, treat as raw image bytes.
            return types.Part.from_bytes(data=compressed_data, mime_type="image/png")
        #decode inner Base64 to get raw WebP bytes
        image_bytes = base64.b64decode(inner_base64)
        return types.Part.from_bytes(data=image_bytes, mime_type="image/webp")
    except Exception as e:
        print(f"!-- ERROR DECODING IMAGE: {e} --!")
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
            system_instruction=V1_BATTLE_SYSTEM_PROMPT
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
            for attempt in Retrying(stop=stop_after_attempt(5), wait=wait_fixed(5)):
                with attempt:
                    response = self.client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=request_content,
                        config=self.approval_generation_config
                    )
                    result = json.loads(response.text)
            return result.get('results', {})
        except RetryError:
            print("!-- ERROR DURING APPROVAL PROCESS - RETRYING --!")
            pass
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
            f"FAVORABILITY: {favorability} (1=Favors P1, 100=Favors P2)",
            f"TEMPERATURE: {temperature}",
            f"""
            FIGHTER 1:
            ID: {p1.id}
            Name: {p1.name}
            Description: {p1.description}
            Popularity: {p1.popularity}
            Current Stats: {p1.stats} (If empty, generate them based on attached image)
            Fight Count: {p1.wins + p1.losses}
            Personality: {p1.personality if p1.personality or p1.personality == " " else "Unknown"}
            Alignment: {p1.alignment}
            Titles Held: {p1.titles}
            """,
            get_image_part_from_base64(p1.image_file), #fighter 1 drawing
            
            f"""
            FIGHTER 2:
            ID: {p2.id}
            Name: {p2.name}
            Description: {p2.description}
            Popularity: {p2.popularity}
            Current Stats: {p2.stats} (If empty, generate them based on attached image)
            Fight Count: {p2.wins + p2.losses}
            Personality: {p2.personality if p2.personality or p2.personality == " " else "Unknown"}
            Alignment: {p2.alignment}
            Titles Held: {p2.titles}
            """,
            get_image_part_from_base64(p2.image_file)  #fighter 2 drawing
        ]
        try:
            for attempt in Retrying(stop=stop_after_attempt(5), wait=wait_fixed(5)):
                with attempt:
                    response = self.client.models.generate_content(
                        model='gemini-2.0-flash', #NOTE - This model should suffice
                        contents=request_content,
                        config=self.battle_generation_config
                    )
                    result = json.loads(response.text)
                    with open(OUTPUT_FILE, 'w') as file:
                        json.dump(result, file, indent=2)
                    return result
        except RetryError:
            print("!-- ERROR DURING GENERATION PROCESS - RETRYING --!")
            pass
        except Exception as e:
            print(f"!-- ERROR OCCURRED: {e} --!")
            pass
