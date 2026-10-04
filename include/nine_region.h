#ifndef GUARD_NINE_REGION_H
#define GUARD_NINE_REGION_H

#include "constants/nine_region.h"

struct PokemonTemplate;

// Badges and obedience
u32 NR_CountRegionBadges(void);
u32 NR_GetObedienceCap(void);
u32 NR_GetDisobeyChance(u32 level, u32 cap);
bool32 NR_ObedienceEnabled(void);
bool32 NR_IsHardMode(void);

// Perfect gifts and legendaries
bool32 NR_IsPerfectWildSpecies(u16 species);
u8 NR_GetOptimalNature(u16 species);
void NR_ApplyPerfectTemplate(struct PokemonTemplate *monTemplate, bool32 isGift);
u32 NR_GetPerfectPersonality(u16 species);

// Script specials
void NR_GetObedienceCapForScript(void);
void NR_BillCheckTradeEvo(void);
void NR_BillDoTradeEvo(void);
void NR_BillDoPartnerEvo(void);

#endif // GUARD_NINE_REGION_H
