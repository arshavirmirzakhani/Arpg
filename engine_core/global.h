#pragma once
#include <iostream>
#include <map>
#include <raygui.h>
#include <raylib.h>
#include <string>
#include <unordered_map>
#include <vector>

#define TILE_SIZE 8
#define DIAGONAL_SPEED_FACTOR 0.8
struct AssetData {
		const unsigned char* data;
		size_t size;
};

std::unordered_map<std::string, AssetData> assets_list;

enum DIRECTION { UP, UP_RIGHT, RIGHT, DOWN_RIGHT, DOWN, DOWN_LEFT, LEFT, UP_LEFT };

DIRECTION rotate_cw_45(DIRECTION dir) {
	int result = ((int)dir + 1);

	if (result > DIRECTION::UP_LEFT) {
		result = DIRECTION::UP;
	}

	return (DIRECTION)result;
}

DIRECTION rotate_ccw_45(DIRECTION dir) {
	int result = ((int)dir - 1);

	if (result < DIRECTION::UP) {
		result = DIRECTION::UP_LEFT;
	}

	return (DIRECTION)result;
}

Camera2D camera = {0};