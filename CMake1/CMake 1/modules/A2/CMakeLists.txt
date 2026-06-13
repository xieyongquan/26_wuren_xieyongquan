add_library(A2 src/A2.cpp)

target_include_directories(A2 PUBLIC include)

target_compile_options(A2 PRIVATE -include cstddef)

