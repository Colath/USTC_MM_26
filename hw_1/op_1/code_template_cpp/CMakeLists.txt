cmake_minimum_required(VERSION 3.15)
project(op1_seam_carving CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

add_executable(op1_template main.cpp)
target_link_libraries(op1_template PRIVATE ${OpenCV_LIBS})
