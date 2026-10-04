#include "global.h"
#include "event_data.h"
#include "nine_region.h"
#include "pokemon.h"
#include "test/test.h"
#include "constants/flags.h"

static void ClearRegionBadges(void)
{
    u32 i;
    for (i = FLAG_BADGE01_GET; i <= FLAG_BADGE08_GET; i++)
        FlagClear(i);
    FlagClear(FLAG_NR_BADGE09);
}

TEST("Nine-Region: obedience cap rises 10 levels per badge and reaches 100 at nine badges")
{
    ClearRegionBadges();
    EXPECT_EQ(NR_GetObedienceCap(), 9);

    FlagSet(FLAG_BADGE01_GET);
    EXPECT_EQ(NR_GetObedienceCap(), 19);

    FlagSet(FLAG_BADGE02_GET);
    FlagSet(FLAG_BADGE03_GET);
    FlagSet(FLAG_BADGE04_GET);
    FlagSet(FLAG_BADGE05_GET);
    FlagSet(FLAG_BADGE06_GET);
    FlagSet(FLAG_BADGE07_GET);
    FlagSet(FLAG_BADGE08_GET);
    EXPECT_EQ(NR_CountRegionBadges(), 8);
    EXPECT_EQ(NR_GetObedienceCap(), 89);

    FlagSet(FLAG_NR_BADGE09);
    EXPECT_EQ(NR_GetObedienceCap(), MAX_LEVEL);
    ClearRegionBadges();
}

TEST("Nine-Region: optimal nature suits the final evolution")
{
    EXPECT_EQ(NR_GetOptimalNature(SPECIES_CHARMANDER), NATURE_TIMID);   // Charizard: special, fast
    EXPECT_EQ(NR_GetOptimalNature(SPECIES_MAGIKARP), NATURE_JOLLY);     // Gyarados: physical, fast
    EXPECT_EQ(NR_GetOptimalNature(SPECIES_HITMONCHAN), NATURE_ADAMANT); // physical, slower
    EXPECT_EQ(NR_GetOptimalNature(SPECIES_MEWTWO), NATURE_TIMID);
}

TEST("Nine-Region: only legendaries and mythicals count as perfect wild encounters")
{
    EXPECT(NR_IsPerfectWildSpecies(SPECIES_MEWTWO));
    EXPECT(NR_IsPerfectWildSpecies(SPECIES_ARTICUNO));
    EXPECT(NR_IsPerfectWildSpecies(SPECIES_MEW));
    EXPECT(!NR_IsPerfectWildSpecies(SPECIES_SNORLAX));
}

TEST("Nine-Region: gift templates become perfect but eggs do not")
{
    u32 i;
    struct PokemonTemplate gift = {0};
    struct PokemonTemplate egg = {0};

    gift.species = SPECIES_BULBASAUR;
    gift.nature = NATURE_RANDOM;
    egg.species = SPECIES_TOGEPI;
    egg.nature = NATURE_RANDOM;
    egg.isEgg = TRUE;
    for (i = 0; i < NUM_STATS; i++)
    {
        gift.ivs[i] = USE_RANDOM_IVS;
        egg.ivs[i] = USE_RANDOM_IVS;
    }

    NR_ApplyPerfectTemplate(&gift, TRUE);
    NR_ApplyPerfectTemplate(&egg, TRUE);

    EXPECT_EQ(gift.nature, NR_GetOptimalNature(SPECIES_BULBASAUR));
    EXPECT_EQ(egg.nature, NATURE_RANDOM);
    for (i = 0; i < NUM_STATS; i++)
    {
        EXPECT_EQ(gift.ivs[i], MAX_PER_STAT_IVS);
        EXPECT_EQ(egg.ivs[i], USE_RANDOM_IVS);
    }
}

TEST("Nine-Region: disobedience chance is 10% per level over the cap")
{
    EXPECT_EQ(NR_GetDisobeyChance(19, 19), 0);
    EXPECT_EQ(NR_GetDisobeyChance(15, 19), 0);
    EXPECT_EQ(NR_GetDisobeyChance(20, 19), 10);
    EXPECT_EQ(NR_GetDisobeyChance(24, 19), 50);
    EXPECT_EQ(NR_GetDisobeyChance(29, 19), 100);
    EXPECT_EQ(NR_GetDisobeyChance(60, 19), 100);
}
