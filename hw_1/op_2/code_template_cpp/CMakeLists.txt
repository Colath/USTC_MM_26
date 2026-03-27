cmake_minimum_required(VERSION 3.15)
project(op2_metro_template CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

add_executable(op2_template
    main.cpp
    metro_algorithm.cpp
    metro_gui.cpp
)
target_link_libraries(op2_template PRIVATE ${OpenCV_LIBS})
