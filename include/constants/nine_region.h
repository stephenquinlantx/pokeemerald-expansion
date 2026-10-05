#ifndef GUARD_CONSTANTS_NINE_REGION_H
#define GUARD_CONSTANTS_NINE_REGION_H

// Nine-Region hack: save data claimed by custom systems.
// The flags are unused in both FireRed and Emerald; the difficulty var differs per game.

#if IS_FRLG
#define VAR_NR_DIFFICULTY          0x408C  // VAR_0x408C: Easy / Normal / Hard (DIFFICULTY_* values)
#else
#define VAR_NR_DIFFICULTY          0x40F7  // VAR_UNUSED_0x40F7 in Emerald (0x408C is a Littleroot var there)
#endif

#define FLAG_NR_BADGE09            0x4A7   // FLAG_UNUSED_0x4A7: 9th badge, from the region's villain leader
#define FLAG_NR_DIFFICULTY_CHOSEN  0x4A8   // FLAG_UNUSED_0x4A8: difficulty picked at new game
#define FLAG_NR_EXP_SHARE          0x4A9   // FLAG_UNUSED_0x4A9: Gen 6 party Exp. Share switched on
#define FLAG_NR_GOT_EXP_SHARE      0x4AA   // FLAG_UNUSED_0x4AA: Mom gave the Exp. Share

#define NR_BADGES_PER_REGION       9
#define NR_OBEDIENCE_STEP          10      // each badge raises the cap by 10 levels
#define NR_OBEDIENCE_BASE          9       // level that obeys with no badges

#endif // GUARD_CONSTANTS_NINE_REGION_H
