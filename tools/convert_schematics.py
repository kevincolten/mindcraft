#!/usr/bin/env python3
"""
Builds the schematic library the Minecraft bot uses.

Pulls the assskelad/minecraftbuildings dataset from HuggingFace, converts each
building into a WorldEdit-compatible .schem file with a kid-readable name, and
writes schematics_index.json so the bot can search by description.

Run inside the mindcraft container:
    python3 /app/tools/convert_schematics.py

Output dir defaults to $SCHEMATICS_DIR (/app/schematics) and must be writable.
"""

import ast
import json
import os
import re
from collections import Counter

from datasets import load_dataset
import mcschematic

OUT_DIR = os.environ.get("SCHEMATICS_DIR", "/app/schematics")
INDEX_PATH = os.path.join(OUT_DIR, "schematics_index.json")

LEGACY_ID_MAP = {
    0: "minecraft:air", 1: "minecraft:stone", 2: "minecraft:grass_block",
    3: "minecraft:dirt", 4: "minecraft:cobblestone", 5: "minecraft:oak_planks",
    6: "minecraft:oak_sapling", 7: "minecraft:bedrock", 8: "minecraft:water",
    9: "minecraft:water", 10: "minecraft:lava", 11: "minecraft:lava",
    12: "minecraft:sand", 13: "minecraft:gravel", 14: "minecraft:gold_ore",
    15: "minecraft:iron_ore", 16: "minecraft:coal_ore", 17: "minecraft:oak_log",
    18: "minecraft:oak_leaves", 19: "minecraft:sponge", 20: "minecraft:glass",
    21: "minecraft:lapis_ore", 22: "minecraft:lapis_block", 23: "minecraft:dispenser",
    24: "minecraft:sandstone", 25: "minecraft:note_block", 26: "minecraft:red_bed",
    27: "minecraft:powered_rail", 28: "minecraft:detector_rail", 29: "minecraft:sticky_piston",
    30: "minecraft:cobweb", 31: "minecraft:short_grass", 32: "minecraft:dead_bush",
    33: "minecraft:piston", 34: "minecraft:air", 35: "minecraft:white_wool",
    36: "minecraft:air", 37: "minecraft:dandelion", 38: "minecraft:poppy",
    39: "minecraft:brown_mushroom", 40: "minecraft:red_mushroom", 41: "minecraft:gold_block",
    42: "minecraft:iron_block", 43: "minecraft:smooth_stone", 44: "minecraft:smooth_stone_slab",
    45: "minecraft:bricks", 46: "minecraft:tnt", 47: "minecraft:bookshelf",
    48: "minecraft:mossy_cobblestone", 49: "minecraft:obsidian", 50: "minecraft:torch",
    51: "minecraft:fire", 52: "minecraft:spawner", 53: "minecraft:oak_stairs",
    54: "minecraft:chest", 55: "minecraft:redstone_wire", 56: "minecraft:diamond_ore",
    57: "minecraft:diamond_block", 58: "minecraft:crafting_table", 59: "minecraft:wheat",
    60: "minecraft:farmland", 61: "minecraft:furnace", 62: "minecraft:furnace",
    63: "minecraft:oak_sign", 64: "minecraft:oak_door", 65: "minecraft:ladder",
    66: "minecraft:rail", 67: "minecraft:cobblestone_stairs", 68: "minecraft:oak_wall_sign",
    69: "minecraft:lever", 70: "minecraft:stone_pressure_plate", 71: "minecraft:iron_door",
    72: "minecraft:oak_pressure_plate", 73: "minecraft:redstone_ore", 74: "minecraft:redstone_ore",
    75: "minecraft:redstone_torch", 76: "minecraft:redstone_torch", 77: "minecraft:stone_button",
    78: "minecraft:snow", 79: "minecraft:ice", 80: "minecraft:snow_block",
    81: "minecraft:cactus", 82: "minecraft:clay", 83: "minecraft:sugar_cane",
    84: "minecraft:jukebox", 85: "minecraft:oak_fence", 86: "minecraft:carved_pumpkin",
    87: "minecraft:netherrack", 88: "minecraft:soul_sand", 89: "minecraft:glowstone",
    90: "minecraft:air", 91: "minecraft:jack_o_lantern", 92: "minecraft:cake",
    93: "minecraft:repeater", 94: "minecraft:repeater", 95: "minecraft:white_stained_glass",
    96: "minecraft:oak_trapdoor", 97: "minecraft:infested_stone", 98: "minecraft:stone_bricks",
    99: "minecraft:brown_mushroom_block", 100: "minecraft:red_mushroom_block",
    101: "minecraft:iron_bars", 102: "minecraft:glass_pane", 103: "minecraft:melon",
    104: "minecraft:pumpkin_stem", 105: "minecraft:melon_stem", 106: "minecraft:vine",
    107: "minecraft:oak_fence_gate", 108: "minecraft:brick_stairs", 109: "minecraft:stone_brick_stairs",
    110: "minecraft:mycelium", 111: "minecraft:lily_pad", 112: "minecraft:nether_bricks",
    113: "minecraft:nether_brick_fence", 114: "minecraft:nether_brick_stairs",
    115: "minecraft:nether_wart", 116: "minecraft:enchanting_table", 117: "minecraft:brewing_stand",
    118: "minecraft:cauldron", 119: "minecraft:air", 120: "minecraft:end_portal_frame",
    121: "minecraft:end_stone", 122: "minecraft:dragon_egg", 123: "minecraft:redstone_lamp",
    124: "minecraft:redstone_lamp", 125: "minecraft:oak_planks", 126: "minecraft:oak_slab",
    127: "minecraft:cocoa", 128: "minecraft:sandstone_stairs", 129: "minecraft:emerald_ore",
    130: "minecraft:ender_chest", 131: "minecraft:tripwire_hook", 132: "minecraft:tripwire",
    133: "minecraft:emerald_block", 134: "minecraft:spruce_stairs", 135: "minecraft:birch_stairs",
    136: "minecraft:jungle_stairs", 137: "minecraft:command_block", 138: "minecraft:beacon",
    139: "minecraft:cobblestone_wall", 140: "minecraft:flower_pot", 141: "minecraft:carrots",
    142: "minecraft:potatoes", 143: "minecraft:oak_button", 144: "minecraft:skeleton_skull",
    145: "minecraft:anvil", 146: "minecraft:trapped_chest",
    147: "minecraft:light_weighted_pressure_plate", 148: "minecraft:heavy_weighted_pressure_plate",
    149: "minecraft:comparator", 150: "minecraft:comparator", 151: "minecraft:daylight_detector",
    152: "minecraft:redstone_block", 153: "minecraft:nether_quartz_ore", 154: "minecraft:hopper",
    155: "minecraft:quartz_block", 156: "minecraft:quartz_stairs", 157: "minecraft:activator_rail",
    158: "minecraft:dropper", 159: "minecraft:white_terracotta",
    160: "minecraft:white_stained_glass_pane", 161: "minecraft:acacia_leaves",
    162: "minecraft:acacia_log", 163: "minecraft:acacia_stairs", 164: "minecraft:dark_oak_stairs",
    165: "minecraft:slime_block", 166: "minecraft:barrier", 167: "minecraft:iron_trapdoor",
    168: "minecraft:prismarine", 169: "minecraft:sea_lantern", 170: "minecraft:hay_block",
    171: "minecraft:white_carpet", 172: "minecraft:terracotta", 173: "minecraft:coal_block",
    174: "minecraft:packed_ice", 175: "minecraft:sunflower", 176: "minecraft:white_banner",
    177: "minecraft:white_wall_banner", 178: "minecraft:daylight_detector",
    179: "minecraft:red_sandstone", 180: "minecraft:red_sandstone_stairs",
    181: "minecraft:red_sandstone", 182: "minecraft:red_sandstone_slab",
    183: "minecraft:spruce_fence_gate", 184: "minecraft:birch_fence_gate",
    185: "minecraft:jungle_fence_gate", 186: "minecraft:dark_oak_fence_gate",
    187: "minecraft:acacia_fence_gate", 188: "minecraft:spruce_fence", 189: "minecraft:birch_fence",
    190: "minecraft:jungle_fence", 191: "minecraft:dark_oak_fence", 192: "minecraft:acacia_fence",
    193: "minecraft:spruce_door", 194: "minecraft:birch_door", 195: "minecraft:jungle_door",
    196: "minecraft:acacia_door", 197: "minecraft:dark_oak_door", 198: "minecraft:end_rod",
    199: "minecraft:chorus_plant", 200: "minecraft:chorus_flower", 201: "minecraft:purpur_block",
    202: "minecraft:purpur_pillar", 203: "minecraft:purpur_stairs", 204: "minecraft:purpur_block",
    205: "minecraft:purpur_slab", 206: "minecraft:end_stone_bricks", 207: "minecraft:beetroots",
    208: "minecraft:dirt_path", 209: "minecraft:air", 210: "minecraft:repeating_command_block",
    211: "minecraft:chain_command_block", 212: "minecraft:frosted_ice", 213: "minecraft:magma_block",
    214: "minecraft:nether_wart_block", 215: "minecraft:red_nether_bricks", 216: "minecraft:bone_block",
    217: "minecraft:structure_void", 218: "minecraft:observer",
    219: "minecraft:white_shulker_box", 220: "minecraft:orange_shulker_box",
    221: "minecraft:magenta_shulker_box", 222: "minecraft:light_blue_shulker_box",
    223: "minecraft:yellow_shulker_box", 224: "minecraft:lime_shulker_box",
    225: "minecraft:pink_shulker_box", 226: "minecraft:gray_shulker_box",
    227: "minecraft:light_gray_shulker_box", 228: "minecraft:cyan_shulker_box",
    229: "minecraft:purple_shulker_box", 230: "minecraft:blue_shulker_box",
    231: "minecraft:brown_shulker_box", 232: "minecraft:green_shulker_box",
    233: "minecraft:red_shulker_box", 234: "minecraft:black_shulker_box",
    235: "minecraft:white_glazed_terracotta", 236: "minecraft:orange_glazed_terracotta",
    237: "minecraft:magenta_glazed_terracotta", 238: "minecraft:light_blue_glazed_terracotta",
    239: "minecraft:yellow_glazed_terracotta", 240: "minecraft:lime_glazed_terracotta",
    241: "minecraft:pink_glazed_terracotta", 242: "minecraft:gray_glazed_terracotta",
    243: "minecraft:light_gray_glazed_terracotta", 244: "minecraft:cyan_glazed_terracotta",
    245: "minecraft:purple_glazed_terracotta", 246: "minecraft:blue_glazed_terracotta",
    247: "minecraft:brown_glazed_terracotta", 248: "minecraft:green_glazed_terracotta",
    249: "minecraft:red_glazed_terracotta", 250: "minecraft:black_glazed_terracotta",
    251: "minecraft:white_concrete", 252: "minecraft:white_concrete_powder",
    255: "minecraft:structure_block",
}

SKIP_BLOCKS = {"minecraft:air", "minecraft:fire", "minecraft:barrier",
               "minecraft:structure_void", "minecraft:structure_block"}

BOILERPLATE = re.compile(
    r"^(the |this )?(image |picture |photo |screenshot )?"
    r"(shows|depicts|displays|showcases|features|is|appears to (show|be)|presents)"
    r"( us)?( a| an| the)?( scene (from|in|of))?( a| an| the)?"
    r"( 3d[- ]rendered,?)?( custom[- ]made)?( minecraft)?( build| creation| structure| scene)?"
    r"( of| in| within| from)?( the game)?( minecraft)?[,.]?\s*",
    re.IGNORECASE,
)

STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "at", "to", "and", "or", "with", "is",
    "are", "was", "were", "it", "its", "this", "that", "these", "those", "there",
    "which", "featuring", "features", "appears", "seems", "very", "quite",
    "image", "picture", "photo", "screenshot", "shows", "showing", "depicts",
    "depicting", "displays", "build", "builds", "built", "minecraft", "game",
    "scene", "style", "styled", "rendered", "custom", "made", "within", "some",
}

PRIORITY_WORDS = [
    "castle", "fortress", "tower", "house", "home", "cabin", "cottage", "mansion",
    "village", "town", "city", "farm", "barn", "windmill", "lighthouse", "bridge",
    "ship", "boat", "pirate", "temple", "pyramid", "church", "cathedral", "tavern",
    "inn", "shop", "market", "bakery", "library", "school", "hospital", "statue",
    "fountain", "garden", "park", "maze", "arena", "stadium", "dragon", "tree",
    "treehouse", "igloo", "volcano", "island", "cave", "dungeon", "prison", "wall",
    "gate", "stable", "mine", "railway", "train", "station", "airport", "plane",
    "rocket", "spaceship", "robot", "skyscraper", "hotel", "restaurant", "cafe",
    "medieval", "modern", "japanese", "desert", "snow", "jungle", "underwater",
    "haunted", "spooky", "magic", "wizard", "fairy", "hobbit", "viking", "greek",
    "roman", "egyptian", "wooden", "stone", "brick", "glass", "small", "large",
    "giant", "tiny", "cozy",
]

unmapped_ids = Counter()
used_names = set()


def map_block(block_id):
    name = LEGACY_ID_MAP.get(block_id)
    if name is None:
        unmapped_ids[block_id] += 1
        return "minecraft:stone"
    return name


def clean_description(desc):
    d = desc.strip().strip('"')
    prev = None
    while prev != d:
        prev = d
        d = BOILERPLATE.sub("", d, count=1).strip()
    return d


def make_name(desc, idx):
    cleaned = clean_description(desc)
    words = [w.lower() for w in re.findall(r"[A-Za-z]+", cleaned)]
    meaningful = [w for w in words if w not in STOPWORDS and len(w) > 2]
    priority_hits = [w for w in meaningful if w in PRIORITY_WORDS]

    seen, ordered = set(), []
    for w in priority_hits + meaningful:
        if w not in seen:
            seen.add(w)
            ordered.append(w)
        if len(ordered) >= 4:
            break

    base = re.sub(r"[^a-z_]", "", "_".join(ordered))[:50].strip("_") or "building"
    name = base if base not in used_names else f"{base}_{idx}"
    used_names.add(name)
    return name


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Output dir: {OUT_DIR}", flush=True)
    print("Loading dataset from Hugging Face...", flush=True)
    ds = load_dataset("assskelad/minecraftbuildings", split="train")
    print(f"Loaded {len(ds)} buildings. Converting...", flush=True)

    index = {}
    ok, skipped = 0, 0

    for idx, row in enumerate(ds):
        description = row.get("Description") or row.get("description") or ""
        raw = row.get("Block Info") or row.get("block_info")
        if not raw:
            skipped += 1
            continue
        try:
            blocks = ast.literal_eval(raw) if isinstance(raw, str) else raw
        except (ValueError, SyntaxError):
            skipped += 1
            continue
        if not blocks:
            skipped += 1
            continue

        schem = mcschematic.MCSchematic()
        placed, max_y = 0, 0
        for entry in blocks:
            if len(entry) != 4:
                continue
            x, y, z, block_id = entry
            block_name = map_block(block_id)
            if block_name in SKIP_BLOCKS:
                continue
            schem.setBlock((x, y, z), block_name)
            placed += 1
            max_y = max(max_y, y)

        if placed == 0:
            skipped += 1
            continue

        name = make_name(description, idx)
        try:
            schem.save(OUT_DIR, name, mcschematic.Version.JE_1_20_1)
        except Exception as e:
            print(f"  Failed to save {name}: {e}", flush=True)
            skipped += 1
            continue

        cleaned = clean_description(description)
        index[f"{name}.schem"] = {
            "name": name.replace("_", " "),
            "description": cleaned[:400],
            "keywords": sorted({w.lower() for w in re.findall(r"[A-Za-z]+", cleaned)
                                if w.lower() not in STOPWORDS and len(w) > 2}),
            "blocks": placed,
            "height": max_y + 1,
        }
        ok += 1

        if (idx + 1) % 200 == 0:
            print(f"  progress: {idx + 1}/{len(ds)} (ok={ok}, skipped={skipped})", flush=True)

    with open(INDEX_PATH, "w") as f:
        json.dump(index, f, indent=1)

    print(f"\nDONE: {ok} schematics written to {OUT_DIR}, {skipped} skipped", flush=True)
    if unmapped_ids:
        print("Unmapped legacy IDs (fell back to stone):", flush=True)
        for bid, count in unmapped_ids.most_common(20):
            print(f"  id {bid}: {count} blocks", flush=True)

    for s in list(index.keys())[:15]:
        print(f"  sample: {s}", flush=True)


if __name__ == "__main__":
    main()
