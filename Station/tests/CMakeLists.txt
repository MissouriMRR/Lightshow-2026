find_package(Catch2 3 REQUIRED)
add_executable(tests)

target_link_libraries(tests
    PRIVATE
        Catch2::Catch2WithMain
    PUBLIC
        freetype 
        assimp 
        glfw 
        GL 
        m 
        X11 
        pthread 
        Xi 
        Xrandr 
        dl 
        z 
        bz2 
        png 
        brotlidec
)

target_sources(tests
    PRIVATE
        droneSelect.cpp
)

target_link_libraries(tests PRIVATE source_lib)
target_include_directories(tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/..")

add_custom_command(
    TARGET tests
    POST_BUILD
    COMMAND tests
    VERBATIM
)
