#pragma once
#include "global.h"

struct SpriteFrame {
		int x = 0;
		int y = 0;
};

class SpriteSheet {
	private:
	public:
		SpriteSheet() {}
		~SpriteSheet() {}

		Texture2D image;

		int frame_width	 = TILE_SIZE;
		int frame_height = TILE_SIZE;

		std::unordered_map<std::string, std::vector<SpriteFrame>> states;
};