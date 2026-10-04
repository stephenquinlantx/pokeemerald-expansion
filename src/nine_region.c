// Nine-Region hack: custom systems layered on pokeemerald-expansion.
//  - Badge-based obedience caps (9 badges per region, cap = 9 + 10 per badge, 100 at 9)
//  - Difficulty helpers (Easy / Normal / Hard)
//  - Perfect IVs and optimal nature for gifts and legendaries
//  - Bill's simulated trade machine for trade evolutions

#include "global.h"
#include "difficulty.h"
#include "event_data.h"
#include "evolution_scene.h"
#include "field_screen_effect.h"
#include "field_weather.h"
#include "main.h"
#include "nine_region.h"
#include "overworld.h"
#include "palette.h"
#include "pokemon.h"
#include "script.h"
#include "task.h"
#include "constants/difficulty.h"
#include "constants/flags.h"
#include "constants/party_menu.h"
#include "constants/pokemon.h"

// ---------------------------------------------------------------------------
// Badges and obedience
// ---------------------------------------------------------------------------

u32 NR_CountRegionBadges(void)
{
    u32 i, count = 0;

    for (i = FLAG_BADGE01_GET; i <= FLAG_BADGE08_GET; i++)
    {
        if (FlagGet(i))
            count++;
    }
    if (FlagGet(FLAG_NR_BADGE09))
        count++;
    return count;
}

u32 NR_GetObedienceCap(void)
{
    u32 badges = NR_CountRegionBadges();

    if (badges >= NR_BADGES_PER_REGION)
        return MAX_LEVEL;
    return NR_OBEDIENCE_BASE + NR_OBEDIENCE_STEP * badges;
}

bool32 NR_ObedienceEnabled(void)
{
    return GetCurrentDifficultyLevel() != DIFFICULTY_EASY;
}

bool32 NR_IsHardMode(void)
{
    return GetCurrentDifficultyLevel() == DIFFICULTY_HARD;
}

void NR_GetObedienceCapForScript(void)
{
    gSpecialVar_Result = NR_GetObedienceCap();
}

// ---------------------------------------------------------------------------
// Perfect gifts and legendaries
// ---------------------------------------------------------------------------

bool32 NR_IsPerfectWildSpecies(u16 species)
{
    species = SanitizeSpeciesId(species);
    return gSpeciesInfo[species].isRestrictedLegendary
        || gSpeciesInfo[species].isSubLegendary
        || gSpeciesInfo[species].isMythical;
}

// Follow the first listed evolution to the end of the line, so a Magikarp
// gets a nature that suits Gyarados rather than Magikarp.
static u16 GetFinalStage(u16 species)
{
    u32 depth, i;

    for (depth = 0; depth < 3; depth++)
    {
        const struct Evolution *evos = GetSpeciesEvolutions(species);
        u16 next = SPECIES_NONE;

        if (evos == NULL)
            break;
        for (i = 0; evos[i].method != EVOLUTIONS_END; i++)
        {
            if (SanitizeSpeciesId(evos[i].targetSpecies) != SPECIES_NONE)
            {
                next = evos[i].targetSpecies;
                break;
            }
        }
        if (next == SPECIES_NONE)
            break;
        species = next;
    }
    return species;
}

// Picks the standard competitive nature from the final evolution's base stats:
// fast attackers get Jolly/Timid, slower ones Adamant/Modest, and walls get a
// defensive nature that lowers their unused attacking stat.
u8 NR_GetOptimalNature(u16 species)
{
    const struct SpeciesInfo *info = &gSpeciesInfo[SanitizeSpeciesId(GetFinalStage(species))];
    u32 atk = info->baseAttack, spa = info->baseSpAttack, spe = info->baseSpeed;
    u32 def = info->baseDefense, spd = info->baseSpDefense;
    bool32 physical = (atk >= spa);

    if (max(atk, spa) < 80 && def + spd >= 180)
    {
        if (def >= spd)
            return physical ? NATURE_IMPISH : NATURE_BOLD;
        else
            return physical ? NATURE_CAREFUL : NATURE_CALM;
    }
    if (spe >= 80)
        return physical ? NATURE_JOLLY : NATURE_TIMID;
    return physical ? NATURE_ADAMANT : NATURE_MODEST;
}

u32 NR_GetPerfectPersonality(u16 species)
{
    return GetMonPersonality(species, MON_GENDER_RANDOM, NR_GetOptimalNature(species), RANDOM_UNOWN_LETTER);
}

// Gifts to the player (never eggs) and legendary/mythical static encounters
// get 31 IVs in every stat and their optimal nature, unless the script
// already specified them.
void NR_ApplyPerfectTemplate(struct PokemonTemplate *monTemplate, bool32 isGift)
{
    u32 i;
    bool32 perfect;

    if (isGift)
        perfect = !monTemplate->isEgg;
    else
        perfect = NR_IsPerfectWildSpecies(monTemplate->species);

    if (!perfect)
        return;

    if (monTemplate->nature == NATURE_RANDOM)
        monTemplate->nature = NR_GetOptimalNature(monTemplate->species);
    for (i = 0; i < NUM_STATS; i++)
    {
        if (monTemplate->ivs[i] == USE_RANDOM_IVS)
            monTemplate->ivs[i] = MAX_PER_STAT_IVS;
    }
}

// ---------------------------------------------------------------------------
// Bill's simulated trade machine
//   VAR_0x8004: party slot chosen by the player
//   VAR_0x8005: party slot of a trade partner that also evolves (PARTY_SIZE if none)
//   VAR_0x8006: evolution target for the chosen Pokémon
//   VAR_0x8007: evolution target for the partner
// ---------------------------------------------------------------------------

#define tSlot   data[0]
#define tTarget data[1]

static void Task_NR_StartEvolution(u8 taskId)
{
    if (!gPaletteFade.active)
    {
        u8 slot = gTasks[taskId].tSlot;
        u16 target = gTasks[taskId].tTarget;

        CleanupOverworldWindowsAndTilemaps();
        gCB2_AfterEvolution = CB2_ReturnToField;
        gFieldCallback = FieldCB_ContinueScriptHandleMusic;
        BeginEvolutionScene(&gParties[B_TRAINER_PLAYER][slot], target, FALSE, slot);
        DestroyTask(taskId);
    }
}

static void NR_StartEvolution(u8 slot, u16 target)
{
    u8 taskId;

    LockPlayerFieldControls();
    taskId = CreateTask(Task_NR_StartEvolution, 10);
    gTasks[taskId].tSlot = slot;
    gTasks[taskId].tTarget = target;
    FadeScreen(FADE_TO_BLACK, 0);
}

#undef tSlot
#undef tTarget

// Sets VAR_RESULT to TRUE if the chosen Pokémon evolves by trade.
// Pokémon that need a specific trade partner (Karrablast and Shelmet)
// use another party member as the partner, and both evolve.
void NR_BillCheckTradeEvo(void)
{
    u32 slot = gSpecialVar_0x8004;
    u32 i;
    u16 target;

    gSpecialVar_Result = FALSE;
    gSpecialVar_0x8005 = PARTY_SIZE;
    gSpecialVar_0x8006 = SPECIES_NONE;
    gSpecialVar_0x8007 = SPECIES_NONE;

    if (slot >= PARTY_SIZE || GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_IS_EGG)
     || GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_SPECIES) == SPECIES_NONE)
        return;

    // Ordinary trade evolutions, including held-item ones like Onix + Metal Coat.
    target = GetEvolutionTargetSpecies(&gParties[B_TRAINER_PLAYER][slot], EVO_MODE_TRADE, ITEM_NONE, NULL, NULL, CHECK_EVO);
    if (target != SPECIES_NONE)
    {
        gSpecialVar_0x8006 = target;
        gSpecialVar_Result = TRUE;
        return;
    }

    // Partner-specific trade evolutions.
    for (i = 0; i < PARTY_SIZE; i++)
    {
        if (i == slot || GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_SPECIES) == SPECIES_NONE
         || GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_IS_EGG))
            continue;

        target = GetEvolutionTargetSpecies(&gParties[B_TRAINER_PLAYER][slot], EVO_MODE_TRADE, ITEM_NONE, &gParties[B_TRAINER_PLAYER][i], NULL, CHECK_EVO);
        if (target != SPECIES_NONE)
        {
            gSpecialVar_0x8006 = target;
            gSpecialVar_0x8007 = GetEvolutionTargetSpecies(&gParties[B_TRAINER_PLAYER][i], EVO_MODE_TRADE, ITEM_NONE, &gParties[B_TRAINER_PLAYER][slot], NULL, CHECK_EVO);
            if (gSpecialVar_0x8007 != SPECIES_NONE)
                gSpecialVar_0x8005 = i;
            gSpecialVar_Result = TRUE;
            return;
        }
    }
}

// Runs the evolution for the chosen Pokémon. Use after NR_BillCheckTradeEvo.
void NR_BillDoTradeEvo(void)
{
    u32 slot = gSpecialVar_0x8004;
    u32 partner = gSpecialVar_0x8005;
    struct Pokemon *partnerMon = (partner < PARTY_SIZE) ? &gParties[B_TRAINER_PLAYER][partner] : NULL;

    // Apply side effects (such as using up a held item) for both Pokémon
    // before either changes species.
    GetEvolutionTargetSpecies(&gParties[B_TRAINER_PLAYER][slot], EVO_MODE_TRADE, ITEM_NONE, partnerMon, NULL, DO_EVO);
    if (partnerMon != NULL)
        GetEvolutionTargetSpecies(partnerMon, EVO_MODE_TRADE, ITEM_NONE, &gParties[B_TRAINER_PLAYER][slot], NULL, DO_EVO);

    NR_StartEvolution(slot, gSpecialVar_0x8006);
}

// Runs the partner's evolution, if NR_BillCheckTradeEvo found one.
void NR_BillDoPartnerEvo(void)
{
    if (gSpecialVar_0x8005 < PARTY_SIZE && gSpecialVar_0x8007 != SPECIES_NONE)
        NR_StartEvolution(gSpecialVar_0x8005, gSpecialVar_0x8007);
    else
        ScriptContext_Enable();
}
