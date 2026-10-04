CinnabarIsland_Mart_Frlg_MapScripts::
	.byte 0

CinnabarIsland_Mart_EventScript_Woman::
	msgbox CinnabarIsland_Mart_Text_DontTheyHaveXAttack, MSGBOX_NPC
	end

CinnabarIsland_Mart_EventScript_Scientist::
	msgbox CinnabarIsland_Mart_Text_ExtraItemsNeverHurt, MSGBOX_NPC
	end

CinnabarIsland_Mart_EventScript_Clerk::
	lock
	faceplayer
	message gText_HowMayIServeYou
	waitmessage
	pokemart CinnabarIsland_Mart_Items
	msgbox gText_PleaseComeAgain
	release
	end

	.align 2
CinnabarIsland_Mart_Items::
	.2byte ITEM_GREAT_BALL
	.2byte ITEM_ULTRA_BALL
	.2byte ITEM_MAX_POTION
	.2byte ITEM_FULL_RESTORE
	.2byte ITEM_REVIVE
	.2byte ITEM_MAX_REVIVE
	.2byte ITEM_FULL_HEAL
	.2byte ITEM_MAX_ETHER
	.2byte ITEM_MAX_ELIXIR
	.2byte ITEM_ESCAPE_ROPE
	.2byte ITEM_MAX_REPEL
	.2byte ITEM_X_ATTACK
	.2byte ITEM_X_DEFENSE
	.2byte ITEM_X_SPEED
	.2byte ITEM_X_SP_ATK
	.2byte ITEM_X_SP_DEF
	.2byte ITEM_X_ACCURACY
	.2byte ITEM_DIRE_HIT
	.2byte ITEM_GUARD_SPEC
	.2byte ITEM_NONE
	release
	end

CinnabarIsland_Mart_Text_DontTheyHaveXAttack::
	.string "Don't they have X ATTACK?\p"
	.string "I like it because it raises the\n"
	.string "ATTACK stat in battle.$"

CinnabarIsland_Mart_Text_ExtraItemsNeverHurt::
	.string "It never hurts to have extra items.\n"
	.string "You never know what might happen.$"

