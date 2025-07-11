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

	struct zip_t* zip = zip_open("data.arpg", 0, 'r');
	{
		zip_entry_open(zip, "project.toml"); // read project data
		{
			bufsize = zip_entry_size(zip);
			buf	= (unsigned char*)calloc(sizeof(unsigned char), bufsize);

			zip_entry_noallocread(zip, (void*)buf, bufsize);

			std::string_view string = (const char*)buf;
			toml::table tbl		= toml::parse(string);

			auto title   = tbl.get("window_title")->value<std::string>();
			WINDOW_TITLE = *title;
		}
		zip_entry_close(zip);

		int i, n = zip_entries_total(zip);
		for (i = 0; i < n; ++i) {
			zip_entry_openbyindex(zip, i);
			{
				if (!zip_entry_isdir(zip)) {
					if (std::string(zip_entry_name(zip)).find("spritesheets/") != std::string::npos &&
					    std::string(zip_entry_name(zip)).find("spritesheets/") == 0) {
						bufsize = zip_entry_size(zip);
						buf	= (unsigned char*)calloc(sizeof(unsigned char), bufsize);

						zip_entry_noallocread(zip, (void*)buf, bufsize);

						std::string_view string = (const char*)buf;
						toml::table tbl		= toml::parse(string);

						auto image  = tbl.get("image_path")->value<std::string>();
						auto width  = tbl.get("width")->value<toml::int32_t>();
						auto height = tbl.get("height")->value<toml::int32_t>();
					}
				}
			}
			zip_entry_close(zip);
		}
		zip_close(zip);

		free(buf);
	}

	// Initialize game

	// Initialize window
	SetTraceLogLevel(LOG_WARNING);
	SetConfigFlags(FLAG_WINDOW_RESIZABLE);
	InitWindow(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE.c_str());
	InitAudioDevice();
	SetTargetFPS(60);

	// Main game loop

	RenderTexture2D target = LoadRenderTexture(WINDOW_WIDTH, WINDOW_HEIGHT);

	while (!WindowShouldClose()) {

		BeginDrawing();

		BeginTextureMode(target);

		process();

		ClearBackground(GREEN);
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
