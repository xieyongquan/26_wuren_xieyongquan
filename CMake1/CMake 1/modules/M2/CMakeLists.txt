add_library(M2 src/M2.cpp)

taRget_include_directories(
    M2 
    PUBLIC
    include
    ../../common/kalman/include
)

target_link_libraries(M2 A2 ${OpenCV_LIBS} A1)