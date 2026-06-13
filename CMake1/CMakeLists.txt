cmake_minimum_required(VERSION 3.10)

project(test)

add_subdirectory(common)
add_subdirectory(modules)

add_executable(server server.cpp)
add_executable(cilent cilent.cpp)

target_link_libraries()
