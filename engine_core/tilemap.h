#pragma once
#include "global.h"

class Tileset {
	private:
	public:
		Tileset() {}
		~Tileset() {}
};

class Tilemap {
	private:
		std::vector<unsigned int> tilemap_buffer;

	public:
		Tilemap() {}
		~Tilemap() {}
};