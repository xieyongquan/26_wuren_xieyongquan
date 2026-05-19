cmake_minimum_required(VERSION 3.10)

project(test)

find_package(OpenCV REQUIRED)


add_subdirectory(common)
add_subdirectory(modules)

add_executable(test main.cpp)

target_link_libraries(test
    M1
    M2
    math
    A1
    A2
)

target_include_directories(
    test
    PUBLIC
    ./common/kalman/include
    ./common/math/include
    ./modules/A1/include
    ./modules/A2/include
    ./modules/M1/include
    ./modules/M2/include
    ${OpenCV_INCLUDE_DIRS}
)