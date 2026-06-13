aux_source_directory(src a1_src) 

add_library(A1 ${a1_src})

target_include_directories(A1 PUBLIC include)

