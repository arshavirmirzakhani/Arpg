#include <engine.h>
#include <iostream>
#include <raylib.h>
#include <rlgl.h>
#include <string>
#include <toml.hpp>
#include <zip.h>

int main(void) {

	// Load game data
	unsigned char* buf;
	size_t bufsize;
	bool zip_loaded = true;

	struct zip_t* zip = zip_open("data.arpg", 0, 'r');
	if (zip) {

		zip_entry_open(zip, "project.toml"); // read project data
		{
			bufsize = zip_entry_size(zip);
			buf	= (unsigned char*)calloc(sizeof(unsigned char), bufsize);

			zip_entry_noallocread(zip, (void*)buf, bufsize);

			std::string_view string((const char*)buf, bufsize);
			toml::table tbl = toml::parse(string);

			auto title   = tbl.get("window_title")->value<std::string>();
			WINDOW_TITLE = *title;
		}
		zip_entry_close(zip);

		int i, n = (int)zip_entries_total(zip);
		for (i = 0; i < n; ++i) {
			zip_entry_openbyindex(zip, i);
			{
				if (!zip_entry_isdir(zip)) {

					// load assets
					if (std::string(zip_entry_name(zip)).find("assets/") != std::string::npos &&
					    std::string(zip_entry_name(zip)).find("assets/") == 0) {
						bufsize = zip_entry_size(zip);
						buf	= (unsigned char*)calloc(sizeof(unsigned char), bufsize);

						zip_entry_noallocread(zip, (void*)buf, bufsize);

						assets_list[std::string(zip_entry_name(zip)).substr(strlen("assets/"))] = AssetData{buf, bufsize};
					}

					// load spritesheets

					else if (std::string(zip_entry_name(zip)).find("spritesheets/") != std::string::npos &&
						 std::string(zip_entry_name(zip)).find("spritesheets/") == 0) {
						bufsize = zip_entry_size(zip);
						buf	= (unsigned char*)calloc(sizeof(unsigned char), bufsize);

						zip_entry_noallocread(zip, (void*)buf, bufsize);

						std::string_view string((const char*)buf, bufsize);
						toml::table tbl = toml::parse(string);

						auto image  = tbl.get("image_path")->value<std::string>();
						auto width  = tbl.get("width")->value<toml::int32_t>();
						auto height = tbl.get("height")->value<toml::int32_t>();

						SpriteSheet sheet;

						sheet.image_path   = *image;
						sheet.frame_width  = *width;
						sheet.frame_height = *height;

						if (auto states_tbl = tbl["states"].as_table()) {
							for (const auto& [state_name, state_value] : *states_tbl) {
								if (auto anim_tbl = state_value.as_table()) {
									AnimationState anim;
									anim.fps = anim_tbl->get("fps")->value_or(6);

									if (auto frames_array = anim_tbl->get("frames")->as_array()) {
										for (const auto& frame : *frames_array) {
											if (auto xy = frame.as_array(); xy && xy->size() == 2) {
												int x = (*xy)[0].value_or(0);
												int y = (*xy)[1].value_or(0);
												anim.frames.push_back({x, y});
											}
										}
									}
									sheet.states[state_name.data()] = anim;
								}
							}
						}

						spritesheets_list[std::string(zip_entry_name(zip)).substr(strlen("spritesheets/"))] = sheet;
					}
				}
			}
			zip_entry_close(zip);
		}
		zip_close(zip);

		free(buf);
	} else {
		zip_loaded = false;
	}

	// Initialize window
	// SetTraceLogLevel(LOG_WARNING);
	SetConfigFlags(FLAG_WINDOW_RESIZABLE);
	InitWindow(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE.c_str());
	InitAudioDevice();
	SetTargetFPS(60);

	// Initialize game

	for (auto& [name, spritesheet] : spritesheets_list) {
		auto it		       = assets_list.find(spritesheet.image_path);
		const AssetData& asset = it->second;

		Image img = LoadImageFromMemory(GetFileExtension(spritesheet.image_path.c_str()), asset.data, (int)asset.size);

		TraceLog(LOG_INFO, "before texture");
		spritesheet.image = LoadTextureFromImage(img);
		TraceLog(LOG_INFO, "after texture");

		UnloadImage(img);
	}

	player_sprite_sheet_name = "sprite.toml";

	// Main game loop

	RenderTexture2D target = LoadRenderTexture(WINDOW_WIDTH, WINDOW_HEIGHT);

	while (!WindowShouldClose()) {
		BeginDrawing();

		BeginTextureMode(target);

		if (zip_loaded) {
			process();
		} else {
			DrawText("Game data is not found!", (WINDOW_WIDTH / 2) - (MeasureText("Game data is not found!", 40) / 2), 100, 40, RED);
			DrawText("Please check if \"data.arpg\" exist", (WINDOW_WIDTH / 2) - (MeasureText("Please check if \"data.arpg\" exist", 30) / 2), 150,
				 30, RED);
		}

		ClearBackground(BLACK);
		EndTextureMode();

		ClearBackground(BLACK);

		float scale	 = std::min((float)GetScreenWidth() / WINDOW_WIDTH, (float)GetScreenHeight() / WINDOW_HEIGHT);
		int scaledWidth	 = (int)(WINDOW_WIDTH * scale);
		int scaledHeight = (int)(WINDOW_HEIGHT * scale);
		int offsetX	 = (GetScreenWidth() - scaledWidth) / 2;
		int offsetY	 = (GetScreenHeight() - scaledHeight) / 2;

		DrawTexturePro(target.texture, Rectangle{0, 0, (float)WINDOW_WIDTH, -(float)WINDOW_HEIGHT},
			       Rectangle{(float)offsetX, (float)offsetY, (float)scaledWidth, (float)scaledHeight}, Vector2{0, 0}, 0.0f, WHITE);

		if (IsKeyPressed(KEY_GRAVE)) {
			DEBUG_MODE = !DEBUG_MODE;
		}

		if (DEBUG_MODE) {
			DrawText("Arpg Engine by Arshavir Mirzakhani - MIT Licenced", 5, 1, 20, PINK);

			DrawText("Arpg Engine version : ", 5, 21, 20, PINK);
			DrawText(("FPS : " + std::to_string(GetFPS())).c_str(), 5, 41, 20, PINK);
			DrawText(("FrameTime (DeltaTime) : " + std::to_string(GetFrameTime())).c_str(), 5, 61, 20, PINK);
			DrawText(("Monitor refresh rate : " + std::to_string(GetMonitorRefreshRate(GetCurrentMonitor()))).c_str(), 5, 81, 20, PINK);
		}

		EndDrawing();
	}

	UnloadRenderTexture(target);
	CloseWindow();

	return 0;
}
