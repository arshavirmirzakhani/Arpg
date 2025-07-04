#pragma once
#include "game.h"
#include "global.h"

int player_pos_x = 50;
int player_pos_y = 50;

int player_speed = 5;

void process_player() {
	DrawRectangle(player_pos_x, player_pos_y, 50, 50, RED);
	player_pos_x += player_speed * (IsKeyDown(RIGHT_BUTTON) - IsKeyDown(LEFT_BUTTON));
	player_pos_y += player_speed * (IsKeyDown(DOWN_BUTTON) - IsKeyDown(UP_BUTTON));
}
