#pragma once
#include "game.h"
#include "global.h"

int player_pos_x = 50;
int player_pos_y = 50;

int player_speed = 5;

const float DIAGONAL_SPEED_FACTOR = (float)0.8;

void process_player() {
	DrawRectangle(player_pos_x, player_pos_y, 50, 50, RED);

	if ((IsKeyDown(RIGHT_BUTTON) || IsKeyDown(LEFT_BUTTON)) && (IsKeyDown(DOWN_BUTTON) || IsKeyDown(UP_BUTTON))) {
		player_pos_x += (int)((float)(player_speed * (IsKeyDown(RIGHT_BUTTON) - IsKeyDown(LEFT_BUTTON))) * DIAGONAL_SPEED_FACTOR);
		player_pos_y += (int)((float)(player_speed * (IsKeyDown(DOWN_BUTTON) - IsKeyDown(UP_BUTTON))) * DIAGONAL_SPEED_FACTOR);
	} else {
		player_pos_x += player_speed * (IsKeyDown(RIGHT_BUTTON) - IsKeyDown(LEFT_BUTTON));
		player_pos_y += player_speed * (IsKeyDown(DOWN_BUTTON) - IsKeyDown(UP_BUTTON));
	}
}
