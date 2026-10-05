"""Read map data out of a Hyper Emerald: Lost Artifacts ROM (Emerald engine, relocated tables).

Only the structures the Emerald engine uses are read: map groups, map headers, layouts,
tilesets, events and connections. Nothing here is specific to Sinnoh; the caller picks maps.
"""
import struct

ROM_BASE = 0x08000000

# Found by scanning the v5.7 ROM: the hack moved both tables out of vanilla space.
MAP_GROUPS = 0x08A54698      # 38 groups (vanilla Emerald has 34)
MAP_GROUP_COUNT = 38
MAP_LAYOUTS = 0x08CFD124     # gMapLayouts copy the headers' layout ids index into
REGION_MAP_ENTRIES = 0x085A147C  # 8-byte entries: x, y, w, h, name pointer

CHARMAP = {0x00: ' ', 0xAB: '!', 0xAC: '?', 0xAD: '.', 0xAE: '-', 0xB0: '...', 0xB4: "'",
           0xB8: ',', 0xBA: '/', 0x1B: 'e', 0xB5: 'm', 0xB6: 'f'}


class Rom:
    def __init__(self, path):
        self.data = open(path, 'rb').read()
        self.size = len(self.data)

    # --- primitives -------------------------------------------------------
    def off(self, ptr):
        return ptr - ROM_BASE

    def is_ptr(self, v):
        return ROM_BASE <= v < ROM_BASE + self.size

    def u8(self, ptr):
        return self.data[self.off(ptr)]

    def s8(self, ptr):
        return struct.unpack_from('<b', self.data, self.off(ptr))[0]

    def u16(self, ptr):
        return struct.unpack_from('<H', self.data, self.off(ptr))[0]

    def s16(self, ptr):
        return struct.unpack_from('<h', self.data, self.off(ptr))[0]

    def u32(self, ptr):
        return struct.unpack_from('<I', self.data, self.off(ptr))[0]

    def s32(self, ptr):
        return struct.unpack_from('<i', self.data, self.off(ptr))[0]

    def raw(self, ptr, n):
        o = self.off(ptr)
        return self.data[o:o + n]

    def text(self, ptr, limit=64):
        out = ''
        for b in self.raw(ptr, limit):
            if b == 0xFF:
                break
            if 0xBB <= b <= 0xD4:
                out += chr(ord('A') + b - 0xBB)
            elif 0xD5 <= b <= 0xEE:
                out += chr(ord('a') + b - 0xD5)
            elif 0xA1 <= b <= 0xAA:
                out += chr(ord('0') + b - 0xA1)
            else:
                out += CHARMAP.get(b, '')
        return out

    def lz77(self, ptr):
        """GBA BIOS LZ77 (type 0x10)."""
        o = self.off(ptr)
        d = self.data
        if d[o] != 0x10:
            raise ValueError('not LZ77 at %#x' % ptr)
        size = d[o + 1] | d[o + 2] << 8 | d[o + 3] << 16
        out = bytearray()
        o += 4
        while len(out) < size:
            flags = d[o]
            o += 1
            for bit in range(8):
                if len(out) >= size:
                    break
                if flags & (0x80 >> bit):
                    b1, b2 = d[o], d[o + 1]
                    o += 2
                    length = (b1 >> 4) + 3
                    disp = ((b1 & 0xF) << 8 | b2) + 1
                    for _ in range(length):
                        out.append(out[-disp])
                else:
                    out.append(d[o])
                    o += 1
        return bytes(out[:size])

    # --- map tables -------------------------------------------------------
    def map_section_name(self, sec):
        return self.text(self.u32(REGION_MAP_ENTRIES + 8 * sec + 4))

    def groups(self):
        """List of groups, each a list of map header pointers. Groups are stored
        back to back, so a group ends where the next one starts or where the run
        of valid header pointers ends."""
        starts = [self.u32(MAP_GROUPS + 4 * i) for i in range(MAP_GROUP_COUNT)]
        result = []
        for p in starts:
            later = [q for q in starts if q > p]
            stop = min(later) if later else None
            maps = []
            q = p
            while (stop is None or q < stop) and self.is_header(self.u32(q)):
                maps.append(self.u32(q))
                q += 4
            result.append(maps)
        return result

    def is_header(self, h):
        if not self.is_ptr(h) or h % 4:
            return False
        layout = self.u32(h)
        if not self.is_ptr(layout):
            return False
        lid = self.u16(h + 18)
        return 0 < lid < 2000 and self.u32(MAP_LAYOUTS + 4 * (lid - 1)) == layout

    def header(self, h):
        flags = self.u8(h + 26)
        return {
            'layout': self.u32(h),
            'events': self.u32(h + 4),
            'scripts': self.u32(h + 8),
            'connections': self.u32(h + 12),
            'music': self.u16(h + 16),
            'layout_id': self.u16(h + 18),
            'mapsec': self.u8(h + 20),
            'cave': self.u8(h + 21),
            'weather': self.u8(h + 22),
            'map_type': self.u8(h + 23),
            'allow_cycling': bool(flags & 1),
            'allow_escaping': bool(flags & 2),
            'allow_running': bool(flags & 4),
            'show_map_name': bool(flags >> 3),
            'battle_scene': self.u8(h + 27),
        }

    def layout(self, ptr):
        return {
            'width': self.s32(ptr),
            'height': self.s32(ptr + 4),
            'border': self.u32(ptr + 8),
            'blockdata': self.u32(ptr + 12),
            'primary': self.u32(ptr + 16),
            'secondary': self.u32(ptr + 20),
        }

    def tileset(self, ptr):
        return {
            'compressed': self.u8(ptr),
            'secondary': self.u8(ptr + 1),
            'tiles': self.u32(ptr + 4),
            'palettes': self.u32(ptr + 8),
            'metatiles': self.u32(ptr + 12),
            'attributes': self.u32(ptr + 16),
            'callback': self.u32(ptr + 20),
        }

    def events(self, ptr):
        if not self.is_ptr(ptr):
            return {'objects': [], 'warps': [], 'coords': [], 'bgs': []}
        n_obj, n_warp, n_coord, n_bg = (self.u8(ptr + i) for i in range(4))
        p_obj, p_warp, p_coord, p_bg = (self.u32(ptr + 4 + 4 * i) for i in range(4))
        objs, warps, coords, bgs = [], [], [], []
        for i in range(n_obj if self.is_ptr(p_obj) else 0):
            o = p_obj + 24 * i
            rng = self.u8(o + 10)
            objs.append({
                'local_id': self.u8(o), 'gfx': self.u8(o + 1), 'kind': self.u8(o + 2),
                'x': self.s16(o + 4), 'y': self.s16(o + 6), 'elevation': self.u8(o + 8),
                'movement': self.u8(o + 9), 'range_x': rng & 0xF, 'range_y': rng >> 4,
                'trainer_type': self.u16(o + 12), 'sight': self.u16(o + 14),
                'script': self.u32(o + 16), 'flag': self.u16(o + 20),
            })
        for i in range(n_warp if self.is_ptr(p_warp) else 0):
            o = p_warp + 8 * i
            warps.append({'x': self.s16(o), 'y': self.s16(o + 2), 'elevation': self.u8(o + 4),
                          'dest_warp': self.u8(o + 5), 'dest_num': self.u8(o + 6),
                          'dest_group': self.u8(o + 7)})
        for i in range(n_coord if self.is_ptr(p_coord) else 0):
            o = p_coord + 16 * i
            coords.append({'x': self.s16(o), 'y': self.s16(o + 2), 'elevation': self.u8(o + 4),
                           'var': self.u16(o + 6), 'value': self.u16(o + 8),
                           'script': self.u32(o + 12)})
        for i in range(n_bg if self.is_ptr(p_bg) else 0):
            o = p_bg + 12 * i
            bgs.append({'x': self.s16(o), 'y': self.s16(o + 2), 'elevation': self.u8(o + 4),
                        'kind': self.u8(o + 5), 'arg': self.u32(o + 8)})
        return {'objects': objs, 'warps': warps, 'coords': coords, 'bgs': bgs}

    def connections(self, ptr):
        if not self.is_ptr(ptr):
            return []
        count = self.s32(ptr)
        lst = self.u32(ptr + 4)
        out = []
        for i in range(count if 0 < count < 16 and self.is_ptr(lst) else 0):
            o = lst + 12 * i
            out.append({'direction': self.u8(o), 'offset': self.s32(o + 4),
                        'group': self.u8(o + 8), 'num': self.u8(o + 9)})
        return out
