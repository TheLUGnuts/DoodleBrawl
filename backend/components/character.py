#cwf, jfr, tjc
import random
import string

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
        self.championship: str = ""
        # If data dict is present, overwrite defaults
        if data:
            self.id = data.get("id", self.id)
            self.image_file = data.get("image_file", self.image_file)
            self.stats = data.get("stats", self.stats)
            self.wins = data.get("wins", self.wins)
            self.losses = data.get("losses", self.losses)
            self.name = data.get("name", self.name)
            self.description = data.get("description", self.description)
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
            "championship": self.championship
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
            "championship": self.championship
        }
    
    def update_values(self, new_stats: dict) -> None:
        """Takes a dictionary containing new values for any of the character stats."""
        self.id = new_stats["id"] if new_stats.get("id", False) else self.id
        self.image_file = new_stats["image_file"] if new_stats.get("image_file", False) else self.image_file
        self.stats = new_stats["stats"] if new_stats.get("stats", False) else self.stats
        self.wins = new_stats["wins"] if new_stats.get("wins", False) else self.wins
        self.losses = new_stats["losses"] if new_stats.get("losses", False) else self.losses
        self.name = new_stats["name"] if new_stats.get("name", False) else self.name
        self.description = new_stats.get("description", self.description)

    #Representation of character object
    def __repr__(self):
        return f"<Fighter: {self.name} (ID: {self.id})>"




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