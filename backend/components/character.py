#cwf, jfr, tjc
import random, string, time

##################################
#       CHARACTER HANDLING       #
##################################

class Character():
    """The class for storing all the character information for a single character.
    @param id: A randomly generated string of characters that represents the character.
    @param image_file: The location for where the character file is located.
    @param stats: The dictionary containing HP, speed, agility and power.
    @param wins: The number of wins.
    @param losses: The number of losses.
    @param total_battles: 
    @param name: The name of the character"""
    def __init__(self, id_or_data, image_ref: str = "", name="", data = None):
        if isinstance(id_or_data, dict):
            data = id_or_data
            self.id = data.get("id", "UNKNOWN_ID")
        else:
            self.id = id_or_data
        #defaults
        self.image_file: str = image_ref
        self.stats: dict = dict()
        self.wins: int = 0
        self.losses: int = 0
        self.name: str = name
        self.description: str = "Mysterious Challenger!"
        self.alignment: str = "Neutral"
        self.titles: list = []
        self.personality: str = ""
        self.creation_time = time.time()
        self.manager: str = "None"
        self.popularity: int = 1
        # If data dict is present, overwrite defaults
        if data:
            self.id = data.get("id", self.id)
            self.image_file = data.get("image_file", self.image_file)
            self.stats = data.get("stats", self.stats)
            self.wins = data.get("wins", self.wins)
            self.losses = data.get("losses", self.losses)
            self.name = data.get("name", self.name)
            self.description = data.get("description", self.description)
            self.alignment = data.get("alignment", "Unknown")
            self.titles = data.get("titles", [])
            #fallback to safely move championship status into the new 'titles' list.
            old_status = data.get("status", None)
            if old_status:
                if "Champion" in old_status and "Former" not in old_status:
                    if old_status not in self.titles:
                        self.titles.append(old_status)

            self.personality = data.get("personality", self.personality)
            self.manager = data.get("manager", self.manager)

        self.total_battles = self.wins + self.losses

    
    def to_dict(self) -> dict:
        """Creates a dictionary containing all on the character information."""
        return {
            "id": self.id,
            "image_file": self.image_file,
            "stats": self.stats,
            "wins": self.wins,
            "losses": self.losses,
            "name": self.name,
            "description": self.description,
            "alignment": self.alignment,
            "titles": self.titles,
            "personality": self.personality,
            "manager": self.manager
        }

    def to_light_dict(self) -> dict:
        """Returns character info WITHOUT the base64 string"""
        return {
            "id": self.id,
            "name": self.name,
            "stats": self.stats,
            "wins": self.wins,
            "losses": self.losses,
            "description": self.description,
            "alignment": self.alignment,
            "titles": self.titles,
            "personality": self.personality,
            "manager": self.manager
        }
    
    def update_values(self, new_stats: dict) -> None:
        """Takes a dictionary containing new values for any of the character stats."""
        self.id = new_stats.get("id", self.id)
        self.image_file = new_stats.get("image_file", self.image_file)
        self.stats = new_stats.get("stats", self.stats)
        self.wins = new_stats.get("wins", self.wins)
        self.losses = new_stats.get("losses", self.losses)

        self.name = new_stats.get("name", self.name)
        self.description = new_stats.get("description", self.description)
        self.personality = new_stats.get("personality", self.personality)
        self.status = new_stats.get("status", self.status)
        self.manager = new_stats.get("manager", self.manager)

        self.alignment = new_stats.get("alignment", self.alignment)
        #on the offchance that we want it to create a new title, or something.
        if "titles" in new_stats:
            self.titles = new_stats["titles"]

        #keywords for capturing any remaining stat keys
        combat_keys = ['hp', 'HP', 'agility', 'Agility', 'power', 'Power', 'speed', 'Speed']
        stats_update = {k: v for k, v in new_stats.items() if k.lower() in [ck.lower() for ck in combat_keys]}
        
        if stats_update:
            self.stats.update(stats_update)

    #Representation of character object
    def __repr__(self):
        return f"<Fighter: {self.name} (ID: {self.id})>"



# lol, what is this?
if __name__ == "__main__":
    data = {
        "image_file": "/nope.png",
        "stats": {
            "hp": 10,
            "speed": 10,
            "agility": 10,
            "power": 10
        },
        "wins": 10,
        "losses": 100000,
        "name": "spider man"
    }
    temp = Character(data=data)
    data = {
        "name": "idiot"
    }
    print(temp.total_battles)
    print(temp.id)
    print(temp.name)
    temp.update_values(data)
    print(temp.id)
    print(temp.name)