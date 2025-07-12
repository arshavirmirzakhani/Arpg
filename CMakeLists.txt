cmake_minimum_required(VERSION 3.10)
set(CMAKE_CXX_STANDARD 17)


project(arpg_engine)

file(GLOB_RECURSE SOURCES_ENGINE ${CMAKE_CURRENT_SOURCE_DIR}/engine_bin/*.cpp ${CMAKE_CURRENT_SOURCE_DIR}/vendor/zip/src/*.c)

set(COMMON_INCLUDES
${PROJECT_SOURCE_DIR}/vendor/
${PROJECT_SOURCE_DIR}/vendor/raylib/src
${PROJECT_SOURCE_DIR}/vendor/box2d/include
${PROJECT_SOURCE_DIR}/vendor/sol/
${PROJECT_SOURCE_DIR}/vendor/zip/src
${PROJECT_SOURCE_DIR}/engine_core
)

add_executable(arpg_engine ${SOURCES_ENGINE})

if(CMAKE_BUILD_TYPE STREQUAL "Release")
    if (WIN32)
        if (MSVC)
            target_link_options(arpg_engine PRIVATE /SUBSYSTEM:WINDOWS /ENTRY:mainCRTStartup)
        else()
            target_link_options(arpg_engine PRIVATE -mwindows)
        endif()
    endif()
endif()




target_include_directories(arpg_engine PRIVATE ${COMMON_INCLUDES})


add_subdirectory(vendor/raylib)
add_subdirectory(vendor/zip)
add_subdirectory(vendor/lua)

target_link_libraries(arpg_engine PRIVATE raylib lua_static)


add_compile_options(-Wall -Wextra -Werror)