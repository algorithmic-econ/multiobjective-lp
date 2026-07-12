cmake_minimum_required(VERSION 3.15...3.27)

project(
  ${SKBUILD_PROJECT_NAME}
  VERSION ${SKBUILD_PROJECT_VERSION}
  LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(methods STATIC
  src/common.cpp
  src/mes_add1.cpp
  src/mes_utils.cpp
  src/expanding_approvals.cpp
  src/single_transferable_vote.cpp
  src/solid_coalition_refinement.cpp)
set_target_properties(methods PROPERTIES POSITION_INDEPENDENT_CODE ON)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

include_directories(${pybind11_INCLUDE_DIRS})

python_add_library(muoblpbindings MODULE src/binder.cpp WITH_SOABI)
target_link_libraries(muoblpbindings PRIVATE pybind11::headers)
target_link_libraries(muoblpbindings PRIVATE methods)

target_compile_definitions(muoblpbindings PRIVATE VERSION_INFO=${PROJECT_VERSION})

install(TARGETS muoblpbindings DESTINATION muoblpbindings)
