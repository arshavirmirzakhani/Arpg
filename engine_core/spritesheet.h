#pragma once
#include "global.h"

enum SPRITE_SHEET_TYPES { NONE, EIGHT_DIR, FOUR_DIR };

struct SpriteFrame {
		int x = 0;
		int y = 0;
};

class SpriteSheet {
	private:
	public:
		SpriteSheet() {}
		~SpriteSheet() {}

		SPRITE_SHEET_TYPES sheet_type = NONE;

		Texture2D image;

		int frame_width	 = TILE_SIZE;
		int frame_height = TILE_SIZE;

		std::unordered_map<std::string, std::vector<SpriteFrame>> states;
};