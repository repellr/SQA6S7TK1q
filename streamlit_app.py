# D&D Encounter Builder (5e) — Google Colab friendly
# --------------------------------------------------
# Drop this whole cell into Google Colab and run it. A small UI will appear.
# No internet access required. You can also upload your own monster CSV to expand the database.
# Challenge scaffolds removed per request. Seeds are randomized automatically on each action.

import math
import random
import textwrap
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# Widgets / display
try:
    import ipywidgets as widgets
    from IPython.display import display, HTML
    _HAS_WIDGETS = True
except Exception:
    _HAS_WIDGETS = False

# CSV support
try:
    import pandas as pd
except Exception:
    pd = None

# -----------------------------
# Core SRD-ish XP tables (DMG)
# -----------------------------
XP_THRESHOLDS = {
    1:  {"easy": 25,   "medium": 50,   "hard": 75,    "deadly": 100},
    2:  {"easy": 50,   "medium": 100,  "hard": 150,   "deadly": 200},
    3:  {"easy": 75,   "medium": 150,  "hard": 225,   "deadly": 400},
    4:  {"easy": 125,  "medium": 250,  "hard": 375,   "deadly": 500},
    5:  {"easy": 250,  "medium": 500,  "hard": 750,   "deadly": 1100},
    6:  {"easy": 300,  "medium": 600,  "hard": 900,   "deadly": 1400},
    7:  {"easy": 350,  "medium": 750,  "hard": 1100,  "deadly": 1700},
    8:  {"easy": 450,  "medium": 900,  "hard": 1400,  "deadly": 2100},
    9:  {"easy": 550,  "medium": 1100, "hard": 1600,  "deadly": 2400},
    10: {"easy": 600,  "medium": 1200, "hard": 1900,  "deadly": 2800},
    11: {"easy": 800,  "medium": 1600, "hard": 2400,  "deadly": 3600},
    12: {"easy": 1000, "medium": 2000, "hard": 3000,  "deadly": 4500},
    13: {"easy": 1100, "medium": 2200, "hard": 3400,  "deadly": 5100},
    14: {"easy": 1250, "medium": 2500, "hard": 3800,  "deadly": 5700},
    15: {"easy": 1400, "medium": 2800, "hard": 4300,  "deadly": 6400},
    16: {"easy": 1600, "medium": 3200, "hard": 4800,  "deadly": 7200},
    17: {"easy": 2000, "medium": 3900, "hard": 5900,  "deadly": 8800},
    18: {"easy": 2100, "medium": 4200, "hard": 6300,  "deadly": 9500},
    19: {"easy": 2400, "medium": 4900, "hard": 7300,  "deadly": 10900},
    20: {"easy": 2800, "medium": 5700, "hard": 8500,  "deadly": 12700},
}

# XP per Challenge Rating (SRD values)
CR_XP = {
    0: 10, 1/8: 25, 1/4: 50, 1/2: 100,
    1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800, 6: 2300, 7: 2900, 8: 3900,
    9: 5000, 10: 5900, 11: 7200, 12: 8400, 13: 10000, 14: 11500, 15: 13000,
    16: 15000, 17: 18000, 18: 20000, 19: 22000, 20: 25000, 21: 33000, 22: 41000,
    23: 50000, 24: 62000, 25: 75000, 26: 90000, 27: 105000, 28: 120000, 29: 135000, 30: 155000,
}

# Encounter multipliers by number of monsters (DMG) with party-size adjustment
BASE_MULTIPLIER = [
    (1, 1.0),
    (2, 1.5),
    (6, 2.0),
    (10, 2.5),
    (14, 3.0),
    (math.inf, 4.0),
]
PARTY_SIZE_ADJ = {"small": 1.5, "normal": 1.0, "large": 0.75}

# ---------------------------------
# Minimal offline monster database
# ---------------------------------
@dataclass
class Monster:
    name: str
    cr: float
    type: str
    tags: List[str]
    environments: List[str]
    xp: int = field(init=False)
    def __post_init__(self):
        if isinstance(self.cr, str) and "/" in self.cr:
            num, den = self.cr.split("/")
            self.cr = float(num) / float(den)
        self.cr = float(self.cr)
        self.xp = CR_XP.get(self.cr, 0)

# Seed list (SRD-friendly; extend via CSV)
SEED_MONSTERS: List[Monster] = [
  Monster("Aarakocra", 1/4, "humanoid", ["flight", "talons", "javelin"], ["mountain", "sky"]),
  Monster("Aboleth", 10, "aberration", ["telepathy", "enslave", "mucus-cloud"], ["underwater", "ruins"]),
  Monster("Abishai, Black", 7, "fiend", ["devil", "black-fire", "magic-resistance"], ["nine-hells", "temple"]),
  Monster("Abishai, Blue", 17, "fiend", ["devil", "lightning", "dragon-scale"], ["nine-hells", "fortress"]),
  Monster("Abishai, Green", 15, "fiend", ["devil", "poison", "fear"], ["nine-hells", "swamp"]),
  Monster("Abishai, Red", 19, "fiend", ["devil", "fire", "teleport"], ["nine-hells", "battlefield"]),
  Monster("Abishai, White", 6, "fiend", ["devil", "cold", "flight"], ["nine-hells", "arctic"]),
  Monster("Acolyte", 1/4, "humanoid", ["spellcasting", "healing"], ["temple", "city"]),
  Monster("Adult Black Dragon", 14, "dragon", ["acid-breath", "legendary-resistance", "swim"], ["swamp", "marsh"]),
  Monster("Adult Blue Dragon", 16, "dragon", ["lightning-breath", "legendary-resistance", "burrow"], ["desert", "coast"]),
  Monster("Adult Brass Dragon", 13, "dragon", ["sleep-gas", "fire-breath", "charm"], ["desert", "caves"]),
  Monster("Adult Bronze Dragon", 15, "dragon", ["lightning-breath", "repulsion-breath", "swim"], ["coast", "islands"]),
  Monster("Adult Copper Dragon", 14, "dragon", ["slow-breath", "acid-breath", "prankster"], ["hill", "canyon"]),
  Monster("Adult Gold Dragon", 17, "dragon", ["fire-breath", "weakening-breath", "shapechanger"], ["mountain", "palace"]),
  Monster("Adult Green Dragon", 15, "dragon", ["poison-breath", "deception", "swim"], ["forest", "jungle"]),
  Monster("Adult Red Dragon", 17, "dragon", ["fire-breath", "legendary-resistance", "flight"], ["mountain", "volcano"]),
  Monster("Adult Silver Dragon", 16, "dragon", ["cold-breath", "paralyzing-breath", "shapechanger"], ["mountain", "cloud"]),
  Monster("Adult White Dragon", 13, "dragon", ["cold-breath", "legendary-resistance", "burrow"], ["arctic", "glacier"]),
  Monster("Alhoon", 10, "undead", ["mind-flayer", "lich", "psionics"], ["underdark", "dungeons"]),
  Monster("Alkilith", 11, "fiend", ["demon", "corrupt-ground", "teleport"], ["abyss", "wasteland"]),
  Monster("Allip", 5, "undead", ["wailing-horror", "madness", "incorporeal"], ["ruins", "graveyard"]),
  Monster("Amnizu", 18, "fiend", ["devil", "soul-recall", "teleport"], ["nine-hells", "fortress"]),
  Monster("Angel, Deva", 10, "celestial", ["healing", "radiant-damage", "shapeshift"], ["upper-planes", "temple"]),
  Monster("Angel, Planetar", 16, "celestial", ["greatsword", "holy-aura", "divine-sense"], ["upper-planes", "sky"]),
  Monster("Angel, Solar", 21, "celestial", ["vorpal-sword", "slaying-arrow", "healing"], ["upper-planes", "battlefield"]),
  Monster("Animated Armor", 1, "construct", ["false-appearance", "antimagic-susceptibility"], ["dungeons", "castle"]),
  Monster("Ankheg", 2, "monstrosity", ["acid-spray", "burrow"], ["forest", "farmland"]),
  Monster("Annis Hag", 6, "fey", ["crushing-embrace", "talons", "shapeshift"], ["forest", "mountains"]),
  Monster("Archdruid", 12, "humanoid", ["spellcaster", "wild-shape", "nature-ally"], ["forest", "sacred-grove"]),
  Monster("Archer", 3, "humanoid", ["longbow", "battle-mastery"], ["camp", "city-wall"]),
  Monster("Armanite", 7, "fiend", ["demon", "cavalry", "trample"], ["abyss", "wasteland"]),
  Monster("Assassin", 8, "humanoid", ["assassinate", "poison", "stealth"], ["city", "sewers"]),
  Monster("Astral Dreadnought", 21, "aberration", ["gargantuan", "antimagic-cone", "soul-capture"], ["astral-plane", "void"]),
  Monster("Aurochs", 2, "beast", ["charge", "trample", "herd"], ["grassland", "plains"]),
  Monster("Azer", 2, "elemental", ["fire-immunity", "heated-weapon", "smithing"], ["elemental-plane-of-fire", "forge"]),

  Monster("Babau", 4, "fiend", ["demon", "stealth", "shadows"], ["abyss", "ruins"]),
  Monster("Baboon", 0, "beast", ["pack-tactics"], ["jungle", "savanna"]),
  Monster("Badger", 0, "beast", ["burrow", "keen-smell"], ["forest", "plains"]),
  Monster("Bael", 19, "fiend", ["devil", "commander", "teleportation"], ["hells", "fortress"]),
  Monster("Balhannoth", 11, "aberration", ["lure", "teleportation", "blindsight"], ["underdark", "dungeons"]),
  Monster("Balor", 19, "fiend", ["demon", "fire", "whip", "sword"], ["abyss", "battlefield"]),
  Monster("Banderhobb", 5, "monstrosity", ["swallow", "shadow-step", "invisibility"], ["swamp", "shadow-fell"]),
  Monster("Bandit", 1/8, "humanoid", ["pack-tactics", "dagger", "scimitar"], ["roadside", "wilderness"]),
  Monster("Bandit Captain", 2, "humanoid", ["commander", "parry"], ["camp", "ruins"]),
  Monster("Banshee", 4, "undead", ["wail", "incorporeal", "fear"], ["haunted-place", "ruins"]),
  Monster("Baphomet", 23, "fiend", ["demon", "labyrinth", "charge", "fear"], ["abyss", "minotaur-lairs"]),
  Monster("Bard", 2, "humanoid", ["spellcaster", "inspiration"], ["tavern", "city"]),
  Monster("Barghest", 4, "fiend", ["goblin-shifter", "consume-soul", "invisibility"], ["goblin-lairs", "hills"]),
  Monster("Basilisk", 3, "monstrosity", ["petrifying-gaze", "poison"], ["caves", "forest"]),
  Monster("Bat", 0, "beast", ["blindsight", "fly"], ["caves", "dungeons"]),
  Monster("Bear, Black", 1/2, "beast", ["claws", "keen-smell"], ["forest", "mountains"]),
  Monster("Bear, Brown", 1, "beast", ["claws", "keen-smell"], ["forest", "mountains"]),
  Monster("Bear, Cave", 2, "beast", ["claws", "keen-smell"], ["caves", "arctic"]),
  Monster("Bear, Polar", 2, "beast", ["claws", "swim"], ["arctic", "coastal"]),
  Monster("Behir", 11, "monstrosity", ["lightning-breath", "swallow", "climb"], ["caves", "mountains"]),
  Monster("Beholder", 13, "aberration", ["antimagic-cone", "eye-rays", "fly"], ["underdark", "lairs"]),
  Monster("Beholder Zombie", 5, "undead", ["eye-rays", "fly", "undead-fortitude"], ["dungeons", "underdark"]),
  Monster("Berbalang", 2, "undead", ["etherealness", "soul-form", "copy-attack"], ["ruins", "other-planes"]),
  Monster("Bheur Hag", 7, "fey", ["winter-magic", "blizzard", "ice-hook"], ["arctic", "mountains"]),
  Monster("Blackguard", 8, "humanoid", ["smite", "evil-spells", "mount"], ["fortress", "swamp"]),
  Monster("Black Pudding", 4, "ooze", ["corrosive", "split", "amorphous"], ["dungeons", "underdark"]),
  Monster("Blink Dog", 1/4, "fey", ["teleport", "pack-tactics"], ["forest", "plains"]),
  Monster("Blood Hawk", 1/8, "beast", ["pack-tactics", "fly", "keen-sight"], ["mountains", "plains"]),
  Monster("Bodak", 6, "undead", ["death-gaze", "sunlight-vulnerability"], ["wasteland", "ruins"]),
  Monster("Boggle", 1/8, "fey", ["oily-spill", "dimensional-rift", "gluey-oil"], ["feywild", "sewers"]),
  Monster("Boneclaw", 12, "undead", ["shadow-teleport", "grapple", "rejuvenation"], ["shadowfell", "graveyard"]),
  Monster("Brass Dragon, Wyrmling", 1, "dragon", ["sleep-gas", "fire-breath"], ["desert", "caves"]),
  Monster("Brass Dragon, Young", 6, "dragon", ["sleep-gas", "fire-breath"], ["desert", "caves"]),
  Monster("Bronze Dragon, Wyrmling", 2, "dragon", ["lightning-breath", "repulsion-breath"], ["coastal", "caves"]),
  Monster("Bronze Dragon, Young", 8, "dragon", ["lightning-breath", "repulsion-breath"], ["coastal", "caves"]),
  Monster("Bulette", 5, "monstrosity", ["land-shark", "leap", "burrow"], ["plains", "hills"]),
  Monster("Bugbear", 1, "humanoid", ["stealth", "surprise-attack", "pack-tactics"], ["forest", "dungeons"]),
  Monster("Bugbear Chief", 3, "humanoid", ["commander", "stealth", "martial-advantage"], ["fortress", "dungeons"]),
  Monster("Bulezau", 3, "fiend", ["demon", "infectious-wounds", "disease"], ["abyss", "wasteland"]),


  Monster("Cadaver Collector", 14, "construct", ["summoner", "paralysis", "undead-minion"], ["battlefield", "wasteland"]),
  Monster("Cambion", 5, "fiend", ["flying", "charmer", "spellcaster"], ["hell", "abyss", "urban"]),
  Monster("Camel", 1/8, "beast", ["mount", "desert-dweller"], ["desert"]),
  Monster("Canoloth", 8, "fiend", ["yugoloth", "tracker", "tongue-attack"], ["abyss", "hell", "wasteland"]),
  Monster("Carrion Crawler", 2, "monstrosity", ["paralysis", "climber"], ["dungeon", "underdark", "caves"]),
  Monster("Cat", 0, "beast", ["stealthy"], ["urban", "forest"]),
  Monster("Catoblepas", 5, "monstrosity", ["stench", "death-ray"], ["swamp"]),
  Monster("Cave Fisher", 3, "monstrosity", ["ambusher", "filament", "climber"], ["underdark", "caves"]),
  Monster("Centaur (MotM)", 3, "fey", ["charger", "ranged", "survivalist"], ["forest", "plains"]),
  Monster("Chain Devil (Kyton)", 8, "fiend", ["devil", "chains", "animator"], ["hell"]),
  Monster("Chimera", 6, "monstrosity", ["flying", "fire-breath", "multi-headed"], ["hills", "mountains"]),
  Monster("Chitine", 1/2, "monstrosity", ["web", "ambusher", "pack"], ["underdark"]),
  Monster("Choker", 1, "aberration", ["ambusher", "climber", "grappler"], ["dungeon", "underdark"]),
  Monster("Choldrith", 3, "monstrosity", ["priestess", "spellcaster", "web"], ["underdark"]),
  Monster("Chuul", 4, "aberration", ["aquatic", "paralysis", "grappler"], ["underdark", "swamp", "coast"]),
  Monster("Clay Golem", 9, "construct", ["berserk", "magic-immunity", "brute"], ["dungeon", "ruins"]),
  Monster("Cloaker", 8, "aberration", ["ambusher", "flying", "shadow-dweller"], ["underdark", "dungeon"]),
  Monster("Clockwork Bronze Scout", 1, "construct", ["scout", "armored", "poison-gas"], ["dungeon", "urban"]),
  Monster("Clockwork Iron Cobra", 4, "construct", ["stealthy", "poison-bite", "construct"], ["dungeon", "urban", "desert"]),
  Monster("Clockwork Oaken Bolter", 5, "construct", ["siege", "ranged", "construct"], ["battlefield", "forest"]),
  Monster("Clockwork Stone Defender", 4, "construct", ["guardian", "resilient", "construct"], ["dungeon", "urban", "ruins"]),
  Monster("Cloud Giant", 9, "giant", ["flying-castle", "spellcaster", "brute"], ["mountains", "sky"]),
  Monster("Cockatrice", 1/2, "monstrosity", ["flying", "petrification"], ["plains", "hills"]),
  Monster("Commoner", 0, "humanoid", ["civilian"], ["urban", "plains"]),
  Monster("Corpse Flower", 8, "plant", ["zombie-harvester", "stench", "brute"], ["swamp", "jungle", "forest"]),
  Monster("Couatl", 4, "celestial", ["flying", "spellcaster", "shapeshifter"], ["forest", "plains"]),
  Monster("Crab", 0, "beast", ["aquatic", "swarm"], ["coast"]),
  Monster("Cranium Rat", 5, "beast", ["swarm", "psionic", "telepathic"], ["dungeon", "sewer", "urban"]),
  Monster("Crawling Claw", 0, "undead", ["climber", "construct-like"], ["dungeon", "urban"]),
  Monster("Cultist", 1/8, "humanoid", ["fanatic", "pack"], ["urban", "ruins"]),
  Monster("Cult Fanatic", 2, "humanoid", ["leader", "spellcaster", "fanatic"], ["urban", "ruins", "dungeon"]),
  Monster("Cyclops", 6, "giant", ["brute", "single-eye"], ["hills", "coast", "mountains"]),

  Monster("Darkling", 2, "fey", ["light-vulnerability", "death-flash", "stealth"], ["underdark", "forest"]),
  Monster("Darkling Elder", 6, "fey", ["light-vulnerability", "death-flash", "shadow-magic"], ["underdark", "ruins"]),
  Monster("Darkmantle", 1/2, "monstrosity", ["darkness-aura", "stealth", "suffocation"], ["caves", "dungeons"]),
  Monster("Death Kiss", 10, "aberration", ["blood-drain", "lightning-tentacles", "fly"], ["underdark", "caves"]),
  Monster("Deathlock", 4, "undead", ["warlock-magic", "shadow-teleport"], ["ruins", "dungeons"]),
  Monster("Deathlock Mastermind", 8, "undead", ["mastermind", "warlock-magic", "teleport"], ["hidden-lair", "city"]),
  Monster("Deathlock Wight", 3, "undead", ["life-drain", "warlock-magic"], ["graveyard", "dungeons"]),
  Monster("Deep Scion", 3, "humanoid", ["amphibious", "charming-gaze", "shapeshift"], ["underwater", "coastal"]),
  Monster("Demogorgon", 26, "fiend", ["demon-prince", "madness-gaze", "two-heads"], ["abyss", "cultist-lair"]),
  Monster("Derro", 1/4, "humanoid", ["madness", "light-sensitivity", "poison"], ["underdark", "tunnels"]),
  Monster("Derro Savant", 3, "humanoid", ["madness", "spellcaster", "light-sensitivity"], ["underdark", "settlement"]),
  Monster("Deva", 10, "celestial", ["healing", "radiant-damage", "shapeshift"], ["upper-planes", "sky"]),
  Monster("Devourer", 13, "fiend", ["soul-hunger", "soul-capture", "teleport"], ["lower-planes", "battlefield"]),
  Monster("Dhergoloth", 7, "fiend", ["yugoloth", "fear", "battle-prowess"], ["lower-planes", "war-zone"]),
  Monster("Dinosaur, Allosaurus", 2, "beast", ["pounce", "ferocious"], ["jungle", "lost-world"]),
  Monster("Dinosaur, Brontosaurus", 5, "beast", ["gargantuan", "stomp"], ["jungle", "lost-world"]),
  Monster("Dinosaur, Deinonychus", 1, "beast", ["pounce", "pack-tactics"], ["jungle", "lost-world"]),
  Monster("Dinosaur, Dimetrodon", 1/4, "beast", ["bite", "aquatic"], ["swamp", "coastal"]),
  Monster("Dinosaur, Hadrosaurus", 1/4, "beast", ["herbivore", "herd"], ["grassland", "jungle"]),
  Monster("Dinosaur, Quetzalcoatlus", 2, "beast", ["flight", "swoop"], ["mountain", "coastal"]),
  Monster("Dinosaur, Stegosaurus", 4, "beast", ["tail-spikes", "armored"], ["grassland", "lost-world"]),
  Monster("Dinosaur, Triceratops", 5, "beast", ["charge", "horn-attack"], ["grassland", "jungle"]),
  Monster("Dinosaur, Tyrannosaurus Rex", 8, "beast", ["huge", "swallow", "bite"], ["jungle", "lost-world"]),
  Monster("Dinosaur, Velociraptor", 1/4, "beast", ["pack-tactics", "pounce"], ["jungle", "lost-world"]),
  Monster("Displacer Beast", 3, "monstrosity", ["illusion", "tentacles", "displace"], ["forest", "caves"]),
  Monster("Djinn", 5, "elemental", ["air-form", "whirlwind-attack", "wish"], ["elemental-plane-of-air", "sky"]),
  Monster("Dolphin", 1/8, "beast", ["aquatic", "keen-hearing", "pod-tactics"], ["ocean", "coastal"]),
  Monster("Dolphin Delighter", 1/8, "fey", ["aquatic", "innate-spellcasting", "charming-song"], ["feywild", "ocean"]),
  Monster("Doppelganger", 3, "monstrosity", ["shapeshifter", "telepathy", "read-thoughts"], ["city", "sewers"]),
  Monster("Draft Horse", 1/4, "beast", ["carry-load", "sturdy"], ["farm", "road"]),
  Monster("Dracolich", 17, "undead", ["dragon", "lich", "necrotic-breath"], ["hoard", "ruins"]),
  Monster("Drider", 6, "monstrosity", ["spider-climb", "poison-weapon", "spellcaster"], ["underdark", "drow-city"]),
  Monster("Drow", 1/4, "humanoid", ["darkness-spell", "sunlight-sensitivity", "poison"], ["underdark", "drow-city"]),
  Monster("Drow Arachnomancer", 14, "humanoid", ["spider-magic", "summoner", "drow-ally"], ["underdark", "temple"]),
  Monster("Drow Favored Consort", 10, "humanoid", ["commander", "noble", "magic-item"], ["underdark", "palace"]),
  Monster("Drow House Captain", 9, "humanoid", ["commander", "martial-superiority", "venom"], ["underdark", "fortress"]),
  Monster("Drow Inquisitor", 8, "humanoid", ["divination", "telepathy", "detect-lie"], ["underdark", "prison"]),
  Monster("Drow Matron Mother", 20, "humanoid", ["high-priestess", "epic-spellcasting", "demon-ally"], ["underdark", "main-temple"]),
  Monster("Drow Priestess of Lolth", 8, "humanoid", ["spider-summoner", "spellcaster", "whip"], ["underdark", "temple"]),
  Monster("Drow Shadowblade", 11, "humanoid", ["shadow-step", "assassinate", "poison-weapon"], ["underdark", "city-streets"]),
  Monster("Dryad", 1, "fey", ["tree-step", "charm", "innate-spellcasting"], ["forest", "sacred-grove"]),
  Monster("Duergar", 1, "humanoid", ["invisibility", "enlarge", "light-sensitivity"], ["underdark", "dwarven-ruins"]),
  Monster("Duergar Despot", 12, "humanoid", ["commander", "psionics", "guardian-duergar"], ["underdark", "throne-room"]),
  Monster("Duergar Hammerer", 2, "humanoid", ["tremor-sense", "hammer-throw", "light-sensitivity"], ["underdark", "mines"]),
  Monster("Duergar Kavalrachni", 2, "humanoid", ["steeder-rider", "lance", "pack-tactics"], ["underdark", "caves"]),
  Monster("Duergar Mind Master", 2, "humanoid", ["psionics", "illusion", "telepathy"], ["underdark", "settlement"]),
  Monster("Duergar Screamer", 5, "humanoid", ["sonic-attack", "light-sensitivity", "exploding"], ["underdark", "mines"]),
  Monster("Duergar Soulblade", 4, "humanoid", ["psionic-weapon", "teleport", "duergar-ally"], ["underdark", "city-streets"]),
  Monster("Duergar Stone Guard", 2, "humanoid", ["shield", "stone-camoflage", "light-sensitivity"], ["underdark", "fortress"]),
  Monster("Duergar Warlord", 6, "humanoid", ["commander", "martial-advantage", "battle-axe"], ["underdark", "barracks"]),
  Monster("Duergar Xarrorn", 2, "humanoid", ["fire-damage", "flame-weapon", "heat-resistance"], ["underdark", "lava-tubes"]),
  Monster("Dybbuk", 8, "fiend", ["demon", "possession", "fly"], ["lower-planes", "haunted-place"]),

  Monster("Eagle", 0, "beast", ["fly", "keen-sight", "talons"], ["mountain", "sky"]),
  Monster("Eidolon", 12, "undead", ["possess-statue", "incorporeal", "undead-minion"], ["temple", "ruins"]),
  Monster("Eladrin, Autumn", 10, "fey", ["fey-step", "charm", "wither"], ["feywild", "forest"]),
  Monster("Eladrin, Spring", 10, "fey", ["fey-step", "teleport-others", "healing"], ["feywild", "forest"]),
  Monster("Eladrin, Summer", 10, "fey", ["fey-step", "fire", "frightful-presence"], ["feywild", "forest"]),
  Monster("Eladrin, Winter", 10, "fey", ["fey-step", "cold", "fear"], ["feywild", "forest"]),
  Monster("Elder Brain", 14, "aberration", ["telepathy", "spellcasting", "psionics"], ["underdark", "mind-flayer-colony"]),
  Monster("Elder Tempest", 23, "elemental", ["storm", "lightning", "flight"], ["elemental-plane-of-air", "sky"]),
  Monster("Elemental, Air", 5, "elemental", ["whirlwind", "flight", "incorporeal"], ["elemental-plane-of-air", "sky"]),
  Monster("Elemental, Earth", 5, "elemental", ["tremorsense", "burrow", "damage-resistance"], ["elemental-plane-of-earth", "caves"]),
  Monster("Elemental, Fire", 5, "elemental", ["fire-aura", "fire-form", "burn"], ["elemental-plane-of-fire", "volcano"]),
  Monster("Elemental, Water", 5, "elemental", ["whelm", "swim", "water-form"], ["elemental-plane-of-water", "coastal"]),
  Monster("Elemental Myrmidon, Air", 7, "construct", ["elemental-armor", "lightning-weapon", "whirlwind"], ["any-plane", "fortress"]),
  Monster("Elemental Myrmidon, Earth", 7, "construct", ["elemental-armor", "ground-slam", "burrow"], ["any-plane", "fortress"]),
  Monster("Elemental Myrmidon, Fire", 7, "construct", ["elemental-armor", "fire-weapon", "heated-body"], ["any-plane", "fortress"]),
  Monster("Elemental Myrmidon, Water", 7, "construct", ["elemental-armor", "water-whip", "freeze-water"], ["any-plane", "fortress"]),
  Monster("Empyrean", 23, "celestial", ["divine-magic", "rock-throwing", "god-kin"], ["upper-planes", "mountain-top"]),
  Monster("Erinyes", 12, "fiend", ["devil", "flying", "rope-of-entanglement", "longsword"], ["nine-hells", "battlefield"]),
  Monster("Ettercap", 2, "monstrosity", ["web-shooter", "spider-ally", "poison"], ["forest", "caves"]),
  Monster("Ettin", 4, "giant", ["two-heads", "morningstar", "javelin"], ["hill", "caves"]),
  Monster("Evil Mage", 9, "humanoid", ["spellcaster", "necromancy", "fireball"], ["tower", "dungeons"]),

  Monster("Faerie Dragon (Red, Young)", 1, "dragon", ["chromatic", "innate-spellcasting", "invisibility"], ["forest", "feywild"]),
  Monster("Faerie Dragon (Orange, Young)", 2, "dragon", ["chromatic", "innate-spellcasting", "invisibility"], ["forest", "feywild"]),
  Monster("Faerie Dragon (Yellow, Adult)", 3, "dragon", ["chromatic", "innate-spellcasting", "invisibility"], ["forest", "feywild"]),
  Monster("Faerie Dragon (Green, Adult)", 4, "dragon", ["chromatic", "innate-spellcasting", "invisibility"], ["forest", "feywild"]),
  Monster("Faerie Dragon (Blue, Adult)", 5, "dragon", ["chromatic", "innate-spellcasting", "invisibility"], ["forest", "feywild"]),
  Monster("Faerie Dragon (Indigo, Old)", 6, "dragon", ["chromatic", "innate-spellcasting", "invisibility"], ["forest", "feywild"]),
  Monster("Faerie Dragon (Violet, Old)", 7, "dragon", ["chromatic", "innate-spellcasting", "invisibility"], ["forest", "feywild"]),
  Monster("Fairy", 1/2, "fey", ["flight", "innate-spellcasting", "tiny"], ["feywild", "forest"]),
  Monster("Flail Snail", 3, "elemental", ["shell-defense", "antimagic", "fire-retaliation"], ["underground", "caves"]),
  Monster("Flameskull", 4, "undead", ["fire-magic", "rejuvenation", "fly"], ["tomb", "wizard-tower"]),
  Monster("Flind", 9, "humanoid", ["gnoll", "flail-of-madness", "fear"], ["wasteland", "gnoll-camp"]),
  Monster("Flying Snake", 1/8, "beast", ["fly", "poison"], ["jungle", "swamp"]),
  Monster("Flying Sword", 0, "construct", ["animated", "antimagic-susceptibility", "sword"], ["dungeons", "tomb"]),
  Monster("Fomorian", 8, "giant", ["evil-eye", "cursing", "huge"], ["underdark", "feywild-ruins"]),
  Monster("Fraz-Urb'luu", 23, "fiend", ["demon-prince", "illusion-master", "madness"], ["abyss", "cultist-lair"]),
  Monster("Frog", 0, "beast", ["amphibious", "camouflage"], ["swamp", "forest"]),
  Monster("Froghemoth", 10, "monstrosity", ["multi-attack", "tongue-grapple", "swallow"], ["swamp", "ruins"]),
  Monster("Frost Giant", 8, "giant", ["cold-immunity", "rock-throwing", "axe"], ["arctic", "mountain"]),
  Monster("Frost Giant Everlasting One", 12, "giant", ["cold-immunity", "regeneration", "extra-attack"], ["arctic", "jötunheim"]),
  Monster("Frost Salamander", 16, "elemental", ["cold-aura", "claws", "fire-vulnerability"], ["arctic", "elemental-plane-of-water"]),

  Monster("Gargoyle", 4, "elemental", ["statue-camouflage", "flight", "damage-resistance"], ["ruins", "mountain"]),
  Monster("Gauth", 6, "aberration", ["beholder-kin", "eye-rays", "eat-magic"], ["underdark", "dungeons"]),
  Monster("Gazer", 1/2, "aberration", ["beholder-kin", "eye-rays", "mimicry", "fly"], ["dungeons", "underdark"]),
  Monster("Gelatinous Cube", 2, "ooze", ["engulf", "transparent", "acid"], ["dungeons", "sewers"]),
  Monster("Genie, Dao", 11, "elemental", ["earth-form", "burrow", "wish"], ["elemental-plane-of-earth", "caves"]),
  Monster("Genie, Djinni", 5, "elemental", ["air-form", "whirlwind", "wish"], ["elemental-plane-of-air", "sky"]),
  Monster("Genie, Efreeti", 15, "elemental", ["fire-form", "heat-aura", "wish"], ["elemental-plane-of-fire", "volcano"]),
  Monster("Genie, Marid", 11, "elemental", ["water-form", "water-mastery", "wish"], ["elemental-plane-of-water", "ocean"]),
  Monster("Geryon", 22, "fiend", ["archdevil", "battle-mastery", "poison-tail", "fly"], ["nine-hells", "icy-wasteland"]),
  Monster("Ghast", 2, "undead", ["stink", "claws", "undead-trait"], ["graveyard", "crypt"]),
  Monster("Ghost", 4, "undead", ["incorporeal-movement", "possession", "wailing"], ["haunted-place", "ruins"]),
  Monster("Ghoul", 1, "undead", ["paralyzing-touch", "carrion-eater"], ["graveyard", "crypt"]),
  Monster("Giant Ape", 7, "beast", ["rock-throwing", "huge", "fist"], ["jungle", "mountain"]),
  Monster("Giant Badger", 1/4, "beast", ["burrow", "keen-smell", "rage"], ["forest", "plains"]),
  Monster("Giant Bat", 1, "beast", ["echolocation", "fly"], ["caves", "swamp"]),
  Monster("Giant Boar", 2, "beast", ["charge", "tusk"], ["forest", "plains"]),
  Monster("Giant Centipede", 1/4, "beast", ["poison-bite", "climb"], ["dungeons", "caves"]),
  Monster("Giant Constrictor Snake", 2, "beast", ["constrict", "grapple"], ["jungle", "swamp"]),
  Monster("Giant Crab", 1/8, "beast", ["amphibious", "grapple"], ["coastal", "ocean"]),
  Monster("Giant Crocodile", 5, "beast", ["underwater-grapple", "death-roll", "stealth"], ["swamp", "river"]),
  Monster("Giant Eagle", 1, "beast", ["fly", "keen-sight", "talons"], ["mountain", "sky"]),
  Monster("Giant Elk", 2, "beast", ["trampling-charge", "antlers"], ["forest", "tundra"]),
  Monster("Giant Fire Beetle", 0, "beast", ["light-production"], ["caves", "underground"]),
  Monster("Giant Frog", 1/4, "beast", ["swallow", "grapple-tongue", "stealth"], ["swamp", "river"]),
  Monster("Giant Goat", 1/2, "beast", ["charge", "sure-footed"], ["mountain", "hill"]),
  Monster("Giant Hyena", 1, "beast", ["pack-tactics", "cackle"], ["plains", "desert"]),
  Monster("Giant Lizard", 1/4, "beast", ["climb", "swim"], ["dungeons", "caves"]),
  Monster("Giant Octopus", 4, "beast", ["underwater-grapple", "ink-cloud", "jet"], ["ocean", "coastal"]),
  Monster("Giant Owl", 1/4, "beast", ["fly", "keen-hearing", "stealth"], ["forest", "night-sky"]),
  Monster("Giant Poisonous Snake", 1/4, "beast", ["poison-bite"], ["jungle", "swamp"]),
  Monster("Giant Rat", 1/8, "beast", ["pack-tactics", "disease"], ["sewers", "city"]),
  Monster("Giant Scorpion", 3, "beast", ["poison-sting", "grapple"], ["desert", "dungeons"]),
  Monster("Giant Sea Horse", 1, "beast", ["underwater-charge"], ["ocean", "coastal"]),
  Monster("Giant Shark", 5, "beast", ["blood-frenzy", "aquatic"], ["ocean", "deep-sea"]),
  Monster("Giant Spider", 1, "beast", ["web-shooter", "poison-bite", "climb"], ["forest", "caves"]),
  Monster("Giant Strider", 2, "beast", ["fire-resistance", "heated-body", "jump"], ["volcano", "wastes"]),
  Monster("Giant Toad", 1, "beast", ["swallow", "grapple-tongue"], ["swamp", "river"]),
  Monster("Giant Vulture", 4, "beast", ["carrion-eater", "pack-tactics", "fly"], ["plains", "mountain"]),
  Monster("Giant Weasel", 1/8, "beast", ["keen-smell", "bite"], ["forest", "plains"]),
  Monster("Gibbering Mouther", 2, "aberration", ["gibbering", "blinding", "many-mouths"], ["underground", "swamp"]),
  Monster("Giff", 3, "humanoid", ["firearms", "hippopotamus-head", "space-travel"], ["any-plane", "spelljammer"]),
  Monster("Girallon", 4, "beast", ["four-arms", "climb", "rage"], ["jungle", "forest"]),
  Monster("Githyanki Gish", 10, "humanoid", ["psionics", "greatsword", "spellcasting"], ["astral-plane", "creche"]),
  Monster("Githyanki Kith'rak", 12, "humanoid", ["commander", "psionics", "silver-sword"], ["astral-plane", "fortress"]),
  Monster("Githyanki Supreme Commander", 14, "humanoid", ["general", "psionics", "high-level-magic"], ["astral-plane", "githyanki-city"]),
  Monster("Githzerai Anarch", 16, "humanoid", ["psionics", "teleport", "plane-shift", "monk"], ["limbo", "monastery"]),
  Monster("Githzerai Enlightened", 14, "humanoid", ["psionics", "monk-master", "foresight"], ["limbo", "monastery"]),
  Monster("Githzerai Zerth", 11, "humanoid", ["psionics", "teleport", "monk-magic"], ["limbo", "monastery"]),
  Monster("Gnoll", 1/2, "humanoid", ["rampage", "pack-tactics", "carrion"], ["wasteland", "plains"]),
  Monster("Gnoll Flesh Gnawer", 1, "humanoid", ["gnoll", "lunge", "rampage"], ["wasteland", "raid"]),
  Monster("Gnoll Hunter", 3, "humanoid", ["gnoll", "ranged-attack", "rampage"], ["wasteland", "scout"]),
  Monster("Gnoll Witherling", 1/4, "undead", ["gnoll", "mindless-undead", "rampage"], ["wasteland", "battlefield"]),
  Monster("Goat", 0, "beast", ["charge", "sure-footed"], ["mountain", "hill"]),
  Monster("Goblin", 1/4, "humanoid", ["nimble-escape", "stealth"], ["caves", "forest"]),
  Monster("Goblin Boss", 1, "humanoid", ["nimble-escape", "commander", "wound"], ["caves", "camp"]),
  Monster("Golem, Clay", 9, "construct", ["amulet-of-life", "damage-immunity", "haste"], ["dungeons", "temple"]),
  Monster("Golem, Flesh", 5, "construct", ["lightning-absorption", "random-behavior", "damage-immunity"], ["laboratory", "graveyard"]),
  Monster("Golem, Iron", 16, "construct", ["poison-breath", "damage-immunity", "fire-absorption"], ["fortress", "dungeons"]),
  Monster("Golem, Stone", 10, "construct", ["slow-gaze", "damage-immunity", "magic-resistance"], ["tomb", "temple"]),
  Monster("Gorgon", 5, "monstrosity", ["petrifying-breath", "charge", "metal-bull"], ["plains", "mountain"]),
  Monster("Gray Ooze", 1/2, "ooze", ["corrode-metal", "pseudopod-attack", "blindsight"], ["dungeons", "sewers"]),
  Monster("Gray Render", 12, "monstrosity", ["bond-mate", "guardian", "frightful-presence"], ["caves", "ruins"]),
  Monster("Graz'zt", 22, "fiend", ["demon-prince", "spellcasting", "charming-presence"], ["abyss", "extravagant-lair"]),
  Monster("Green Hag", 3, "fey", ["mimicry", "innate-spellcasting", "coven"], ["swamp", "forest"]),
  Monster("Grell", 3, "aberration", ["fly", "paralysis-tentacles", "acid"], ["underdark", "dungeons"]),
  Monster("Grick", 2, "monstrosity", ["stone-camouflage", "tentacles"], ["caves", "underground"]),
  Monster("Grick Alpha", 7, "monstrosity", ["stone-camouflage", "leader", "venom"], ["caves", "underground"]),
  Monster("Griffon", 2, "monstrosity", ["fly", "keen-sight", "swoop"], ["mountain", "sky"]),
  Monster("Grimlock", 1/4, "humanoid", ["blindsight", "stone-camouflage", "cannibal"], ["underdark", "caves"]),
  Monster("Grung", 1/4, "humanoid", ["amphibious", "poison-skin", "leap"], ["jungle", "forest"]),
  Monster("Grung Elite Warrior", 2, "humanoid", ["poison-darts", "commander", "jump"], ["jungle", "camp"]),
  Monster("Grung Wildling", 1, "humanoid", ["spellcaster", "poison-weapon", "amphibious"], ["jungle", "ritual-site"]),
  Monster("Guard", 1/8, "humanoid", ["spear", "profession"], ["city", "fortress"]),
  Monster("Guard Drake", 2, "dragon", ["guardian", "acid-breath"], ["fortress", "dungeons"]),

  Monster("Half-Red Dragon Veteran", 5, "humanoid", ["fire-resistance", "fire-breath", "martial-advantage"], ["fortress", "lair"]),
  Monster("Harpy", 1, "monstrosity", ["luring-song", "fly", "talons"], ["coastal", "mountain"]),
  Monster("Hawk", 0, "beast", ["fly", "keen-sight"], ["any-where", "sky"]),
  Monster("Heavy Horse", 2, "beast", ["equine", "kick"], ["farm", "road"]),
  Monster("Hell Hound", 3, "fiend", ["fire-breath", "pack-tactics", "fire-immune"], ["hells", "volcano"]),
  Monster("Hellfire Engine", 16, "construct", ["fire-cannon", "hellfire-breath", "siege-monster"], ["nine-hells", "battlefield"]),
  Monster("Hippogriff", 1, "monstrosity", ["fly", "keen-sight", "talons"], ["mountain", "sky"]),
  Monster("Hobgoblin", 1/2, "humanoid", ["martial-advantage", "leader", "formation"], ["fortress", "camp"]),
  Monster("Hobgoblin Captain", 3, "humanoid", ["martial-advantage", "commander", "battle-ready"], ["fortress", "camp"]),
  Monster("Hobgoblin Devastator", 9, "humanoid", ["spellcaster", "arcane-advantage", "area-of-effect"], ["fortress", "war-camp"]),
  Monster("Hobgoblin Iron Shadow", 2, "humanoid", ["stealth", "shadow-teleport", "unarmed-defense"], ["fortress", "assassination"]),
  Monster("Hobgoblin Warlord", 6, "humanoid", ["martial-advantage", "leader", "rallying-cry"], ["fortress", "battlefield"]),
  Monster("Homunculus", 0, "construct", ["telepathic-bond", "alchemical-creation", "fly"], ["wizard-tower", "laboratory"]),
  Monster("Hook Horror", 3, "monstrosity", ["echolocation", "climb", "hook-attack"], ["underdark", "caves"]),
  Monster("Howler", 8, "fiend", ["fear-howl", "teleport", "chaotic-evil"], ["abyss", "battlefield"]),
  Monster("Hydra", 8, "monstrosity", ["multi-head", "head-regrowth", "multi-attack"], ["swamp", "mountain"]),
  Monster("Hydroloth", 9, "fiend", ["yugoloth", "water-travel", "spellcasting"], ["elemental-plane-of-water", "river"]),
  Monster("Hyena", 0, "beast", ["pack-tactics", "cackle"], ["plains", "desert"]),

  Monster("Ice Devil", 14, "fiend", ["devil", "ice-chain", "fear-aura", "fly"], ["nine-hells", "icy-plain"]),
  Monster("Imp", 1, "fiend", ["devil", "shapeshift", "invisibility", "sting"], ["nine-hells", "mortal-plane"]),
  Monster("Incubus/Succubus", 8, "fiend", ["shapeshift", "charm", "drain-life", "telepathic"], ["any-plane", "city"]),
  Monster("Intellect Devourer", 2, "aberration", ["brain-siphon", "body-thief", "telepathy"], ["underdark", "mind-flayer-colony"]),
  Monster("Invisible Stalker", 6, "elemental", ["invisible", "air-form", "air-mastery"], ["elemental-plane-of-air", "sky"]),
  Monster("Iron Golem", 16, "construct", ["poison-breath", "damage-immunity", "fire-absorption"], ["fortress", "dungeons"]),

  Monster("Jackal", 0, "beast", ["keen-hearing-smell", "pack-tactics"], ["plains", "desert"]),
  Monster("Jackalwere", 1/2, "humanoid", ["shapeshift", "sleep-gaze", "bite"], ["city", "desert"]),
  Monster("Jaculi", 1/2, "beast", ["ambush-from-above", "coil"], ["jungle", "forest"]),
  Monster("Jellyfish", 0, "beast", ["aquatic", "poison-sting"], ["ocean", "coastal"]),
  Monster("Juiblex", 23, "fiend", ["demon-lord-of-oozes", "acid-aura", "engulf", "teleport"], ["abyss", "slimy-dungeon"]),
  Monster("Jubilex", 23, "fiend", ["demon-lord-of-oozes", "acid-aura", "engulf", "teleport"], ["abyss", "slimy-dungeon"]),

  Monster("Kenku", 1/4, "humanoid", ["mimicry", "expert-forgery", "tricks"], ["city", "sewers"]),
  Monster("Ki-rin", 12, "celestial", ["healing-touch", "legendary-resistance", "magic-weapons", "fly"], ["mountain-tops", "upper-planes"]),
  Monster("Kobold", 1/8, "humanoid", ["pack-tactics", "sunlight-sensitivity", "trap-builder"], ["caves", "dungeons"]),
  Monster("Kobold Dragonshield", 1, "humanoid", ["shield-master", "protect-leader", "kobold-kin"], ["caves", "dungeons"]),
  Monster("Kobold Inventor", 1/4, "humanoid", ["kobold-contraptions", "trap-master", "pack-tactics"], ["caves", "workshop"]),
  Monster("Kobold Scale Sorcerer", 1, "humanoid", ["spellcasting", "sorcery", "kobold-kin"], ["caves", "ritual-site"]),
  Monster("Korred", 7, "fey", ["animate-hair", "stone-mastery", "dance-of-wounding"], ["forest", "mountain"]),
  Monster("Kraken", 23, "monstrosity", ["gargantuan", "lightning-storm", "ink-cloud", "tentacles"], ["deep-ocean", "coastal"]),
  Monster("Kraken Priest", 5, "humanoid", ["spellcasting", "prophet-of-kraken", "underwater-focus"], ["coastal", "sunken-temple"]),
  Monster("Kruthik, Young", 1/2, "monstrosity", ["acid-spit", "tunnel-travel", "pack-tactics"], ["underdark", "hive"]),
  Monster("Kruthik, Adult", 2, "monstrosity", ["acid-spit", "tunnel-travel", "swarm-tactics"], ["underdark", "hive"]),
  Monster("Kruthik Hive Lord", 5, "monstrosity", ["acid-spit", "commander", "multi-attack"], ["underdark", "hive"]),
  Monster("Kuo-toa", 1/4, "humanoid", ["slippery", "net-attack", "grotto-creations"], ["underdark", "underwater"]),
  Monster("Kuo-toa Archpriest", 6, "humanoid", ["amphibious", "spellcasting", "blessing-of-the-goddess"], ["underdark", "temple"]),
  Monster("Kuo-toa Whip", 1, "humanoid", ["amphibious", "whip-attack", "leader"], ["underdark", "grotto"]),

  Monster("Lamia", 4, "monstrosity", ["charming-touch", "innate-spellcasting", "curse"], ["desert", "ruins"]),
  Monster("Leucrotta", 6, "monstrosity", ["mimicry", "kick-attack", "horse-body"], ["forest", "plains"]),
  Monster("Lemure", 0, "fiend", ["devil", "mindless-servant", "devils-food"], ["nine-hells", "city-streets"]),
  Monster("Leviathan", 20, "elemental", ["gargantuan", "tsunami", "water-mastery"], ["elemental-plane-of-water", "deep-ocean"]),
  Monster("Lich", 21, "undead", ["legendary-actions", "phylactery", "master-spellcaster"], ["tomb", "arcane-tower"]),
  Monster("Light Horse", 1/4, "beast", ["equine", "kick"], ["farm", "road"]),
  Monster("Lion", 1, "beast", ["pounce", "pack-tactics", "keen-smell"], ["plains", "savanna"]),
  Monster("Lizard", 0, "beast", ["climb", "tiny"], ["any-where", "dungeons"]),
  Monster("Lizardfolk", 1/2, "humanoid", ["hold-breath", "jaws-attack", "swamp-survival"], ["swamp", "river"]),
  Monster("Lizardfolk Shaman", 2, "humanoid", ["spellcasting", "leadership", "lizard-kin"], ["swamp", "temple"]),
  Monster("Lizardfolk Subchief", 3, "humanoid", ["multiattack", "jaws-attack", "leader"], ["swamp", "camp"]),
  Monster("Lizardfolk King/Queen", 4, "humanoid", ["multiattack", "jaws-attack", "commander"], ["swamp", "throne-room"]),
  Monster("Lizardfolk King/Queen (Mounted)", 5, "humanoid", ["mount-attack", "leader", "multiattack"], ["swamp", "war-party"]),
  Monster("Lycanthrope, Werebear", 5, "humanoid", ["shapeshift", "curse", "bear-form"], ["forest", "mountain"]),
  Monster("Lycanthrope, Wereboar", 4, "humanoid", ["shapeshift", "curse", "boar-form"], ["forest", "farm"]),
  Monster("Lycanthrope, Wererat", 2, "humanoid", ["shapeshift", "curse", "rat-form"], ["city", "sewers"]),
  Monster("Lycanthrope, Weretiger", 4, "humanoid", ["shapeshift", "curse", "tiger-form"], ["jungle", "forest"]),
  Monster("Lycanthrope, Werewolf", 3, "humanoid", ["shapeshift", "curse", "wolf-form"], ["forest", "plains"]),

  Monster("Magma Mephit", 1/2, "elemental", ["lava-skin", "magma-breath", "explosive-death", "fly"], ["volcano", "elemental-plane-of-fire"]),
  Monster("Magmin", 1/2, "elemental", ["ignite-touch", "magma-spray", "fire-immune"], ["volcano", "elemental-plane-of-fire"]),
  Monster("Manticore", 3, "monstrosity", ["spikes-attack", "fly", "lion-human-bat"], ["mountain", "plains"]),
  Monster("Marilith", 16, "fiend", ["demon", "six-arms", "parry", "serpentine-lower-body"], ["abyss", "battlefield"]),
  Monster("Marut", 25, "construct", ["inexorable-justice", "legendary-resistance", "thunder-attack", "teleport"], ["mechanus", "arbitration"]),
  Monster("Martial Arts Adept", 3, "humanoid", ["monk", "unarmed-mastery", "patient-defense"], ["monastery", "city"]),
  Monster("Master Thief", 5, "humanoid", ["rogue", "master-of-disguise", "steal", "sneak-attack"], ["city", "sewers"]),
  Monster("Maurezhi", 7, "fiend", ["demon", "consume-body", "shapeshift", "disease"], ["abyss", "feast"]),
  Monster("Maw Demon", 2, "fiend", ["demon", "insatiable-hunger", "engulf", "frenzy"], ["abyss", "gluttony"]),
  Monster("Meazel", 3, "humanoid", ["shadow-step", "garrote", "soul-siphon"], ["shadowfell", "haunted-place"]),
  Monster("Medusa", 6, "monstrosity", ["petrifying-gaze", "snake-hair", "venomous"], ["ruins", "dungeons"]),
  Monster("Meenlock", 2, "fey", ["fear-aura", "telepathic-harassment", "mind-control"], ["shadowfell", "forest"]),
  Monster("Merfolk", 1/8, "humanoid", ["aquatic", "spear-attack", "ocean-dwellers"], ["ocean", "coastal"]),
  Monster("Merregon", 4, "fiend", ["devil", "battle-formation", "guard-duty", "fire-immune"], ["nine-hells", "fortress"]),
  Monster("Merrow", 2, "monstrosity", ["amphibious", "spear-attack", "savage"], ["ocean", "coastal"]),
  Monster("Merrenoloth", 3, "fiend", ["yugoloth", "ferryman", "oar-attack", "spellcasting"], ["river-styx", "underworld"]),
  Monster("Mimic", 2, "monstrosity", ["shapeshift", "adhesive", "surprise-attack"], ["dungeons", "treasure-room"]),
  Monster("Mind Flayer", 7, "aberration", ["brain-extract", "mind-blast", "psionics"], ["underdark", "colony"]),
  Monster("Mind Flayer Arcanist", 8, "aberration", ["mind-blast", "spellcasting", "psionics"], ["underdark", "colony"]),
  Monster("Mindwitness", 5, "aberration", ["beholder-kin", "tentacles", "psionic-link"], ["underdark", "mind-flayer-colony"]),
  Monster("Minotaur", 3, "monstrosity", ["charge", "labyrinth-master", "horns"], ["dungeons", "maze"]),
  Monster("Moloch", 21, "fiend", ["archdevil", "legendary-resistance", "whip-of-flame", "teleport"], ["nine-hells", "brass-city"]),
  Monster("Molydeus", 21, "fiend", ["demon", "serpent-head", "true-sight", "demon-lord-slayer"], ["abyss", "chaos-realm"]),
  Monster("Morkoth", 11, "aberration", ["teleport", "spell-reflection", "magical-collector"], ["underwater", "lair"]),
  Monster("Mouth of Grolantor", 6, "giant", ["giant-kin", "insatiable-hunger", "rock-throwing"], ["hill", "wasteland"]),
  Monster("Mule", 1/8, "beast", ["sure-footed", "kick"], ["farm", "road"]),
  Monster("Mummy", 3, "undead", ["mummy-rot", "dreadful-gaze", "curse"], ["tomb", "pyramid"]),
  Monster("Mummy Lord", 15, "undead", ["mummy-rot", "legendary-resistance", "command-undead", "spellcasting"], ["tomb", "pyramid"]),
  Monster("Myconid Sprout", 0, "plant", ["pacifist", "spore-burst", "sunlight-sensitive"], ["underdark", "colony"]),
  Monster("Myconid Adult", 1/2, "plant", ["rapport-spores", "distress-spores", "pacifist"], ["underdark", "colony"]),
  Monster("Myconid Sovereign", 2, "plant", ["animating-spores", "telepathic-link", "leader"], ["underdark", "colony"]),
  Monster("Myrmidon, Air Elemental", 7, "elemental", ["fly", "lightning-strike", "whirlwind-attack"], ["elemental-plane-of-air", "battlefield"]),
  Monster("Myrmidon, Earth Elemental", 7, "elemental", ["earth-glide", "ground-shaker", "earth-mastery"], ["elemental-plane-of-earth", "battlefield"]),
  Monster("Myrmidon, Fire Elemental", 7, "elemental", ["fire-aura", "whip-of-flame", "fire-mastery"], ["elemental-plane-of-fire", "battlefield"]),
  Monster("Myrmidon, Water Elemental", 7, "elemental", ["water-form", "whip-of-water", "water-mastery"], ["elemental-plane-of-water", "battlefield"]),

  Monster("Nabassu", 15, "fiend", ["demon", "life-drain-gaze", "shadow-form", "soul-eater"], ["abyss", "mortal-plane"]),
  Monster("Naga, Guardian", 10, "monstrosity", ["venom-spit", "spellcasting", "powerful-protector"], ["temple", "treasury"]),
  Monster("Naga, Spirit", 8, "monstrosity", ["poison-venom", "ethereal-travel", "regeneration"], ["haunted-ruins", "underdark"]),
  Monster("Nagpa", 10, "humanoid", ["vulture-headed-curse", "spellcasting", "hoarder"], ["ruins", "tower"]),
  Monster("Nalfeshnee", 13, "fiend", ["demon", "fear-gaze", "teleport", "brute-strength"], ["abyss", "battlefield"]),
  Monster("Narzugon", 13, "fiend", ["devil", "mounted-combat", "hell-lance", "fire-immune"], ["nine-hells", "battlefield"]),
  Monster("Neogi, Hatchling", 1/8, "aberration", ["mind-flayer-kin", "group-mind", "acid-attack"], ["underdark", "colony"]),
  Monster("Neogi, Adult", 3, "aberration", ["mind-flayer-kin", "enslavement", "poison-bite"], ["underdark", "slave-vessel"]),
  Monster("Neogi, Master", 4, "aberration", ["mind-flayer-kin", "spellcasting", "mind-control"], ["underdark", "command-post"]),
  Monster("Neothelid", 13, "aberration", ["giant-worm", "mind-flayer-kin", "acid-spray", "psionics"], ["underdark", "abandoned-colony"]),
  Monster("Night Hag", 5, "fiend", ["etherealness", "dream-haunting", "heartstone"], ["any-plane", "night-coven"]),
  Monster("Nightmare", 3, "fiend", ["smoke-trail", "etherealness", "fire-damage-hooves"], ["lower-planes", "mortal-plane"]),
  Monster("Nightwalker", 20, "undead", ["life-drain", "soul-harvest", "shadow-teleport"], ["shadowfell", "ancient-tomb"]),
  Monster("Nilbog", 1/4, "fey", ["reverse-healing", "nilbog-luck", "goblin-kin"], ["goblin-camp", "forest"]),
  Monster("Nothic", 3, "aberration", ["weird-insight", "rot-gaze", "dungeon-guardian"], ["dungeons", "ruins"]),
  Monster("Nupperibo", 1/2, "fiend", ["devil", "mindless-hunger", "devils-food"], ["nine-hells", "city-streets"]),

  Monster("Oblex, Spawn", 1/4, "aberration", ["slime-creation", "telepathy", "oath-of-mimicry"], ["underdark", "colony"]),
  Monster("Oblex, Adult", 5, "aberration", ["memory-steal", "acid-attack", "duplicate-victims"], ["underdark", "colony"]),
  Monster("Oblex, Elder", 10, "aberration", ["memory-steal", "superior-duplication", "legendary-actions"], ["underdark", "colony"]),
  Monster("Ochre Jelly", 2, "ooze", ["split", "acid-attack", "electrocution-immunity"], ["dungeons", "caves"]),
  Monster("Octopus", 0, "beast", ["ink-cloud", "hold-breath", "tentacles"], ["ocean", "coastal"]),
  Monster("Ogre", 2, "giant", ["large", "brute-strength", "club"], ["hill", "wasteland"]),
  Monster("Ogre Battering Ram", 4, "giant", ["siege-equipment", "charge", "brute-strength"], ["fortress", "battlefield"]),
  Monster("Ogre Bolt Launcher", 2, "giant", ["siege-equipment", "ballista-crew", "ranged-attack"], ["fortress", "battlefield"]),
  Monster("Ogre Chain Brute", 4, "giant", ["chain-weapon", "reach", "unarmed-attack"], ["dungeons", "fortress"]),
  Monster("Ogre Howdah", 6, "giant", ["platform-carrier", "mounted-archers", "trample"], ["forest", "battlefield"]),
  Monster("Ogre Zombie", 2, "undead", ["slow", "undead-fortitude", "ogre-strength"], ["dungeons", "graveyard"]),
  Monster("Oinoloth", 12, "fiend", ["yugoloth", "plague-bearer", "spellcasting", "teleport"], ["yugoloth-camps", "disease-zone"]),
  Monster("Oni", 7, "giant", ["shapeshift", "innate-spellcasting", "regeneration"], ["fortress", "city"]),
  Monster("Orc", 1/2, "humanoid", ["aggressive", "sunlight-sensitivity", "greataxe"], ["mountain", "camp"]),
  Monster("Orc Claw of Luthic", 2, "humanoid", ["spellcasting", "priestess-of-luthic", "ritual-knife"], ["temple", "camp"]),
  Monster("Orc Hand of Yurtrus", 2, "humanoid", ["disease-carrier", "touch-of-yurtrus", "undead-kin"], ["grave", "camp"]),
  Monster("Orc Nurtured One of Yurtrus", 1/2, "humanoid", ["disease-carrier", "touch-of-yurtrus", "undead-kin"], ["grave", "camp"]),
  Monster("Orc Red Fang of Shargaas", 3, "humanoid", ["stealth", "dagger-master", "shadow-dance"], ["shadow", "dungeons"]),
  Monster("Orc War Chief", 4, "humanoid", ["aggressive", "leader", "greataxe-cleave"], ["fortress", "battlefield"]),
  Monster("Orcus", 26, "fiend", ["demon-lord-of-undead", "wand-of-orcus", "death-power", "legendary"], ["abyss", "undeath-realm"]),
  Monster("Orthon", 10, "fiend", ["devil", "infernal-weaponry", "invisibility-field", "infernal-gaze"], ["nine-hells", "hunt"]),
  Monster("Otyugh", 5, "aberration", ["telepathy", "disease-carrier", "garbage-dweller"], ["dungeons", "sewers"]),
  Monster("Owl", 0, "beast", ["fly", "keen-hearing-sight", "stealth"], ["forest", "night"]),
  Monster("Owlbear", 3, "monstrosity", ["brute-strength", "grizzly-owl-hybrid", "hugs-to-death"], ["forest", "caves"]),
  Monster("Ox", 1/2, "beast", ["large", "charge"], ["farm", "road"]),

  Monster("Pegasus", 2, "celestial", ["fly", "hooves-attack", "noble-steed"], ["mountain-tops", "upper-planes"]),
  Monster("Phoenix", 16, "elemental", ["fire-aura", "fiery-talons", "rebirth"], ["elemental-plane-of-fire", "volcano"]),
  Monster("Piercer", 1/2, "monstrosity", ["false-appearance", "drop-attack", "stalactite"], ["caves", "underdark"]),
  Monster("Plesiosaurus", 2, "beast", ["aquatic", "swift-swimmer", "bite"], ["ocean", "lake"]),
  Monster("Poisonous Snake", 1/8, "beast", ["poison-bite", "stealth"], ["swamp", "forest"]),
  Monster("Pony", 1/8, "beast", ["equine", "kick"], ["farm", "road"]),
  Monster("Pseudodragon", 1/4, "dragon", ["telepathic-link", "sting-poison", "innocent-familiar"], ["forest", "caves"]),
  Monster("Pudding, Black", 4, "ooze", ["acid-damage", "corrosive-form", "split", "climb"], ["dungeons", "sewers"]),
  Monster("Purple Worm", 15, "monstrosity", ["gargantuan", "tremorsense", "swallow", "burrow"], ["underdark", "desert"]),

  Monster("Quadrone", 2, "construct", ["geometric-form", "multiattack", "lawful-machine"], ["mechanus", "fortress"]),
  Monster("Quaggoth", 2, "humanoid", ["claws", "underdark-hunter", "feral-instinct"], ["underdark", "caves"]),
  Monster("Quaggoth Spore Servant", 1, "plant", ["zombified", "fungus-mindless", "underdark"], ["underdark", "myconid-colony"]),
  Monster("Quasit", 1, "fiend", ["demon", "shapeshift", "invisibility", "poison-claws"], ["abyss", "mortal-plane"]),
  Monster("Quetzalcoatlus", 2, "beast", ["fly", "pterosaur", "dive-attack"], ["jungle", "coastal"]),
  Monster("Quickling", 3, "fey", ["super-speed", "dagger-attack", "fey-trickster"], ["forest", "glade"]),
  Monster("Quipper", 0, "beast", ["piscine", "blood-frenzy", "small-swarm"], ["river", "ocean"]),

  Monster("Rakshasa", 13, "fiend", ["innate-spellcasting", "damage-resistance", "mind-reading", "backwards-hands"], ["city", "ruins"]),
  Monster("Rat", 0, "beast", ["disease", "small-swarm"], ["city", "sewers"]),
  Monster("Raven", 0, "beast", ["mimicry", "fly"], ["forest", "city"]),
  Monster("Red Dragon, Wyrmling", 4, "dragon", ["fly", "fire-breath", "hoarder"], ["mountain", "volcano"]),
  Monster("Red Dragon, Young", 10, "dragon", ["fly", "fire-breath", "aggressive"], ["mountain", "volcano"]),
  Monster("Red Dragon, Adult", 17, "dragon", ["fly", "fire-breath", "legendary-actions"], ["mountain", "volcano"]),
  Monster("Red Dragon, Ancient", 24, "dragon", ["fly", "fire-breath", "legendary-actions", "lair-actions"], ["mountain", "volcano"]),
  Monster("Redcap", 3, "fey", ["iron-boots", "blood-lust", "fey-brute"], ["forest", "ancient-ruins"]),
  Monster("Remorhaz, Young", 5, "monstrosity", ["heated-body", "swallow", "cold-immune"], ["arctic", "tundra"]),
  Monster("Remorhaz, Adult", 11, "monstrosity", ["heated-body", "swallow", "cold-immune"], ["arctic", "tundra"]),
  Monster("Retriever", 14, "construct", ["giant-spider-robot", "teleport-prey", "force-vision"], ["outer-planes", "dungeons"]),
  Monster("Rhinoceros", 2, "beast", ["charge", "massive-horn"], ["savanna", "plains"]),
  Monster("Roc", 11, "monstrosity", ["gargantuan", "fly", "talons-attack"], ["mountain", "sky"]),
  Monster("Roper", 5, "monstrosity", ["false-appearance", "lightning-tendrils", "devouring-maw"], ["caves", "dungeons"]),
  Monster("Rug of Smothering", 2, "construct", ["false-appearance", "smother", "mimicry"], ["dungeons", "house"]),
  Monster("Rust Monster", 1/2, "monstrosity", ["antenna-rust", "metal-eater"], ["dungeons", "caves"]),
  Monster("Rutterkin", 5, "fiend", ["demon", "limping-gait", "enraged-attack", "demon-kin"], ["abyss", "battlefield"]),

  Monster("Sahuagin", 3, "humanoid", ["aquatic", "blood-frenzy", "shark-telepathy"], ["ocean", "coastal"]),
  Monster("Sahuagin Baron", 5, "humanoid", ["leader", "four-arms", "shark-telepathy"], ["ocean", "fortress"]),
  Monster("Sahuagin Priestess", 2, "humanoid", ["spellcasting", "shark-telepathy", "leader"], ["temple", "ocean"]),
  Monster("Salamander, Fire", 5, "elemental", ["heated-body", "spear-attack", "fire-immune"], ["volcano", "elemental-plane-of-fire"]),
  Monster("Satyr", 1/2, "fey", ["innate-spellcasting", "fey-charm", "pan-pipes"], ["forest", "glade"]),
  Monster("Scorpion", 0, "beast", ["sting-poison", "claws"], ["desert", "dungeons"]),
  Monster("Sea Hag", 2, "fey", ["horrific-appearance", "death-gaze", "amphibious"], ["coastal", "swamp"]),
  Monster("Sea Horse", 0, "beast", ["aquatic", "tiny"], ["ocean", "reef"]),
  Monster("Sea Spawn", 1, "humanoid", ["amphibious", "transformed-human", "spear-and-net"], ["ocean", "coastal"]),
  Monster("Shadar-Kai Gloom Weaver", 9, "fey", ["shadow-magic", "teleport-shadow", "messenger-of-raven-queen"], ["shadowfell", "ruins"]),
  Monster("Shadar-Kai Shadow Dancer", 7, "fey", ["shadow-dance", "teleport-shadow", "dagger-attack"], ["shadowfell", "ruins"]),
  Monster("Shadar-Kai Soul Monger", 11, "fey", ["soul-siphon", "shadow-step", "spellcasting"], ["shadowfell", "tower"]),
  Monster("Shadow", 1/2, "undead", ["life-drain", "shadow-stealth", "strength-drain"], ["dark-places", "city"]),
  Monster("Shadow Demon", 4, "fiend", ["invisibility", "shadow-form", "claws"], ["abyss", "shadow-realm"]),
  Monster("Shadow Mastiff", 2, "monstrosity", ["shadow-bite", "shadow-stealth", "shadow-hound"], ["shadowfell", "night"]),
  Monster("Shadow Mastiff Alpha", 3, "monstrosity", ["leader", "shadow-bite", "howl-of-despair"], ["shadowfell", "night"]),
  Monster("Shambling Mound", 5, "plant", ["absorb-lightning", "entangle-vines", "false-appearance"], ["swamp", "forest"]),
  Monster("Shield Guardian", 7, "construct", ["magical-warding", "stored-spell", "guardian-amulet"], ["fortress", "dungeons"]),
  Monster("Shoosuva", 8, "fiend", ["demon", "demon-dog", "poison-bite", "charge"], ["abyss", "battlefield"]),
  Monster("Shrieker", 0, "plant", ["false-appearance", "alarm-scream"], ["underdark", "dungeons"]),
  Monster("Sibriex", 20, "fiend", ["demon", "flesh-warping", "legendary-actions", "chaos-lord"], ["abyss", "flesh-pits"]),
  Monster("Silver Dragon, Wyrmling", 5, "dragon", ["fly", "cold-breath", "shapeshift"], ["mountain", "sky"]),
  Monster("Silver Dragon, Young", 13, "dragon", ["fly", "cold-breath", "shapeshift"], ["mountain", "sky"]),
  Monster("Silver Dragon, Adult", 16, "dragon", ["fly", "cold-breath", "legendary-actions"], ["mountain", "sky"]),
  Monster("Silver Dragon, Ancient", 23, "dragon", ["fly", "cold-breath", "legendary-actions", "lair-actions"], ["mountain", "sky"]),
  Monster("Skulk", 1/2, "humanoid", ["perfect-invisibility", "vicious-claws", "mimicry"], ["city", "sewers"]),
  Monster("Skull Lord", 15, "undead", ["undead-lieutenant", "legendary-actions", "spellcasting", "three-skulls"], ["tomb", "fortress"]),
  Monster("Slithering Tracker", 3, "ooze", ["fluid-form", "track-prey", "life-drain"], ["city", "swamp"]),
  Monster("Sorrowsworn, The Angry", 13, "monstrosity", ["enraged-brute", "gloom-attack", "shadowfell-dweller"], ["shadowfell", "ruins"]),
  Monster("Sorrowsworn, The Hungry", 6, "monstrosity", ["insatiable-hunger", "devour", "shadowfell-dweller"], ["shadowfell", "wasteland"]),
  Monster("Sorrowsworn, The Lonely", 9, "monstrosity", ["telepathic-harassment", "shadow-attack", "shadowfell-dweller"], ["shadowfell", "solitude"]),
  Monster("Sorrowsworn, The Lost", 7, "monstrosity", ["unravel-reality", "fear-attack", "shadowfell-dweller"], ["shadowfell", "maze"]),
  Monster("Sorrowsworn, The Wretched", 4, "monstrosity", ["claws-of-gloom", "shadow-step", "shadowfell-dweller"], ["shadowfell", "despair"]),
  Monster("Spawn of Kyuss", 5, "undead", ["worm-infested", "vicious-bite", "worm-creation"], ["grave", "cult-site"]),
  Monster("Specter", 1, "undead", ["incorporeal", "life-drain", "sunlight-vulnerability"], ["haunted-house", "grave"]),
  Monster("Sphinx, Androsphinx", 17, "monstrosity", ["roaring-attack", "innate-spellcasting", "guardian"], ["pyramid", "desert"]),
  Monster("Sphinx, Gynosphinx", 11, "monstrosity", ["enigma", "innate-spellcasting", "riddle-guard"], ["temple", "ruins"]),
  Monster("Spider", 0, "beast", ["climb", "tiny-poison"], ["any-where", "dungeons"]),
  Monster("Spider, Giant", 1/4, "beast", ["web-attack", "poison-bite"], ["caves", "forest"]),
  Monster("Spider, Giant Wolf", 1/4, "beast", ["pack-tactics", "poison-bite", "climb"], ["forest", "caves"]),
  Monster("Sprite", 1/4, "fey", ["invisibility", "heart-poison", "fly"], ["forest", "glade"]),
  Monster("Star Spawn Grue", 1/4, "aberration", ["mind-blast-resist", "group-mind", "alien-horror"], ["outer-plane", "cult-site"]),
  Monster("Star Spawn Hulk", 10, "aberration", ["frenzied-rampage", "alien-fist", "psychic-damage"], ["outer-plane", "cult-site"]),
  Monster("Star Spawn Larva Mage", 16, "aberration", ["spellcasting", "host-body", "psychic-feedback"], ["outer-plane", "cult-site"]),
  Monster("Star Spawn Mangler", 5, "aberration", ["teleport-strike", "multi-claw-attack", "alien-horror"], ["outer-plane", "cult-site"]),
  Monster("Star Spawn Seer", 13, "aberration", ["mind-blast", "spellcasting", "telepathy"], ["outer-plane", "cult-site"]),
  Monster("Steeder, Female", 1, "beast", ["climb-ceiling", "sticky-legs", "jump-attack"], ["underdark", "caves"]),
  Monster("Steeder, Male", 1/4, "beast", ["jump-attack", "small-mount", "sticky-legs"], ["underdark", "caves"]),
  Monster("Steel Predator", 16, "construct", ["infernal-engine", "net-launcher", "multiattack"], ["nine-hells", "battlefield"]),
  Monster("Stirge", 1/8, "beast", ["blood-drain", "fly"], ["caves", "forest"]),
  Monster("Stone Cursed", 7, "construct", ["petrified-body", "slow-moving", "unseen-curse"], ["dungeons", "ancient-ruins"]),
  Monster("Stone Giant", 7, "giant", ["rock-throwing", "stone-camoflage", "dream-walker"], ["mountain", "caves"]),
  Monster("Stone Giant Dreamwalker", 10, "giant", ["spellcasting", "dream-shaper", "rock-throwing"], ["mountain", "dream-realm"]),
  Monster("Storm Giant", 13, "giant", ["lightning-damage", "innate-spellcasting", "master-of-sky"], ["ocean", "mountain"]),
  Monster("Storm Giant Quintessent", 16, "giant", ["lightning-form", "thunder-attack", "legendary-actions"], ["elemental-plane-of-air", "stormy-sky"]),
  Monster("Succubus/Incubus", 8, "fiend", ["shapeshift", "charm", "drain-life"], ["lower-planes", "mortal-plane"]),
  Monster("Swashbuckler", 3, "humanoid", ["finesse-fighter", "cunning-action", "sea-dog"], ["city", "ship"]),
  Monster("Swarm of Bats", 2, "beast", ["swarm", "fly", "echolocation"], ["caves", "night"]),
  Monster("Swarm of Insects (Flies/Mosquitoes)", 0, "beast", ["swarm", "annoyance", "disease"], ["swamp", "forest"]),
  Monster("Swarm of Insects (Locusts)", 1/2, "beast", ["swarm", "devour-crops", "fly"], ["plains", "desert"]),
  Monster("Swarm of Poisonous Snakes", 2, "beast", ["swarm", "poison-bite", "slither"], ["swamp", "jungle"]),
  Monster("Swarm of Quippers", 1, "beast", ["swarm", "blood-frenzy", "aquatic"], ["river", "ocean"]),
  Monster("Swarm of Rats", 1/4, "beast", ["swarm", "disease", "annoyance"], ["city", "sewers"]),
  Monster("Swarm of Ravens", 1/4, "beast", ["swarm", "fly", "talons"], ["forest", "city"]),
  Monster("Swarm of Rot Grubs", 1/2, "beast", ["rot-grubs", "burrow-into-flesh", "fatal-swarm"], ["grave", "dungeons"]),
  Monster("Swarm of Spiders", 1/2, "beast", ["swarm", "web", "climb"], ["caves", "forest"]),
  Monster("Swarm of Wasps", 1/2, "beast", ["swarm", "sting", "fly"], ["forest", "ruins"]),
  Monster("Sword Wraith Commander", 8, "undead", ["wraith-commander", "possession", "sword-master"], ["grave", "battlefield"]),
  Monster("Sword Wraith Warrior", 3, "undead", ["wraith-warrior", "possession", "sword-attack"], ["grave", "battlefield"]),

  Monster("Tanarukk", 5, "fiend", ["demon-hybrid", "frenzied-attack", "fiendish-brute"], ["demon-camp", "wasteland"]),
  Monster("Tarrasque, The", 30, "monstrosity", ["gargantuan-titan", "legendary-resistance", "reflexive-carapace", "swallow"], ["any-where", "calamity"]),
  Monster("Thri-kreen", 1, "humanoid", ["four-arms", "leap-attack", "mantis-kin", "chitinous-armor"], ["desert", "savanna"]),
  Monster("Tiger", 1, "beast", ["pounce", "stealth", "large-cat"], ["jungle", "forest"]),
  Monster("Titivilus", 21, "fiend", ["archdevil-aide", "manipulation", "legendary-actions", "devils-tongue"], ["nine-hells", "court"]),
  Monster("Tlincalli", 5, "monstrosity", ["scorpion-centaur", "poison-sting", "javelin-throw"], ["desert", "wasteland"]),
  Monster("Tortle", 1, "humanoid", ["natural-armor", "hold-breath", "shell-defense"], ["coastal", "island"]),
  Monster("Tortle Druid", 2, "humanoid", ["spellcasting", "wild-shape", "natural-armor"], ["forest", "island"]),
  Monster("Trapper", 3, "monstrosity", ["false-appearance", "ambush-ceiling", "smother"], ["caves", "dungeons"]),
  Monster("Treant", 9, "plant", ["animate-trees", "stomp", "ancient-protector"], ["forest", "woodland"]),
  Monster("Triceratops", 5, "beast", ["dinosaur", "frill-protection", "gore-charge"], ["jungle", "savanna"]),
  Monster("Tridrone", 1, "construct", ["geometric-form", "multiattack", "lawful-machine"], ["mechanus", "fortress"]),
  Monster("Troll", 6, "giant", ["regeneration", "claws-and-bite", "fire-vulnerability"], ["caves", "mountain"]),
  Monster("Troll, Dire", 13, "giant", ["super-regeneration", "powerful-claws", "fire-vulnerability"], ["arctic", "wasteland"]),
  Monster("Troll, Rot", 9, "undead", ["regeneration", "necrotic-claws", "disease"], ["swamp", "grave"]),
  Monster("Troll, Spirit", 11, "giant", ["incorporeal", "ethereal-travel", "regeneration"], ["haunted-place", "forest"]),
  Monster("Troll, Venom", 7, "giant", ["poison-bite", "regeneration", "venomous"], ["swamp", "jungle"]),
  Monster("Turtle, Giant Sea", 8, "beast", ["aquatic", "massive-shell", "bite-attack"], ["ocean", "coastal"]),
  Monster("Tyrannosaurus Rex", 8, "beast", ["dinosaur-apex-predator", "swallow-whole", "massive-jaws"], ["jungle", "savanna"]),

  Monster("Ulitharid", 9, "aberration", ["mind-flayer-lieutenant", "superior-psionics", "tentacle-attack", "brine-pool-needed"], ["underdark", "colony"]),
  Monster("Umber Hulk", 5, "monstrosity", ["confusing-gaze", "massive-claws", "burrow"], ["underdark", "caves"]),
  Monster("Unicorn", 5, "celestial", ["healing-horn", "innate-spellcasting", "teleport", "woodland-protector"], ["forest", "glade"]),
  Monster("Uride", 0, "beast", ["small-rodent-kin", "desert-dweller", "burrow"], ["desert", "wasteland"]),
  Monster("Uthra", 1/8, "beast", ["goat-kin", "mountain-dweller", "ram-attack"], ["mountain", "highlands"]),
  Monster("Ustilagor", 9, "plant", ["flying-spore-pod", "fire-damage", "plant-servants"], ["swamp", "forest"]),
  Monster("Uthgardt Shaman", 2, "humanoid", ["tribe-priest", "spellcasting", "animal-totem"], ["mountain", "camp"]),
  Monster("Uthgardt Warrior", 1/2, "humanoid", ["tribe-warrior", "axe-attack", "ferocity"], ["mountain", "camp"]),

  Monster("Vampire", 13, "undead", ["shapechange", "charm", "legendary-actions", "misty-escape"], ["castle", "city"]),
  Monster("Vampire Spawn", 5, "undead", ["undead-servant", "spider-climb", "life-drain", "sunlight-vulnerability"], ["city", "tomb"]),
  Monster("Vampiric Mist", 3, "undead", ["amorphous", "blood-drain", "gaseous-form"], ["dungeons", "misty-graveyard"]),
  Monster("Vargouille", 1, "fiend", ["flying-head", "kiss-of-transformation", "disease"], ["lower-planes", "sewers"]),
  Monster("Vegepygmy", 1/4, "plant", ["spore-born", "camouflage", "javelin"], ["forest", "underdark"]),
  Monster("Vegepygmy Chief", 2, "plant", ["leadership", "spore-cloud", "chief-club"], ["forest", "underdark"]),
  Monster("Vegepygmy, Thorny", 1, "plant", ["spines-attack", "tough-hide", "ambush-hunter"], ["forest", "underdark"]),
  Monster("Velociraptor", 1/4, "beast", ["pack-tactics", "dinosaur", "claws-and-bite"], ["jungle", "savanna"]),
  Monster("Veteran", 3, "humanoid", ["master-at-arms", "multiattack", "sword-and-shield"], ["fortress", "city"]),
  Monster("Violet Fungus", 1/4, "plant", ["false-appearance", "rotting-touch", "fungal-trap"], ["caves", "dungeons"]),
  Monster("Vrock", 6, "fiend", ["demon", "spore-burst", "stun-scream", "fly"], ["abyss", "battlefield"]),

  Monster("War Priest", 9, "humanoid", ["spellcasting", "divine-fervor", "leader-aura"], ["temple", "battlefield"]),
  Monster("Warlock of the Archfey", 7, "humanoid", ["spellcasting", "fey-patron", "misty-escape"], ["city", "forest-ruins"]),
  Monster("Warlock of the Fiend", 7, "humanoid", ["spellcasting", "fiendish-patron", "dark-ones-blessing"], ["city", "dungeons"]),
  Monster("Warlock of the Great Old One", 7, "humanoid", ["spellcasting", "cosmic-patron", "mind-power"], ["city", "ancient-ruins"]),
  Monster("Warlord", 12, "humanoid", ["leadership", "command-allies", "great-weapon"], ["fortress", "battlefield"]),
  Monster("Wastrilith", 13, "fiend", ["demon", "water-whip", "corrosive-bile", "aquatic"], ["abyss", "water-plane"]),
  Monster("Water Elemental", 5, "elemental", ["amorphous", "whip-attack", "whirlpool"], ["ocean", "elemental-plane-of-water"]),
  Monster("Water Weird", 3, "elemental", ["invisible-in-water", "constrict", "aquatic-guardian"], ["dungeons", "pool"]),
  Monster("Weasel", 0, "beast", ["keen-smell", "small", "stealth"], ["farm", "forest"]),
  Monster("Werebear", 5, "humanoid (shapechanger)", ["hybrid-form", "curse-of-lycanthropy", "bear-strength"], ["forest", "mountain"]),
  Monster("Wereboar", 4, "humanoid (shapechanger)", ["tusk-gore", "curse-of-lycanthropy", "reckless-attack"], ["forest", "farm"]),
  Monster("Wererat", 2, "humanoid (shapechanger)", ["rat-stealth", "curse-of-lycanthropy", "multiattack"], ["city", "sewers"]),
  Monster("Weretiger", 4, "humanoid (shapechanger)", ["pounce", "curse-of-lycanthropy", "multiattack"], ["jungle", "forest"]),
  Monster("Werewolf", 3, "humanoid (shapechanger)", ["wolf-pack-tactics", "curse-of-lycanthropy", "bite"], ["forest", "mountain"]),
  Monster("White Dragon, Wyrmling", 2, "dragon", ["fly", "cold-breath", "burrow-in-ice"], ["arctic", "glacier"]),
  Monster("White Dragon, Young", 6, "dragon", ["fly", "cold-breath", "primitive-mind"], ["arctic", "glacier"]),
  Monster("White Dragon, Adult", 13, "dragon", ["fly", "cold-breath", "legendary-actions"], ["arctic", "glacier"]),
  Monster("White Dragon, Ancient", 20, "dragon", ["fly", "cold-breath", "legendary-actions", "lair-actions"], ["arctic", "glacier"]),
  Monster("Wight", 3, "undead", ["life-drain", "animate-undead", "sunlight-vulnerability"], ["grave", "dungeons"]),
  Monster("Will-o'-Wisp", 2, "undead", ["light-lure", "absorb-life", "invisibility"], ["swamp", "battlefield"]),
  Monster("Wolf", 1/4, "beast", ["pack-tactics", "keen-smell", "howl"], ["forest", "plains"]),
  Monster("Wolverine, Giant", 1, "beast", ["ferocious", "reckless-attack", "claws-and-bite"], ["arctic", "mountain"]),
  Monster("Wood Woad", 5, "plant", ["bonded-to-tree", "club-attack", "natural-armor"], ["forest", "sacred-grove"]),
  Monster("Wraith", 5, "undead", ["life-drain", "incorporeal", "sunlight-vulnerability"], ["grave", "dungeons"]),
  Monster("Wyvern", 6, "dragon", ["fly", "poison-sting", "grappling-talons"], ["mountain", "ruins"]),

  Monster("Xorn", 7, "elemental", ["earth-glide", "tri-mouth", "keen-smell-for-metal"], ["underdark", "elemental-plane-of-earth"]),
  Monster("Xvart", 1/8, "humanoid", ["desperate-attack", "cowardly-minion", "rat-kin"], ["caves", "dungeons"]),
  Monster("Xvart Warlock of Raxivort", 1, "humanoid", ["spellcasting", "frenzied-attack", "warlock-of-vermin-lord"], ["caves", "dungeons"]),

  Monster("Yagnoloth", 12, "fiend", ["yugoloth", "battlefield-strategist", "massive-arm"], ["lower-planes", "mercenary-camp"]),
  Monster("Yeenoghu", 24, "fiend", ["demon-lord-of-gnolls", "legendary-actions", "rampage-attack", "demon-whip"], ["abyss", "gnoll-horde"]),
  Monster("Yellow Musk Creeper", 2, "plant", ["zombie-control-spores", "vines-attack", "false-appearance"], ["jungle", "swamp"]),
  Monster("Yellow Musk Zombie", 1/4, "undead", ["mindless-minion", "plant-zombie", "slam-attack"], ["jungle", "swamp"]),
  Monster("Yeti", 3, "monstrosity", ["cold-dwelling", "claws-and-bite", "chilling-gaze"], ["arctic", "mountain"]),
  Monster("Yeti, Abominable", 9, "monstrosity", ["terrifying-screech", "chilling-gaze", "arctic-hunter"], ["arctic", "mountain"]),
  Monster("Yeth Hound", 4, "fey", ["shadow-dog", "bay-of-fear", "sunlight-vulnerability"], ["shadowfell", "night"]),
  Monster("Yuan-ti Anathema", 21, "monstrosity", ["snake-titan", "legendary-actions", "multi-headed-attack", "spellcasting"], ["temple", "underdark"]),
  Monster("Yuan-ti Broodguard", 2, "monstrosity", ["mindless-serpent-minion", "multiattack", "poisonous-blood"], ["temple", "dungeons"]),
  Monster("Yuan-ti Malison (Type 1, 2, 3)", 3, "monstrosity", ["snake-human-hybrid", "scimitar-and-bow", "innate-spellcasting"], ["temple", "jungle"]),
  Monster("Yuan-ti Mind Whisperer", 4, "monstrosity", ["psychic-spellcasting", "mind-control-aura", "snake-hybrid"], ["temple", "dungeons"]),
  Monster("Yuan-ti Nightmare Speaker", 6, "monstrosity", ["fear-spellcasting", "poison-attack", "dream-walker"], ["temple", "dungeons"]),
  Monster("Yuan-ti Pit Master", 5, "monstrosity", ["powerful-poison", "leader-of-yuan-ti", "multiattack"], ["temple", "dungeons"]),
  Monster("Yuan-ti Pureblood", 1, "monstrosity", ["human-like-snake", "spellcasting", "dagger-attack"], ["city", "temple"]),
  Monster("Yugoloth, Arcanaloth", 12, "fiend", ["powerful-spellcaster", "mercenary-lord", "teleport"], ["lower-planes", "libraries"]),
  Monster("Yugoloth, Canoloth", 8, "fiend", ["giant-dog-demon", "tongue-grapple", "mercenary"], ["lower-planes", "battlefield"]),
  Monster("Yugoloth, Hydroloth", 9, "fiend", ["aquatic-demon", "corrupt-water", "innate-spellcasting"], ["lower-planes", "ocean"]),
  Monster("Yugoloth, Mezzoloth", 3, "fiend", ["demon-general", "trident-and-teleport", "poison-cloud"], ["lower-planes", "battlefield"]),
  Monster("Yugoloth, Nycaloth", 10, "fiend", ["flying-demon", "massive-claws", "mercenary-commander"], ["lower-planes", "sky"]),
  Monster("Yugoloth, Oinoloth", 12, "fiend", ["disease-demon", "death-touch", "healing-curse"], ["lower-planes", "plague-ridden-land"]),
  Monster("Yugoloth, Ultroloth", 13, "fiend", ["leader-of-yugoloths", "mind-control", "innate-spellcasting"], ["lower-planes", "fortress"]),

  Monster("Zaratan", 22, "elemental", ["colossal-turtle", "earthquake-stomp", "mountain-size-lair"], ["ocean", "land"]),
  Monster("Zariel", 26, "fiend", ["archdevil", "lord-of-avernus", "legendary-actions", "unholy-flames"], ["nine-hells", "avernus"]),
  Monster("Zombie", 2, "undead", ["slow", "undead-fortitude", "mindless-minion"], ["grave", "dungeons"]),
  Monster("Zombie, Beholder", 5, "undead", ["undead-eyestalks", "antimagic-cone-gone", "slow"], ["dungeons", "tomb"]),
  Monster("Zombie, Ogre", 2, "undead", ["ogre-strength", "undead-fortitude", "slow"], ["grave", "dungeons"]),
  Monster("Zuggtmoy", 23, "fiend", ["demon-lord-of-fungi", "legendary-actions", "spore-control", "mind-control"], ["abyss", "underdark"]),
]

# ----------------------
# Helper/engine methods
# ----------------------
def parse_party(text: str) -> List[int]:
    text = text.strip()
    if not text:
        return []
    levels: List[int] = []
    for token in text.replace(",", " ").split():
        if "x" in token.lower():
            a, b = token.lower().split("x")
            levels.extend([int(b)] * int(a))
        else:
            levels.append(int(token))
    return levels

def party_threshold(levels: List[int], difficulty: str) -> int:
    return sum(XP_THRESHOLDS.get(l, XP_THRESHOLDS[1])[difficulty] for l in levels)

def party_size_band(n: int) -> str:
    return "small" if n <= 3 else "large" if n >= 6 else "normal"

def encounter_multiplier(n_mobs: int, party_size: int) -> float:
    base = next(mult for cap, mult in BASE_MULTIPLIER if n_mobs <= cap)
    return base * PARTY_SIZE_ADJ[party_size_band(party_size)]

def adjusted_xp(monsters: List[Monster], party_size: int) -> Tuple[int, int, float]:
    base_xp = sum(m.xp for m in monsters)
    mult = encounter_multiplier(len(monsters), party_size)
    return base_xp, int(round(base_xp * mult)), mult

def estimate_difficulty(levels: List[int], adjusted_xp_value: int) -> str:
    bands = {k: party_threshold(levels, k) for k in ("easy","medium","hard","deadly")}
    if adjusted_xp_value < bands["easy"]:   return "trivial"
    if adjusted_xp_value < bands["medium"]: return "easy"
    if adjusted_xp_value < bands["hard"]:   return "medium"
    if adjusted_xp_value < bands["deadly"]: return "hard"
    return "deadly+"

@dataclass
class BuildOptions:
    target: str = "medium"      # easy|medium|hard|deadly or numeric XP
    environment: Optional[str] = None
    include_types: Optional[List[str]] = None
    exclude_types: Optional[List[str]] = None
    tags_any: Optional[List[str]] = None
    seed: Optional[int] = None
    tolerance: float = 0.15
    max_monsters: int = 8
    prefer_variety: bool = True

@dataclass
class Encounter:
    monsters: List[Monster]
    base_xp: int
    adjusted_xp: int
    multiplier: float
    difficulty: str
    environment: Optional[str]

OBJECTIVES = [
    "Rescue the captive before round 5.",
    "Protect the NPC while retreating 60 ft.",
    "Stop a ritual; three pillars must be destroyed.",
    "Recover a relic from the battlefield.",
    "Escape across a collapsing bridge.",
]

HAZARDS = [
    "Cramped tunnels: large creatures have disadvantage on attacks.",
    "Slick ground: DC 12 Dex save on dash or fall prone.",
    "Low visibility: dim light; Perception at disadvantage.",
    "Arcane static: first spell each round needs DC 10 Con save or fizzles.",
    "Choking spores: DC 12 Con at start of turn or poisoned until end.",
]

def filter_pool(monsters: List[Monster], opt: BuildOptions) -> List[Monster]:
    pool = monsters
    if opt.environment:
        pool = [m for m in pool if opt.environment in m.environments]
    if opt.include_types:
        inc = set(t.lower() for t in opt.include_types)
        pool = [m for m in pool if m.type.lower() in inc]
    if opt.exclude_types:
        exc = set(t.lower() for t in opt.exclude_types)
        pool = [m for m in pool if m.type.lower() not in exc]
    if opt.tags_any:
        tset = set(t.lower() for t in opt.tags_any)
        pool = [m for m in pool if tset.intersection(tag.lower() for tag in m.tags)]
    return pool

def target_budget(levels: List[int], target: str | int) -> int:
    if isinstance(target, str):
        t = target.lower()
        if t in ("easy","medium","hard","deadly"):
            return party_threshold(levels, t)
        # allow like "1.2x hard"
        for label in ("easy","medium","hard","deadly"):
            if label in t:
                factor = float(t.replace(label, "").replace("x", "").strip() or 1)
                return int(party_threshold(levels, label) * factor)
        raise ValueError("Unknown target string.")
    return int(target)

def build_encounter(levels: List[int], pool: List[Monster], opt: BuildOptions) -> Encounter:
    if opt.seed is not None:
        random.seed(opt.seed)
    if not pool:
        raise ValueError("Monster pool is empty after filtering.")
    party_size = len(levels)
    budget = target_budget(levels, opt.target)
    if budget < 1:
      budget = 1
    lo, hi = int(budget * (1 - opt.tolerance)), int(budget * (1 + opt.tolerance))
    pool_sorted = sorted([m for m in pool if m.xp <= hi], key=lambda m: m.xp)
    best: Optional[Encounter] = None

    for _ in range(500):
        chosen: List[Monster] = []
        # seed pick near budget/2
        viable = [m for m in pool_sorted if m.xp <= max(1, budget)]
        chosen.append(random.choice(viable))
        tries = 0
        while len(chosen) < opt.max_monsters and tries < 200:
            tries += 1
            candidates = pool_sorted
            if opt.prefer_variety:
                names = {m.name for m in chosen}
                alt = [m for m in pool_sorted if m.name not in names]
                if alt:
                    candidates = alt
            pick = random.choice(candidates)
            trial = chosen + [pick]
            base, adj, mult = adjusted_xp(trial, party_size)
            if adj <= hi:
                chosen = trial
                if lo <= adj <= hi:
                    base, adj, mult = adjusted_xp(chosen, party_size)
                    enc = Encounter(chosen[:], base, adj, mult, estimate_difficulty(levels, adj), opt.environment)
                    if best is None or abs(adj - budget) < abs(best.adjusted_xp - budget):
                        best = enc
            # else skip
    if best is None:
        # fallback: single strongest that fits
        for m in reversed(pool_sorted):
            base, adj, mult = adjusted_xp([m], party_size)
            if adj <= hi:
                return Encounter([m], base, adj, mult, estimate_difficulty(levels, adj), opt.environment)
        # worst-case: spam lowest XP until cap
        m = pool_sorted[0]
        chosen = [m]
        while len(chosen) < opt.max_monsters:
            base, adj, mult = adjusted_xp(chosen, party_size)
            if adj >= lo:
                break
            chosen.append(m)
        base, adj, mult = adjusted_xp(chosen, party_size)
        return Encounter(chosen, base, adj, mult, estimate_difficulty(levels, adj), opt.environment)
    return best

# ----------------------
# CSV extension support
# ----------------------
CSV_TEMPLATE = """name,cr,type,tags,environments
Goblin,0.25,humanoid,"nimble|pack","forest|hills|caves|plains|coast|underdark|urban"
"""

def load_csv(path: str) -> List[Monster]:
    if pd is None:
        raise RuntimeError("pandas not available; cannot load CSV.")
    df = pd.read_csv(path)
    mons = []
    for _, row in df.iterrows():
        tags = [t.strip() for t in str(row.get("tags", "")).split("|") if t.strip()]
        envs = [e.strip() for e in str(row.get("environments", "")).split("|") if e.strip()]
        mons.append(Monster(str(row["name"]), row["cr"], str(row.get("type","")), tags, envs))
    return mons

def explain_csv():
    msg = f"""
Upload a CSV to extend monsters. Expected columns:

  name, cr, type, tags, environments

Use pipe separators inside fields, for example:

{CSV_TEMPLATE}

After uploading to Colab (left sidebar, Files), load it like:

    extra = load_csv('/content/my_monsters.csv')
    expanded_pool = SEED_MONSTERS + extra
    SEED_MONSTERS[:] = expanded_pool  # replace pool in-place

CR values can be integers (2) or fractions (0.5 or '1/2').
Tags and environments are optional, but help filtering.
"""
    print(textwrap.dedent(msg))

# ----------------------
# Pretty printing
# ----------------------
def fmt_cr(cr: float) -> str:
    for frac in [(1/8), (1/4), (1/2)]:
        if abs(cr - frac) < 1e-6:
            num = int(round(frac * 8))
            return f"1/{8//num}"
    return str(int(cr)) if float(cr).is_integer() else f"{cr:.2f}"

def render(enc: Encounter, levels: List[int], budget: int):
    party = f"Party: {len(levels)} PCs (levels: {', '.join(map(str, levels))})"
    env = f"Environment: {enc.environment or 'any'}"
    lines = [party, env, f"Target budget: {budget} XP", ""]
    counts: Dict[str, int] = {}
    for m in enc.monsters:
        counts[m.name] = counts.get(m.name, 0) + 1
    lines.append("Monsters:")
    for name, cnt in sorted(counts.items()):
        sample = next(mm for mm in enc.monsters if mm.name == name)
        lines.append(f"  x{cnt} {name} (CR {fmt_cr(sample.cr)}, {sample.type}, {sample.xp} XP each)")
    lines.append("")
    lines.append(f"Base XP: {enc.base_xp} | Multiplier: x{enc.multiplier:.2f} | Adjusted XP: {enc.adjusted_xp}")
    lines.append(f"Estimated difficulty: {enc.difficulty}")
    lines.append("")
    lines.append("Spice:")
    lines.append(f"  Objective: {random.choice(OBJECTIVES)}")
    lines.append(f"  Hazard: {random.choice(HAZARDS)}")
    block = "\n".join(lines)
    if _HAS_WIDGETS:
        display(HTML(f"<pre style='font-size:14px; line-height:1.35; padding:12px; background:#0b1021; color:#dfe7ff; border-radius:12px'>{block}</pre>"))
    else:
        print(block)

# ----------------------
# Procedural lair map generator
# ----------------------
try:
    import numpy as np
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except Exception:
    _HAS_MPL = False

@dataclass
class MapOptions:
    width: int = 48
    height: int = 32
    room_attempts: int = 120
    min_room: int = 4
    max_room: int = 10
    water_chance: float = 0.08
    hazard_chance: float = 0.06
    seed: Optional[int] = None

@dataclass
class LairMap:
    grid: 'np.ndarray'
    legend: Dict[int, str]

def _carve_room(grid, x, y, w, h):
    grid[y:y+h, x:x+w] = 1

def _overlaps(grid, x, y, w, h) -> bool:
    H, W = grid.shape
    x0 = max(0, x-1); y0 = max(0, y-1)
    x1 = min(W, x+w+1); y1 = min(H, y+h+1)
    return np.any(grid[y0:y1, x0:x1] == 1)

def _connect_points(grid, a, b):
    x0, y0 = a; x1, y1 = b
    if random.random() < 0.5:
        for x in range(min(x0, x1), max(x0, x1)+1): grid[y0, x] = 1
        for y in range(min(y0, y1), max(y0, y1)+1): grid[y, x1] = 1
    else:
        for y in range(min(y0, y1), max(y0, y1)+1): grid[y, x0] = 1
        for x in range(min(x0, x1), max(x0, x1)+1): grid[y1, x] = 1

def generate_lair_map(opt: MapOptions) -> LairMap:
    if not _HAS_MPL:
        raise RuntimeError("matplotlib/numpy not available.")
    if opt.seed is not None:
        random.seed(opt.seed); np.random.seed(opt.seed)
    grid = np.zeros((opt.height, opt.width), dtype=np.uint8)
    rooms = []
    for _ in range(opt.room_attempts):
        w = random.randint(opt.min_room, opt.max_room)
        h = random.randint(opt.min_room, opt.max_room)
        x = random.randint(1, opt.width - w - 2)
        y = random.randint(1, opt.height - h - 2)
        if not _overlaps(grid, x, y, w, h):
            _carve_room(grid, x, y, w, h)
            rooms.append((x, y, w, h))
    centers = [(x + w//2, y + h//2) for (x, y, w, h) in rooms]
    random.shuffle(centers)
    for i in range(1, len(centers)):
        _connect_points(grid, centers[i-1], centers[i])
    # Doors and dressing
    for (x, y, w, h) in rooms:
        perimeter = []
        for xx in range(x, x+w):
            perimeter.append((xx, y-1)); perimeter.append((xx, y+h))
        for yy in range(y, y+h):
            perimeter.append((x-1, yy)); perimeter.append((x+w, yy))
        random.shuffle(perimeter)
        placed = 0
        for px, py in perimeter:
            if 1 <= px < opt.width-1 and 1 <= py < opt.height-1:
                if grid[py, px] == 0 and (grid[py, px-1] == 1 or grid[py, px+1] == 1 or grid[py-1, px] == 1 or grid[py+1, px] == 1):
                    grid[py, px] = 2; placed += 1
                    if placed >= 2: break
    water_mask = (np.random.rand(opt.height, opt.width) < opt.water_chance) & (grid == 1)
    hazard_mask = (np.random.rand(opt.height, opt.width) < opt.hazard_chance) & (grid == 1)
    grid[water_mask] = 3
    grid[hazard_mask] = 4
    legend = {0: 'wall', 1: 'floor', 2: 'door', 3: 'water', 4: 'hazard'}
    return LairMap(grid, legend)

def show_lair_map(lmap: LairMap, title: str = 'Lair Map'):
    if not _HAS_MPL:
        print("Matplotlib not available."); return
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 7))
    plt.imshow(lmap.grid, interpolation='nearest')
    plt.title(title)
    plt.axis('off')
    plt.show()
    print('Legend:', lmap.legend)

# ----------------------
# Simple UI (Colab)
# ----------------------
def run_ui():
    if not _HAS_WIDGETS:
        print("ipywidgets not available. Use text-mode or run in Colab.")
        return

    party_box = widgets.Text(value="4x5", description="Party")
    target_box = widgets.Text(value="medium", description="Target")
    env_dd = widgets.Dropdown(
        options=["(any)"] + sorted({e for m in SEED_MONSTERS for e in m.environments}),
        value="(any)", description="Env"
    )
    tags_box = widgets.Text(value="", description="Tags any")
    include_box = widgets.Text(value="", description="Types+")
    exclude_box = widgets.Text(value="", description="Types-")
    tol_slider = widgets.FloatSlider(value=0.15, min=0.05, max=0.5, step=0.05, description="Tolerance")
    maxm_slider = widgets.IntSlider(value=8, min=1, max=20, step=1, description="#Mon cap")

    build_btn = widgets.Button(description="Build Encounter", button_style="primary")
    map_btn = widgets.Button(description="Lair Map")

    def do_build(_):
        # Hidden automatic seed every click
        auto_seed = random.randint(1, 999_999)

        levels = parse_party(party_box.value)
        env = env_dd.value if env_dd.value != "(any)" else None
        tags_any = [t.strip() for t in tags_box.value.split(",") if t.strip()]
        include = [t.strip() for t in include_box.value.split(",") if t.strip()]
        exclude = [t.strip() for t in exclude_box.value.split(",") if t.strip()]

        opt = BuildOptions(
            target=target_box.value,
            environment=env,
            include_types=include or None,
            exclude_types=exclude or None,
            tags_any=tags_any or None,
            seed=auto_seed,
            tolerance=float(tol_slider.value),
            max_monsters=int(maxm_slider.value),
        )
        pool = filter_pool(SEED_MONSTERS, opt)
        enc = build_encounter(levels, pool, opt)
        budget = target_budget(levels, opt.target)

        print(f"Auto Seed: {auto_seed}")
        render(enc, levels, budget)

    def do_map(_):
        # Hidden automatic seed every click
        auto_seed = random.randint(1, 999_999)
        lmap = generate_lair_map(MapOptions(seed=auto_seed))
        show_lair_map(lmap, title=f"Lair Map (seed {auto_seed})")

    ui = widgets.VBox([
        widgets.HBox([party_box, target_box, env_dd]),
        widgets.HBox([tags_box, include_box, exclude_box]),
        widgets.HBox([tol_slider, maxm_slider]),
        widgets.HBox([build_btn, map_btn]),
    ])
    display(ui)
    build_btn.on_click(do_build)
    map_btn.on_click(do_map)

# Auto-run UI when executed in a notebook environment
try:
    get_ipython  # type: ignore
    run_ui()
    print("\nTip: call explain_csv() for CSV format and usage.")
except Exception:
    pass
