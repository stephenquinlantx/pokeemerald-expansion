PalletTown_PlayersHouse_2F_Frlg_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, PalletTown_PlayersHouse_2F_OnTransition
	map_script MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE, PalletTown_PlayersHouse_2F_OnWarp
	map_script MAP_SCRIPT_ON_FRAME_TABLE, PalletTown_PlayersHouse_2F_OnFrame
	.byte 0

PalletTown_PlayersHouse_2F_OnTransition::
	call_if_eq VAR_MAP_SCENE_PALLET_TOWN_PLAYERS_HOUSE_2F, 0, PalletTown_PlayersHouse_2F_EventScript_SetRespawn
	end

PalletTown_PlayersHouse_2F_EventScript_SetRespawn::
	setrespawn HEAL_LOCATION_PALLET_TOWN
	return

PalletTown_PlayersHouse_2F_OnWarp::
	map_script_2 VAR_MAP_SCENE_PALLET_TOWN_PLAYERS_HOUSE_2F, 0, PalletTown_PlayersHouse_2F_FirstWarpIn
	.2byte 0

PalletTown_PlayersHouse_2F_FirstWarpIn::
	turnobject LOCALID_PLAYER, DIR_NORTH
	setvar VAR_MAP_SCENE_PALLET_TOWN_PLAYERS_HOUSE_2F, 1
	end

@ Nine-Region: pick a difficulty the first time the game starts.
PalletTown_PlayersHouse_2F_OnFrame::
	map_script_2 VAR_MAP_SCENE_PALLET_TOWN_PLAYERS_HOUSE_2F, 1, PalletTown_PlayersHouse_2F_EventScript_ChooseDifficulty
	.2byte 0

PalletTown_PlayersHouse_2F_EventScript_ChooseDifficulty::
	lockall
	goto_if_set FLAG_NR_DIFFICULTY_CHOSEN, PalletTown_PlayersHouse_2F_EventScript_DifficultyDone
	msgbox PalletTown_PlayersHouse_2F_Text_DifficultyIntro, MSGBOX_DEFAULT
PalletTown_PlayersHouse_2F_EventScript_DifficultyMenu::
	message PalletTown_PlayersHouse_2F_Text_ChooseDifficulty
	waitmessage
	dynmultichoice 0, 0, TRUE, 3, 1, DYN_MULTICHOICE_CB_NONE, PalletTown_PlayersHouse_2F_Text_Easy, PalletTown_PlayersHouse_2F_Text_Normal, PalletTown_PlayersHouse_2F_Text_Hard
	goto_if_eq VAR_RESULT, 0, PalletTown_PlayersHouse_2F_EventScript_PickEasy
	goto_if_eq VAR_RESULT, 2, PalletTown_PlayersHouse_2F_EventScript_PickHard
	msgbox PalletTown_PlayersHouse_2F_Text_ConfirmNormal, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, PalletTown_PlayersHouse_2F_EventScript_DifficultyMenu
	setdifficulty DIFFICULTY_NORMAL
	goto PalletTown_PlayersHouse_2F_EventScript_DifficultySet

PalletTown_PlayersHouse_2F_EventScript_PickEasy::
	msgbox PalletTown_PlayersHouse_2F_Text_ConfirmEasy, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, PalletTown_PlayersHouse_2F_EventScript_DifficultyMenu
	setdifficulty DIFFICULTY_EASY
	goto PalletTown_PlayersHouse_2F_EventScript_DifficultySet

PalletTown_PlayersHouse_2F_EventScript_PickHard::
	msgbox PalletTown_PlayersHouse_2F_Text_ConfirmHard, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, PalletTown_PlayersHouse_2F_EventScript_DifficultyMenu
	setdifficulty DIFFICULTY_HARD
	goto PalletTown_PlayersHouse_2F_EventScript_DifficultySet

PalletTown_PlayersHouse_2F_EventScript_DifficultySet::
	setflag FLAG_NR_DIFFICULTY_CHOSEN
	msgbox PalletTown_PlayersHouse_2F_Text_DifficultySet, MSGBOX_DEFAULT
PalletTown_PlayersHouse_2F_EventScript_DifficultyDone::
	setvar VAR_MAP_SCENE_PALLET_TOWN_PLAYERS_HOUSE_2F, 2
	releaseall
	end

PalletTown_PlayersHouse_2F_EventScript_NES::
	msgbox PalletTown_PlayersHouse_2F_Text_PlayedWithNES, MSGBOX_SIGN
	end

PalletTown_PlayersHouse_2F_EventScript_Sign::
	msgbox PalletTown_PlayersHouse_2F_Text_PressLRForHelp, MSGBOX_SIGN
	end

PalletTown_PlayersHouse_2F_Text_PlayedWithNES::
	.string "{PLAYER} played with the NES.\p"
	.string "…Okay!\n"
	.string "It's time to go!$"

PalletTown_PlayersHouse_2F_Text_PressLRForHelp::
	.string "It's a posted notice…\p"
	.string "If you're confused, ask for HELP!\n"
	.string "Press the L or R Button!$"


PalletTown_PlayersHouse_2F_Text_DifficultyIntro::
	.string "Before your journey begins, choose\n"
	.string "how tough it should be.$"

PalletTown_PlayersHouse_2F_Text_ChooseDifficulty::
	.string "Which difficulty?$"

PalletTown_PlayersHouse_2F_Text_Easy::
	.string "EASY$"

PalletTown_PlayersHouse_2F_Text_Normal::
	.string "NORMAL$"

PalletTown_PlayersHouse_2F_Text_Hard::
	.string "HARD$"

PalletTown_PlayersHouse_2F_Text_ConfirmEasy::
	.string "EASY: every POKéMON always obeys,\n"
	.string "whatever its level.\p"
	.string "Play on EASY? This can't be changed\n"
	.string "later.$"

PalletTown_PlayersHouse_2F_Text_ConfirmNormal::
	.string "NORMAL: POKéMON above your BADGE\n"
	.string "level may ignore orders.\p"
	.string "Play on NORMAL? This can't be\n"
	.string "changed later.$"

PalletTown_PlayersHouse_2F_Text_ConfirmHard::
	.string "HARD: POKéMON above your BADGE level\n"
	.string "never obey, and the party EXP. SHARE\l"
	.string "is disabled.\p"
	.string "Play on HARD? This can't be changed\n"
	.string "later.$"

PalletTown_PlayersHouse_2F_Text_DifficultySet::
	.string "Difficulty set. Good luck!$"
