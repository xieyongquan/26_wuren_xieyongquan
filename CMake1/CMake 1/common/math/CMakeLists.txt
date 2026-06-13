add_library(math src/Math.cpp)

target_include_directories(math PUBLIC include)

target_link_libraries(math ${OpenCV_LIBS})