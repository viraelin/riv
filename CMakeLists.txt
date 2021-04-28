cmake_minimum_required(VERSION 3.16.0)

project(riv VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 COMPONENTS Widgets REQUIRED)
find_package(Qt6 COMPONENTS Network REQUIRED)

file(GLOB_RECURSE sources src/*.cpp src/*.h)
add_executable(riv ${sources})

target_link_libraries(riv PRIVATE Qt6::Widgets PRIVATE Qt6::Network)
