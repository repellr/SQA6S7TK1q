import math, random, textwrap
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------- Tables (SRD-ish) ----------
XP_THRESHOLDS = {
    1:{"easy":25,"medium":50,"hard":75,"deadly":100},
    2:{"easy":50,"medium":100,"hard":150,"deadly":200},
    3:{"easy":75,"medium":150,"hard":225,"deadly":400},
    4:{"easy":125,"medium":250,"hard":375,"deadly":500},
    5:{"easy":250,"medium":500,"hard":750,"deadly":1100},
    6:{"easy":300,"medium":600,"hard":900,"deadly":1400},
    7:{"easy":350,"medium":750,"hard":1100,"deadly":1700},
    8:{"easy":450,"medium":900,"hard":1400,"deadly":2100},
    9:{"easy":550,"medium":1100,"hard":1600,"deadly":2400},
    10:{"easy":600,"medium":1200,"hard":1900,"deadly":2800},
    11:{"easy":800,"medium":1600,"hard":2400,"deadly":3600},
    12:{"easy":1000,"medium":2000,"hard":3000,"deadly":4500},
    13:{"easy":1100,"medium":2200,"hard":3400,"deadly":5100},
    14:{"easy":1250,"medium":2500,"hard":3800,"deadly":5700},
    15:{"easy":1400,"medium":2800,"hard":4300,"deadly":6400},
    16:{"easy":1600,"medium":3200,"hard":4800,"deadly":7200},
    17:{"easy":2000,"medium":3900,"hard":5900,"deadly":8800},
    18:{"easy":2100,"medium":4200,"hard":6300,"deadly":9500},
    19:{"easy":2400,"medium":4900,"hard":7300,"deadly":10900},
    20:{"easy":2800,"medium":5700,"hard":8500,"deadly":12700},
}
CR_XP = {
    0:10, 1/8:25, 1/4:50, 1/2:100, 1:200, 2:450, 3:700, 4:1100, 5:1800, 6:2300,
    7:2900, 8:3900, 9:5000, 10:5900, 11:7200, 12:8400, 13:10000, 14:11500, 15:13000,
    16:15000, 17:18000, 18:20000, 19:22000, 20:25000, 21:33000, 22:41000, 23:50000,
    24:62000, 25:75000, 26:90000, 27:105000, 28:120000, 29:135000, 30:155000,
}
BASE_MULTIPLIER = [(1,1.0),(2,1.5),(6,2.0),(10,2.5),(14,3.0),(math.inf,4.0)]
PARTY_SIZE_ADJ = {"small":1.5,"normal":1.0,"large":0.75}

# ---------- Data classes ----------
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
            n, d = self.cr.split("/")
            self.cr = float(n)/float(d)
        self.cr = float(self.cr)
        self.xp = CR_XP.get(self.cr, 0)

SEED_MONSTERS: List[Monster] = [
    Monster("Goblin", 1/4, "humanoid", ["nimble","pack"], ["forest","hills","caves","plains","coast","underdark","urban"]),
    Monster("Bandit", 1/8, "humanoid", ["bandit","pack"], ["urban","plains","coast","forest","hills"]),
    Monster("Wolf", 1/4, "beast", ["pack","tracker"], ["forest","hills","plains","arctic"]),
    Monster("Skeleton", 1/4, "undead", ["resilient"], ["dungeon","swamp","desert","underdark","urban"]),
    Monster("Zombie", 1/4, "undead", ["brute"], ["dungeon","swamp","urban","underdark"]),
    Monster("Orc", 1/2, "humanoid", ["brute","raider"], ["hills","mountains","plains","forest"]),
    Monster("Hobgoblin", 1/2, "humanoid", ["tactical","soldier"], ["forest","hills","plains","urban"]),
    Monster("Giant Spider", 1, "monstrosity", ["ambusher","web"], ["forest","swamp","underdark"]),
    Monster("Black Bear", 1/2, "beast", ["brute"], ["forest","hills","mountains"]),
    Monster("Thug", 1/2, "humanoid", ["enforcer"], ["urban","coast"]),
    Monster("Ghoul", 1, "undead", ["paralysis"], ["graveyard","urban","swamp","dungeon"]),
    Monster("Ogre", 2, "giant", ["brute"], ["hills","mountains","forest"]),
    Monster("Wight", 3, "undead", ["life-drain"], ["graveyard","dungeon","urban"]),
    Monster("Bugbear", 1, "humanoid", ["ambusher","brute"], ["forest","hills","caves"]),
    Monster("Giant Wolf Spider", 1/4, "beast", ["ambusher"], ["forest","swamp"]),
    Monster("Giant Scorpion", 3, "beast", ["poison"], ["desert"]),
    Monster("Brown Bear", 1, "beast", ["brute"], ["forest","hills","mountains"]),
    Monster("Banshee", 4, "undead", ["fear","wail"], ["forest","swamp","dungeon"]),
]

# ---------- Helpers ----------
def parse_party(text: str) -> List[int]:
    text = text.strip()
    if not text: return []
    out = []
    for tok in text.replace(",", " ").split():
        if "x" in tok.lower():
            a,b = tok.lower().split("x")
            out += [int(b)]*int(a)
        else:
            out.append(int(tok))
    return out

def party_threshold(levels: List[int], difficulty: str) -> int:
    return sum(XP_THRESHOLDS.get(l, XP_THRESHOLDS[1])[difficulty] for l in levels)

def party_size_band(n: int) -> str:
    return "small" if n <= 3 else "large" if n >= 6 else "normal"

def encounter_multiplier(n_mobs: int, party_size: int) -> float:
    base = next(mult for cap, mult in BASE_MULTIPLIER if n_mobs <= cap)
    return base * PARTY_SIZE_ADJ[party_size_band(party_size)]

def adjusted_xp(monsters: List[Monster], party_size: int) -> Tuple[int,int,float]:
    base = sum(m.xp for m in monsters)
    mult = encounter_multiplier(len(monsters), party_size)
    return base, int(round(base*mult)), mult

def estimate_difficulty(levels: List[int], adj: int) -> str:
    bands = {k: party_threshold(levels,k) for k in ("easy","medium","hard","deadly")}
    if adj < bands["easy"]: return "trivial"
    if adj < bands["medium"]: return "easy"
    if adj < bands["hard"]: return "medium"
    if adj < bands["deadly"]: return "hard"
    return "deadly+"

def filter_pool(monsters: List[Monster],
                environment: Optional[str],
                include_types: Optional[List[str]],
                exclude_types: Optional[List[str]],
                tags_any: Optional[List[str]]) -> List[Monster]:
    pool = monsters
    if environment:
        pool = [m for m in pool if environment in m.environments]
    if include_types:
        inc = set(t.lower() for t in include_types)
        pool = [m for m in pool if m.type.lower() in inc]
    if exclude_types:
        exc = set(t.lower() for t in exclude_types)
        pool = [m for m in pool if m.type.lower() not in exc]
    if tags_any:
        tset = set(t.lower() for t in tags_any)
        pool = [m for m in pool if tset.intersection(tag.lower() for tag in m.tags)]
    return pool

def target_budget(levels: List[int], target: str|int) -> int:
    if isinstance(target, str):
        t = target.lower()
        if t in ("easy","medium","hard","deadly"):
            return party_threshold(levels, t)
        for label in ("easy","medium","hard","deadly"):
            if label in t:
                factor = float(t.replace(label,"").replace("x","").strip() or 1)
                return int(party_threshold(levels, label)*factor)
        raise ValueError("Unknown target string.")
    return int(target)

# ---------- Encounter builder ----------
def build_encounter(levels: List[int], pool: List[Monster],
                    target: str, tolerance: float, max_monsters: int,
                    prefer_variety: bool, seed: int) -> Dict:
    random.seed(seed)
    if not pool: raise ValueError("Monster pool empty.")
    party_size = len(levels)
    budget = target_budget(levels, target)
    lo, hi = int(budget*(1-tolerance)), int(budget*(1+tolerance))
    pool_sorted = sorted([m for m in pool if m.xp <= hi], key=lambda m: m.xp)
    best = None
    for _ in range(500):
        chosen = []
        viable = [m for m in pool_sorted if m.xp <= max(1, budget)]
        if not viable: viable = pool_sorted
        chosen.append(random.choice(viable))
        tries = 0
        while len(chosen) < max_monsters and tries < 200:
            tries += 1
            candidates = pool_sorted
            if prefer_variety:
                names = {m.name for m in chosen}
                alt = [m for m in pool_sorted if m.name not in names]
                if alt: candidates = alt
            pick = random.choice(candidates)
            trial = chosen + [pick]
            base, adj, mult = adjusted_xp(trial, party_size)
            if adj <= hi:
                chosen = trial
                if lo <= adj <= hi:
                    if best is None or abs(adj - budget) < abs(best["adjusted_xp"] - budget):
                        best = {
                            "monsters": chosen[:],
                            "base_xp": base,
                            "adjusted_xp": adj,
                            "multiplier": mult,
                            "budget": budget,
                        }
    if best is None:
        # fallbacks
        for m in reversed(pool_sorted):
            base, adj, mult = adjusted_xp([m], party_size)
            if adj <= hi:
                return {"monsters":[m], "base_xp":base, "adjusted_xp":adj, "multiplier":mult, "budget":budget}
        m = pool_sorted[0]
        chosen = [m]
        while len(chosen) < max_monsters:
            base, adj, mult = adjusted_xp(chosen, party_size)
            if adj >= lo: break
            chosen.append(m)
        base, adj, mult = adjusted_xp(chosen, party_size)
        return {"monsters":chosen, "base_xp":base, "adjusted_xp":adj, "multiplier":mult, "budget":budget}
    return best

# ---------- Map generator ----------
def generate_lair_map(width=48, height=32, room_attempts=120, min_room=4, max_room=10,
                      water_chance=0.08, hazard_chance=0.06, seed=None):
    if seed is not None:
        random.seed(seed); np.random.seed(seed)
    grid = np.zeros((height, width), dtype=np.uint8)
    rooms = []
    def overlaps(x,y,w,h):
        H,W = grid.shape
        x0=max(0,x-1); y0=max(0,y-1); x1=min(W,x+w+1); y1=min(H,y+h+1)
        return np.any(grid[y0:y1, x0:x1] == 1)
    def carve(x,y,w,h): grid[y:y+h, x:x+w] = 1
    for _ in range(room_attempts):
        w = random.randint(min_room, max_room)
        h = random.randint(min_room, max_room)
        x = random.randint(1, width - w - 2)
        y = random.randint(1, height - h - 2)
        if not overlaps(x,y,w,h):
            carve(x,y,w,h); rooms.append((x,y,w,h))
    centers = [(x+w//2, y+h//2) for (x,y,w,h) in rooms]
    random.shuffle(centers)
    def connect(a,b):
        x0,y0=a; x1,y1=b
        if random.random()<0.5:
            for x in range(min(x0,x1), max(x0,x1)+1): grid[y0,x]=1
            for y in range(min(y0,y1), max(y0,y1)+1): grid[y,x1]=1
        else:
            for y in range(min(y0,y1), max(y0,y1)+1): grid[y,x0]=1
            for x in range(min(x0,x1), max(x0,x1)+1): grid[y1,x]=1
    for i in range(1,len(centers)): connect(centers[i-1], centers[i])
    # doors & dressing
    for (x,y,w,h) in rooms:
        perimeter=[]
        for xx in range(x,x+w):
            perimeter.append((xx,y-1)); perimeter.append((xx,y+h))
        for yy in range(y,y+h):
            perimeter.append((x-1,yy)); perimeter.append((x+w,yy))
        random.shuffle(perimeter)
        placed=0
        for px,py in perimeter:
            if 1<=px<width-1 and 1<=py<height-1:
                if grid[py,px]==0 and (grid[py,px-1]==1 or grid[py,px+1]==1 or grid[py-1,px]==1 or grid[py+1,px]==1):
                    grid[py,px]=2; placed+=1
                    if placed>=2: break
    water = (np.random.rand(height,width)<water_chance)&(grid==1)
    hazard = (np.random.rand(height,width)<hazard_chance)&(grid==1)
    grid[water]=3; grid[hazard]=4
    legend = {0:'wall',1:'floor',2:'door',3:'water',4:'hazard'}
    return grid, legend

def fmt_cr(cr: float) -> str:
    for frac in (1/8, 1/4, 1/2):
        if abs(cr - frac) < 1e-6:
            num = int(round(frac * 8))
            return f"1/{8//num}"
    return str(int(cr)) if float(cr).is_integer() else f"{cr:.2f}"

# ---------- UI ----------
st.set_page_config(page_title="5e Encounter Builder", layout="wide")
st.title("🧪 5e Encounter Builder (Streamlit)")
st.caption("Runs in a browser. No installs. Perfect for flexing at D&D club.")

with st.sidebar:
    st.subheader("Encounter inputs")
    party_text = st.text_input("Party (e.g., 4x5 or 5,5,5,5)", "4x5")
    target = st.text_input("Target (easy/medium/hard/deadly or '1.2x hard')", "medium")
    environment = st.selectbox("Environment", ["(any)"] + sorted({e for m in SEED_MONSTERS for e in m.environments}))
    tags_any = st.text_input("Tags any (comma-separated)", "")
    include_types = st.text_input("Include types (comma-separated)", "")
    exclude_types = st.text_input("Exclude types (comma-separated)", "")
    tolerance = st.slider("Tolerance", 0.05, 0.50, 0.15, 0.05)
    max_mobs = st.slider("# Monster cap", 1, 20, 8, 1)
    prefer_variety = st.checkbox("Prefer variety", True)
    st.subheader("Monster CSV (optional)")
    up = st.file_uploader("Upload CSV (name, cr, type, tags, environments)", type=["csv"])

col1, col2 = st.columns([1,1])

# Load pool
pool = SEED_MONSTERS[:]
if up is not None:
    try:
        df = pd.read_csv(up)
        for _, row in df.iterrows():
            tags = [t.strip() for t in str(row.get("tags","")).split("|") if t.strip()]
            envs = [e.strip() for e in str(row.get("environments","")).split("|") if e.strip()]
            pool.append(Monster(str(row["name"]), row["cr"], str(row.get("type","")), tags, envs))
    except Exception as e:
        st.error(f"CSV error: {e}")

levels = parse_party(party_text)
env = None if environment == "(any)" else environment
tags_list = [t.strip() for t in tags_any.split(",") if t.strip()]
inc_list = [t.strip() for t in include_types.split(",") if t.strip()]
exc_list = [t.strip() for t in exclude_types.split(",") if t.strip()]
fpool = filter_pool(pool, env, inc_list or None, exc_list or None, tags_list or None)

with col1:
    if st.button("⚔️ Build Encounter"):
        seed = random.randint(1, 999_999)  # auto-random each click
        result = build_encounter(levels, fpool, target, tolerance, max_mobs, prefer_variety, seed)
        base = result["base_xp"]; adj = result["adjusted_xp"]; mult = result["multiplier"]; budget = result["budget"]
        diff = estimate_difficulty(levels, adj)
        st.write(f"**Seed:** {seed}")
        st.write(f"**Base XP:** {base}  |  **Multiplier:** x{mult:.2f}  |  **Adjusted XP:** {adj}  |  **Budget:** {budget}")
        st.write(f"**Estimated difficulty:** {diff}")
        # monster summary
        counts: Dict[str,int] = {}
        for m in result["monsters"]:
            counts[m.name] = counts.get(m.name, 0) + 1
        rows = []
        for name, cnt in sorted(counts.items()):
            smp = next(mm for mm in result["monsters"] if mm.name == name)
            rows.append({"count": cnt, "name": name, "CR": fmt_cr(smp.cr), "type": smp.type, "XP each": smp.xp})
        st.table(pd.DataFrame(rows))

with col2:
    if st.button("🗺️ Generate Lair Map"):
        seed = random.randint(1, 999_999)  # auto-random each click
        grid, legend = generate_lair_map(seed=seed)
        fig, ax = plt.subplots(figsize=(7,5))
        ax.imshow(grid, interpolation="nearest")
        ax.axis("off")
        ax.set_title(f"Lair Map (seed {seed})")
        st.pyplot(fig)
        st.caption(f"Legend: {legend}")
