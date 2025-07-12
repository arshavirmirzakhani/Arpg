#pragma once
#include "game.h"
#include "global.h"
#include "spritesheet.h"

int player_pos_x = 50;
int player_pos_y = 50;

int player_speed = 5;

std::string player_sprite_sheet_name;

void process_player() {
	// Movement logic
	if ((IsKeyDown(RIGHT_BUTTON) || IsKeyDown(LEFT_BUTTON)) && (IsKeyDown(DOWN_BUTTON) || IsKeyDown(UP_BUTTON))) {
		player_pos_x += (int)((float)(player_speed * (IsKeyDown(RIGHT_BUTTON) - IsKeyDown(LEFT_BUTTON))) * DIAGONAL_SPEED_FACTOR);
		player_pos_y += (int)((float)(player_speed * (IsKeyDown(DOWN_BUTTON) - IsKeyDown(UP_BUTTON))) * DIAGONAL_SPEED_FACTOR);
	} else {
		player_pos_x += player_speed * (IsKeyDown(RIGHT_BUTTON) - IsKeyDown(LEFT_BUTTON));
		player_pos_y += player_speed * (IsKeyDown(DOWN_BUTTON) - IsKeyDown(UP_BUTTON));
	}

	auto it = spritesheets_list.find(player_sprite_sheet_name);
	if (it != spritesheets_list.end()) {
		SpriteSheet& sheet = it->second;

		if (!sheet.states.empty()) {
			auto anim_it		   = sheet.states.begin();
			const AnimationState& anim = anim_it->second;

			if (!anim.frames.empty()) {
				const SpriteFrame& frame = anim.frames[0];

				Rectangle source = {(float)frame.x, (float)frame.y, (float)sheet.frame_width, (float)sheet.frame_height};

				Rectangle dest = {(float)player_pos_x, (float)player_pos_y, (float)sheet.frame_width, (float)sheet.frame_height};

				Vector2 origin = {0, 0};

				DrawTexturePro(sheet.image, source, dest, origin, 0.0f, WHITE);
				return;
			}
		}
	}

	DrawRectangle(player_pos_x, player_pos_y, 50, 50, RED);
}
