#pragma once
#include "global.h"

enum SPRITE_SHEET_TYPES { NONE, EIGHT_DIR, FOUR_DIR };

struct SpriteFrame {
		int x = 0;
		int y = 0;
};

struct AnimationState {
		std::vector<SpriteFrame> frames;
		int fps;
};

class SpriteSheet {
	private:
	public:
		SpriteSheet() {}
		~SpriteSheet() {}

		SPRITE_SHEET_TYPES sheet_type = NONE;

		std::string image_path;
		Texture2D image;

		int frame_width	 = TILE_SIZE;
		int frame_height = TILE_SIZE;

		float animation_timer	= 0.0f;
		int current_frame_index = 0;

		std::unordered_map<std::string, AnimationState> states;
};

std::unordered_map<std::string, SpriteSheet> spritesheets_list;