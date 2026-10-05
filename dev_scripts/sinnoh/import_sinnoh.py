#!/usr/bin/env python3
"""Import Hyper Emerald: Lost Artifacts' Sinnoh maps into this project (Emerald mode).

    python3 dev_scripts/sinnoh/import_sinnoh.py "path/to/Hyper Emerald.gba"

Writes layouts, tilesets and map folders under data/, registers them, and adds two map
groups (gMapGroup_Sinnoh, gMapGroup_SinnohIndoor). It is safe to rerun: everything it
generated last time is removed first (tracked in dev_scripts/sinnoh/imported.json).

What comes across: terrain (blocks, collision, elevation, borders), tilesets, warps,
connections, music, weather, map types and flags. What does not: the hack's scripts,
NPCs, trainers, signs and hidden items. Those are dumped to dev_scripts/sinnoh/
hack_events.json as a reference for writing our own.

The maps are the Hyper Emerald team's work. They stay out of anything published:
see the note in dev_scripts/sinnoh/README.md.
"""
import json
import os
import re
import shutil
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from hyper_emerald_rom import Rom  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, 'imported.json')

# Hack map groups that hold Sinnoh, and extra maps the section filter misses.
SINNOH_GROUPS = (36, 37)
EXTRA_GROUPS = (26, 34, 35)
EXTRA_SECTIONS_BY_MAP = {(36, n) for n in range(71, 80)}   # Sinnoh Victory Road, Snowpoint Temple
SKIP_SECTIONS = {'Hisui Region', 'Mauville City', 'Route 121', 'Couriway Town', 'Sootopolis City',
                 'Ancient Retreat', 'Crown Shrine'}

SINNOH_SECTIONS = {
    'Twinleaf Town', 'Sandgem Town', 'Floaroma Town', 'Solaceon Town', 'Celestic Town',
    'Jubilife City', 'Oreburgh City', 'Eterna City', 'Hearthome City', 'Pastoria City',
    'Veilstone City', 'Canalave City', 'Snowpoint City', 'Sunyshore City', 'Sinnoh League',
    'Solaceon Ruins', 'Lost Tower', 'Flower Paradise', 'Sinnoh Region', 'Valor Lakefront',
    'Distortion World', 'Iron Island', 'Mt. Coronet', 'Oreburgh Gate', 'Verity Lakefront',
    'Spear Pillar', 'Oreburgh Mine', 'Acuity Lakefront', 'Pal Park', 'Valley Windworks',
    'Lake Verity', 'Lake Valor', 'Lake Acuity', 'Fuego Ironworks', 'Eterna Forest',
    'Old Chateau', 'Sendoff Spring', 'Ravaged Path', 'Amity Square', 'Spring Path', 'Great Marsh',
    'Victory Road', 'Regigigas Temple',
}

# Hoenn map-section slots reused for Sinnoh (the engine's map sections are a u8 and nearly full).
# Slots with engine behaviour (secret bases, dynamic, Battle Frontier, underwater, the truck)
# are never handed out.
TOWN_SLOTS = {
    'Twinleaf Town': 'LITTLEROOT_TOWN', 'Sandgem Town': 'OLDALE_TOWN',
    'Floaroma Town': 'DEWFORD_TOWN', 'Solaceon Town': 'LAVARIDGE_TOWN',
    'Celestic Town': 'FALLARBOR_TOWN', 'Jubilife City': 'PETALBURG_CITY',
    'Oreburgh City': 'SLATEPORT_CITY', 'Eterna City': 'MAUVILLE_CITY',
    'Hearthome City': 'RUSTBORO_CITY', 'Pastoria City': 'FORTREE_CITY',
    'Veilstone City': 'LILYCOVE_CITY', 'Canalave City': 'MOSSDEEP_CITY',
    'Snowpoint City': 'SOOTOPOLIS_CITY', 'Sunyshore City': 'VERDANTURF_TOWN',
    'Sinnoh League': 'EVER_GRANDE_CITY', 'Great Marsh': 'SAFARI_ZONE',
    'Victory Road': 'VICTORY_ROAD',
}
SPARE_SLOTS = ['PACIFIDLOG_TOWN'] + ['ROUTE_%d' % n for n in range(124, 135)] + [
    'GRANITE_CAVE', 'MT_CHIMNEY', 'PETALBURG_WOODS', 'RUSTURF_TUNNEL', 'ABANDONED_SHIP',
    'NEW_MAUVILLE', 'METEOR_FALLS', 'METEOR_FALLS2', 'MT_PYRE', 'AQUA_HIDEOUT_OLD', 'SHOAL_CAVE',
    'SEAFLOOR_CAVERN', 'MIRAGE_ISLAND', 'CAVE_OF_ORIGIN', 'SOUTHERN_ISLAND', 'FIERY_PATH',
    'FIERY_PATH2', 'JAGGED_PASS', 'JAGGED_PASS2', 'SEALED_CHAMBER', 'SCORCHED_SLAB', 'ISLAND_CAVE',
    'DESERT_RUINS', 'ANCIENT_TOMB', 'SKY_PILLAR', 'FARAWAY_ISLAND', 'ARTISAN_CAVE', 'MARINE_CAVE',
    'TERRA_CAVE', 'DESERT_UNDERPASS', 'ALTERING_CAVE', 'NAVEL_ROCK', 'TRAINER_HILL', 'BIRTH_ISLAND',
]

MAP_TYPES = ['MAP_TYPE_NONE', 'MAP_TYPE_TOWN', 'MAP_TYPE_CITY', 'MAP_TYPE_ROUTE',
             'MAP_TYPE_UNDERGROUND', 'MAP_TYPE_UNDERWATER', 'MAP_TYPE_OCEAN_ROUTE',
             'MAP_TYPE_UNKNOWN', 'MAP_TYPE_INDOOR', 'MAP_TYPE_SECRET_BASE']
OUTDOOR = {1, 2, 3, 6}
WEATHERS = ['WEATHER_NONE', 'WEATHER_SUNNY_CLOUDS', 'WEATHER_SUNNY', 'WEATHER_RAIN',
            'WEATHER_SNOW', 'WEATHER_RAIN_THUNDERSTORM', 'WEATHER_FOG_HORIZONTAL',
            'WEATHER_VOLCANIC_ASH', 'WEATHER_SANDSTORM', 'WEATHER_FOG_DIAGONAL',
            'WEATHER_UNDERWATER', 'WEATHER_SHADE', 'WEATHER_DROUGHT', 'WEATHER_DOWNPOUR',
            'WEATHER_UNDERWATER_BUBBLES', 'WEATHER_ABNORMAL', 'WEATHER_ROUTE119_CYCLE',
            'WEATHER_ROUTE123_CYCLE']
BATTLE_SCENES = ['MAP_BATTLE_SCENE_NORMAL', 'MAP_BATTLE_SCENE_GYM', 'MAP_BATTLE_SCENE_MAGMA',
                 'MAP_BATTLE_SCENE_AQUA', 'MAP_BATTLE_SCENE_SIDNEY', 'MAP_BATTLE_SCENE_PHOEBE',
                 'MAP_BATTLE_SCENE_GLACIA', 'MAP_BATTLE_SCENE_DRAKE', 'MAP_BATTLE_SCENE_FRONTIER']
# Names the hack gives areas that we call by their Sinnoh names.
RENAME_SECTIONS = {'Regigigas Temple': 'Snowpoint Temple'}
CONNECTION_DIRS = {1: 'down', 2: 'up', 3: 'left', 4: 'right', 5: 'dive', 6: 'emerge'}

# The hack kept Emerald's primary tileset slots but redrew General (509 of 512 tiles differ),
# so every primary is extracted. Names for the three primaries Sinnoh uses:
PRIMARY_NAMES = {0x083DF704: 'sinnoh_general', 0x083DF884: 'sinnoh_building',
                 0x089CBC6C: 'sinnoh_outdoor'}

NUM_TILES_PRIMARY = 512
NUM_METATILES_PRIMARY = 512
MAX_METATILES_SECONDARY = 512


def camel(name):
    words = re.sub(r"[^A-Za-z0-9 ]", ' ', name).split()
    return ''.join(w[:1].upper() + w[1:] for w in words)


def snake(name):
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', name)
    s = re.sub(r'(?<=[A-Za-z])(?=[0-9])', '_', s)
    return re.sub(r'[^A-Za-z0-9]+', '_', s).upper().strip('_')


def song_names():
    names = {}
    for m in re.finditer(r'#define (MUS_\w+)\s+(\d+)', open(os.path.join(ROOT, 'include/constants/songs.h')).read()):
        names.setdefault(int(m.group(2)), m.group(1))
    return names


def write_pal(path, colors):
    with open(path, 'w', newline='\r\n') as f:
        f.write('JASC-PAL\n0100\n16\n')
        for c in colors:
            f.write('%d %d %d\n' % ((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3))


def write_tiles_png(path, tile_data, palette):
    """4bpp tile data -> indexed PNG, 16 tiles wide (the layout Porymap expects)."""
    count = len(tile_data) // 32
    rows = (count + 15) // 16
    img = Image.new('P', (128, rows * 8), 0)
    px = img.load()
    for t in range(count):
        tx, ty = (t % 16) * 8, (t // 16) * 8
        for i in range(32):
            b = tile_data[t * 32 + i]
            y, x = divmod(i * 2, 8)
            px[tx + x, ty + y] = b & 0xF
            px[tx + x + 1, ty + y] = b >> 4
    flat = []
    for c in palette:
        flat += [(c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3]
    img.putpalette(flat + [0] * (768 - len(flat)))
    img.save(path, optimize=True)


class Importer:
    def __init__(self, rom_path):
        self.rom = Rom(rom_path)
        self.groups = self.rom.groups()
        self.songs = song_names()
        self.log = []
        self.created = {'maps': [], 'layouts': [], 'tilesets': []}

    # ------------------------------------------------------------------ selection
    def select_maps(self):
        chosen = []
        for g in SINNOH_GROUPS + EXTRA_GROUPS:
            for n, h in enumerate(self.groups[g]):
                hd = self.rom.header(h)
                sec = self.rom.map_section_name(hd['mapsec'])
                route = re.fullmatch(r'Route 2(\d\d)', sec)
                wanted = (sec in SINNOH_SECTIONS or bool(route) or (g, n) in EXTRA_SECTIONS_BY_MAP)
                if sec in SKIP_SECTIONS and (g, n) not in EXTRA_SECTIONS_BY_MAP:
                    wanted = False
                if g in EXTRA_GROUPS and sec in ('Victory Road', 'Sinnoh Region'):
                    wanted = False   # Hoenn's Victory Road copies and hack-only areas
                if wanted:
                    chosen.append((g, n, h, hd, sec))
        return chosen

    # ------------------------------------------------------------------ naming
    def name_maps(self, chosen):
        existing = set(os.listdir(os.path.join(ROOT, 'data/maps')))
        prev = set(self.previous().get('maps', []))
        existing -= prev
        by_sec = {}
        for g, n, h, hd, sec in chosen:
            by_sec.setdefault(sec, []).append((g, n, hd))
        names = {}
        for sec, maps in by_sec.items():
            base = camel(RENAME_SECTIONS.get(sec, sec))
            outdoor = [m for m in maps if m[2]['map_type'] in OUTDOOR]
            first = outdoor[0] if outdoor else None
            idx = 1
            for g, n, hd in maps:
                if (g, n, hd) is first or (first and (g, n) == first[:2]):
                    name = base
                else:
                    name = '%s_%s%d' % (base, 'Inside' if hd['map_type'] == 8 else 'Area', idx)
                    idx += 1
                if name in existing:
                    name += '_Sinnoh'
                names[(g, n)] = name
        return names

    def section_slots(self, chosen):
        slots = dict(TOWN_SLOTS)
        spare = list(SPARE_SLOTS)
        for _, _, _, _, sec in chosen:
            if sec in slots:
                continue
            route = re.fullmatch(r'Route 2(\d\d)', sec)
            if route and int(route.group(1)) <= 23:
                slots[sec] = 'ROUTE_1%02d' % int(route.group(1))
            else:
                slots[sec] = spare.pop(0)
        return slots

    # ------------------------------------------------------------------ cleanup
    def previous(self):
        if os.path.exists(STATE):
            return json.load(open(STATE))
        return {}

    def remove_previous(self):
        prev = self.previous()
        # Scripts written by hand on top of the import survive a rerun.
        self.kept_scripts = {}
        for m in prev.get('maps', []):
            sp = os.path.join(ROOT, 'data/maps', m, 'scripts.inc')
            if os.path.exists(sp):
                text = open(sp).read()
                if text.strip() != '%s_MapScripts::\n\t.byte 0' % m:
                    self.kept_scripts[m] = text
        for m in prev.get('maps', []):
            shutil.rmtree(os.path.join(ROOT, 'data/maps', m), ignore_errors=True)
        for l in prev.get('layouts', []):
            shutil.rmtree(os.path.join(ROOT, 'data/layouts', l), ignore_errors=True)
        for t in prev.get('tilesets', []):
            shutil.rmtree(os.path.join(ROOT, 'data/tilesets', t), ignore_errors=True)
        marker = os.path.join(ROOT, 'include/constants/sinnoh_import.h')
        if os.path.exists(marker):
            os.remove(marker)
        # Generated registrations live between markers, so they can be swapped out wholesale.
        for rel in ('src/data/tilesets/graphics.h', 'src/data/tilesets/metatiles.h',
                    'src/data/tilesets/headers.h'):
            p = os.path.join(ROOT, rel)
            s = open(p).read()
            s = re.sub(r'\n// BEGIN SINNOH IMPORT.*?// END SINNOH IMPORT\n', '\n', s, flags=re.S)
            open(p, 'w').write(s)
        lj = os.path.join(ROOT, 'data/layouts/layouts.json')
        d = json.load(open(lj))
        d['layouts'] = [l for l in d['layouts'] if not l.get('sinnoh_import')]
        json.dump(d, open(lj, 'w'), indent=2)
        gj = os.path.join(ROOT, 'data/maps/map_groups.json')
        d = json.load(open(gj))
        for grp in ('gMapGroup_Sinnoh', 'gMapGroup_SinnohIndoor'):
            if grp in d['group_order']:
                d['group_order'].remove(grp)
            d.pop(grp, None)
        json.dump(d, open(gj, 'w'), indent=2)

    # ------------------------------------------------------------------ tilesets
    def tileset(self, ptr, users):
        if ptr in self.tilesets:
            return self.tilesets[ptr]['label']
        r = self.rom
        ts = r.tileset(ptr)
        secondary = bool(ts['secondary'])
        sec_names = sorted({u for u in users})
        stem = 'sinnoh_' + snake(camel(sec_names[0])).lower() if sec_names else 'sinnoh_%x' % ptr
        stem = PRIMARY_NAMES.get(ptr, stem)
        base = stem
        k = 2
        while any(t['dir'].endswith('/' + stem) for t in self.tilesets.values()):
            stem = '%s_%d' % (base, k)
            k += 1
        kind = 'secondary' if secondary else 'primary'
        rel = 'data/tilesets/%s/%s' % (kind, stem)
        out = os.path.join(ROOT, rel)
        os.makedirs(os.path.join(out, 'palettes'), exist_ok=True)

        pals = [[r.u16(ts['palettes'] + 32 * p + 2 * i) for i in range(16)] for p in range(16)]

        if secondary:
            gap = (ts['attributes'] - ts['metatiles']) // 16
            used = self.max_metatile.get(ptr, 0) + 1
            n_meta = gap if 0 < gap <= MAX_METATILES_SECONDARY and gap >= used else max(used, 8)
            n_meta = min(n_meta, MAX_METATILES_SECONDARY)
        else:
            n_meta = NUM_METATILES_PRIMARY
        metatiles = r.raw(ts['metatiles'], n_meta * 16)
        attrs = r.raw(ts['attributes'], n_meta * 2)

        # Some of the hack's tilesets are flagged compressed but stored raw. For those,
        # take as many tiles as this tileset's own metatiles reference.
        if r.u8(ts['tiles']) == 0x10:
            tiles = r.lz77(ts['tiles'])
        else:
            own = [((metatiles[i] | metatiles[i + 1] << 8) & 0x3FF) for i in range(0, len(metatiles), 2)]
            own = [t - NUM_TILES_PRIMARY if secondary else t for t in own
                   if (t >= NUM_TILES_PRIMARY) == secondary]
            count = (max(own) + 1) if own else 1
            tiles = r.raw(ts['tiles'], count * 32)
            self.log.append('tileset %#x stored raw: %d tiles' % (ptr, count))
        tiles = tiles[:NUM_TILES_PRIMARY * 32]

        open(os.path.join(out, 'metatiles.bin'), 'wb').write(metatiles)
        open(os.path.join(out, 'metatile_attributes.bin'), 'wb').write(attrs)
        for p in range(16):
            write_pal(os.path.join(out, 'palettes', '%02d.pal' % p), pals[p])
        first_pal = 6 if secondary else 0
        write_tiles_png(os.path.join(out, 'tiles.png'), tiles, pals[first_pal])

        label = 'gTileset_' + camel(stem.replace('_', ' '))
        self.tilesets[ptr] = {'label': label, 'dir': rel, 'secondary': secondary,
                              'num_tiles': len(tiles) // 32, 'stem': camel(stem.replace('_', ' '))}
        self.created['tilesets'].append('%s/%s' % (kind, stem))
        return label

    def register_tilesets(self):
        gfx, meta, hdr = [], [], []
        for t in self.tilesets.values():
            s, d = t['stem'], t['dir']
            gfx.append('const u32 gTilesetTiles_%s[] = INCGFX_U32("%s/tiles.png", ".4bpp.fastSmol", "-num_tiles %d -Wnum_tiles");'
                       % (s, d, t['num_tiles']))
            gfx.append('const u16 gTilesetPalettes_%s[][16] =\n{' % s)
            gfx += ['    INCGFX_U16("%s/palettes/%02d.pal", ".gbapal"),' % (d, p) for p in range(16)]
            gfx.append('};\n')
            meta.append('const u16 gMetatiles_%s[] = INCBIN_U16("%s/metatiles.bin");' % (s, d))
            meta.append('const u16 gMetatileAttributes_%s[] = INCBIN_U16("%s/metatile_attributes.bin");' % (s, d))
            hdr.append('const struct Tileset %s =\n{\n    .isCompressed = TRUE,\n    .isSecondary = %s,\n'
                       '    .tiles = gTilesetTiles_%s,\n    .palettes = gTilesetPalettes_%s,\n'
                       '    .metatiles = gMetatiles_%s,\n    .metatileAttributes = gMetatileAttributes_%s,\n'
                       '    .callback = NULL,\n};\n' % (t['label'], 'TRUE' if t['secondary'] else 'FALSE', s, s, s, s))
        for rel, lines, marker in (('src/data/tilesets/graphics.h', gfx, '#else'),
                                   ('src/data/tilesets/metatiles.h', meta, '#else'),
                                   ('src/data/tilesets/headers.h', hdr, '#else')):
            p = os.path.join(ROOT, rel)
            s = open(p).read()
            block = '\n// BEGIN SINNOH IMPORT (dev_scripts/sinnoh/import_sinnoh.py)\n' + '\n'.join(lines) + '\n// END SINNOH IMPORT\n'
            i = s.index('\n' + marker + '\n')   # end of the Emerald (!IS_FRLG) section
            s = s[:i] + block + s[i:]
            open(p, 'w').write(s)

    # ------------------------------------------------------------------ main
    def run(self):
        self.remove_previous()
        chosen = self.select_maps()
        names = self.name_maps(chosen)
        slots = self.section_slots(chosen)
        keys = {(g, n) for g, n, *_ in chosen}

        # highest metatile id each secondary tileset needs, for sizing
        self.max_metatile = {}
        users = {}
        for g, n, h, hd, sec in chosen:
            L = self.rom.layout(hd['layout'])
            users.setdefault(L['secondary'], set()).add(sec)
            users.setdefault(L['primary'], set()).add(sec)
            blk = self.rom.raw(L['blockdata'], L['width'] * L['height'] * 2)
            mx = max(((blk[i] | blk[i + 1] << 8) & 0x3FF) for i in range(0, len(blk), 2))
            if mx >= NUM_METATILES_PRIMARY:
                self.max_metatile[L['secondary']] = max(self.max_metatile.get(L['secondary'], 0),
                                                        mx - NUM_METATILES_PRIMARY)
        self.tilesets = {}

        layouts_json = json.load(open(os.path.join(ROOT, 'data/layouts/layouts.json')))
        layout_ids = {}
        hack_events = {}
        group_out = {'gMapGroup_Sinnoh': [], 'gMapGroup_SinnohIndoor': []}

        for g, n, h, hd, sec in chosen:
            name = names[(g, n)]
            L = self.rom.layout(hd['layout'])
            if hd['layout'] not in layout_ids:
                lname = name
                lid = 'LAYOUT_' + snake(lname)
                ldir = 'data/layouts/' + lname
                os.makedirs(os.path.join(ROOT, ldir), exist_ok=True)
                open(os.path.join(ROOT, ldir, 'map.bin'), 'wb').write(
                    self.rom.raw(L['blockdata'], L['width'] * L['height'] * 2))
                open(os.path.join(ROOT, ldir, 'border.bin'), 'wb').write(self.rom.raw(L['border'], 8))
                layouts_json['layouts'].append({
                    'id': lid, 'name': lname + '_Layout', 'width': L['width'], 'height': L['height'],
                    'primary_tileset': self.tileset(L['primary'], users[L['primary']]),
                    'secondary_tileset': self.tileset(L['secondary'], users[L['secondary']]),
                    'border_filepath': ldir + '/border.bin', 'blockdata_filepath': ldir + '/map.bin',
                    'layout_version': 'emerald', 'sinnoh_import': True,
                })
                layout_ids[hd['layout']] = lid
                self.created['layouts'].append(lname)

            ev = self.rom.events(hd['events'])
            warps = []
            for w in ev['warps']:
                dest = (w['dest_group'], w['dest_num'])
                if dest in keys:
                    warps.append({'x': w['x'], 'y': w['y'], 'elevation': w['elevation'],
                                  'dest_map': 'MAP_' + snake(names[dest]), 'dest_warp_id': str(w['dest_warp'])})
                else:
                    self.log.append('%s: warp at (%d,%d) led outside Sinnoh (%d.%d); points back here'
                                    % (name, w['x'], w['y'], *dest))
                    warps.append({'x': w['x'], 'y': w['y'], 'elevation': w['elevation'],
                                  'dest_map': 'MAP_' + snake(name), 'dest_warp_id': '0'})
            conns = []
            if hd['map_type'] != 8:
                for c in self.rom.connections(hd['connections']):
                    dest = (c['group'], c['num'])
                    if dest in keys and c['direction'] in CONNECTION_DIRS:
                        conns.append({'map': 'MAP_' + snake(names[dest]), 'offset': c['offset'],
                                      'direction': CONNECTION_DIRS[c['direction']]})
            music = self.songs.get(hd['music'])
            if music is None:
                music = 'MUS_ROUTE101'
                self.log.append('%s: unknown song %d, using Route 101' % (name, hd['music']))
            mj = {
                'id': 'MAP_' + snake(name), 'name': name, 'layout': layout_ids[hd['layout']],
                'music': music, 'region': 'REGION_SINNOH',
                'region_map_section': 'MAPSEC_' + slots[sec],
                'requires_flash': bool(hd['cave'] == 1),
                'weather': WEATHERS[hd['weather']] if hd['weather'] < len(WEATHERS) else 'WEATHER_NONE',
                'map_type': MAP_TYPES[hd['map_type']] if hd['map_type'] < len(MAP_TYPES) else 'MAP_TYPE_NONE',
                'allow_cycling': hd['allow_cycling'], 'allow_escaping': hd['allow_escaping'],
                'allow_running': hd['allow_running'], 'show_map_name': hd['show_map_name'],
                'battle_scene': BATTLE_SCENES[hd['battle_scene']] if hd['battle_scene'] < len(BATTLE_SCENES) else 'MAP_BATTLE_SCENE_NORMAL',
                'connections': conns or None,
                'object_events': [], 'warp_events': warps, 'coord_events': [], 'bg_events': [],
            }
            mdir = os.path.join(ROOT, 'data/maps', name)
            os.makedirs(mdir, exist_ok=True)
            json.dump(mj, open(os.path.join(mdir, 'map.json'), 'w'), indent=2)
            spath = os.path.join(mdir, 'scripts.inc')
            if name in self.kept_scripts:
                open(spath, 'w').write(self.kept_scripts[name])
            else:
                open(spath, 'w').write('%s_MapScripts::\n\t.byte 0\n' % name)
            self.created['maps'].append(name)
            group_out['gMapGroup_Sinnoh' if g in SINNOH_GROUPS[:1] or hd['map_type'] in OUTDOOR
                      else 'gMapGroup_SinnohIndoor'].append(name)
            hack_events[name] = {'hack_map': '%d.%d' % (g, n), 'section': sec,
                                 'objects': ev['objects'], 'coord_events': ev['coords'],
                                 'bg_events': ev['bgs']}

        self.register_tilesets()
        open(os.path.join(ROOT, 'include/constants/sinnoh_import.h'), 'w').write(
            '// Generated by dev_scripts/sinnoh/import_sinnoh.py: present once Sinnoh has been imported.\n'
            '#define SINNOH_IMPORTED 1\n')
        open(os.path.join(ROOT, 'data/maps/sinnoh_scripts.inc'), 'w').write(
            '@ Generated by dev_scripts/sinnoh/import_sinnoh.py: map script files for the Sinnoh maps.\n'
            + ''.join('\t.include "data/maps/%s/scripts.inc"\n' % m for m in self.created['maps']))
        json.dump(layouts_json, open(os.path.join(ROOT, 'data/layouts/layouts.json'), 'w'), indent=2)
        gj = os.path.join(ROOT, 'data/maps/map_groups.json')
        d = json.load(open(gj))
        for grp, maps in group_out.items():
            d['group_order'].append(grp)
            d[grp] = maps
        json.dump(d, open(gj, 'w'), indent=2)

        json.dump(self.created, open(STATE, 'w'), indent=2)
        json.dump({'section_slots': slots}, open(os.path.join(HERE, 'section_slots.json'), 'w'), indent=2)
        json.dump(hack_events, open(os.path.join(HERE, 'hack_events.json'), 'w'), indent=1)
        open(os.path.join(HERE, 'import_log.txt'), 'w').write('\n'.join(self.log) + '\n')
        print('%d maps, %d layouts, %d new tilesets; %d notes in import_log.txt'
              % (len(self.created['maps']), len(self.created['layouts']), len(self.tilesets), len(self.log)))


if __name__ == '__main__':
    Importer(sys.argv[1]).run()
