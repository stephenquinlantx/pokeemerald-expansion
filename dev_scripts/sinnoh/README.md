# Sinnoh build

The `sinnoh` branch is a Gen 4, Sinnoh-only version of the nine-region hack, built in
Emerald mode (`make`, not `make firered`). It keeps the Kanto build's rules: badge-tied
obedience (8 gyms plus Cyrus as the 9th badge), difficulty modes, perfect gifts and
legendaries, early Exp. Share, the trade-evolution machine and scaled marts. The Dex is
limited to the 493 Gen 1-4 Pokémon.

## Maps come from Hyper Emerald: Lost Artifacts

Sinnoh's maps, layouts and tilesets are imported from the Chinese hack
**Pokémon Hyper Emerald: Lost Artifacts** (v5.7) by its original authors, with the English
translation by Nn-Exe (github.com/Nn-Exe/Pokemon-Hyper-Emerald-5.7-QoL). All credit for the
map work is theirs.

They never released those maps for reuse, so **the imported files are never committed or
published**. They are generated locally from your own copy of the ROM:

    python3 dev_scripts/sinnoh/import_sinnoh.py "Hyper Emerald.gba"
    make

Until the import has been run, the branch still builds, but as plain Emerald.

### What the importer does

- Finds the hack's relocated map tables (`hyper_emerald_rom.py` has the addresses).
- Takes every Sinnoh map (213: towns, cities, Routes 201-223, interiors, caves, lakes,
  Mt. Coronet, Great Marsh, Iron Island, Spear Pillar, Distortion World, Victory Road,
  Snowpoint Temple). Hisui and the hack's other extra areas are left out.
- Writes layouts (terrain, collision, elevation), 39 tilesets (three primaries, the rest
  secondaries), warps, connections, music, weather and map types.
- Does **not** bring over the hack's scripts, NPCs, trainers, signs or hidden items. Those
  are dumped to `hack_events.json` (local only) as a reference for writing our own.
- Warps that led to the hack's non-Sinnoh areas point back into their own map; the list
  is in `import_log.txt`.
- Rerunning removes the previous import first. Map scripts you have edited by hand
  (`data/maps/<Map>/scripts.inc`) are kept.

### Map sections

The engine stores map sections in a byte and is nearly full, so Sinnoh reuses Hoenn's
slots, renamed: Twinleaf uses Littleroot's, Routes 201-223 use Routes 101-123, Great Marsh
uses the Safari Zone's, the League uses Ever Grande's, and so on. The full mapping is in
`section_slots.json`. Slots with engine behaviour (secret bases, Battle Frontier,
underwater, the truck) are never used.

### Known gaps in the blockout

- No wild encounters, trainers, NPCs or story scripts yet.
- Tile animations (water, flowers) are static: the hack's animation code isn't imported.
- New games start outside the player's house in Twinleaf; the intro comes later.
- Routes 224-230 aren't in the hack, so they still need blocking out.
