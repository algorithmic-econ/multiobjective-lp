# Top-level CMakeLists.txt
cmake_minimum_required(VERSION 3.15)
project(muoblpsolver_bindings LANGUAGES CXX)

message(STATUS "Configuring main bindings project for System: ${CMAKE_SYSTEM_NAME} (${CMAKE_SYSTEM_PROCESSOR})")

# --- Find TARGET Python ---
# Respect PYTHON_EXECUTABLE passed from scikit-build-core
if(DEFINED PYTHON_EXECUTABLE)
  message("Setting Python3_EXECUTABLE ${PYTHON_EXECUTABLE}")
  set(Python3_EXECUTABLE "${PYTHON_EXECUTABLE}")
endif()

#find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
#message(STATUS "Found Target Python: ${Python_EXECUTABLE}")

# --- Find TARGET Pybind11 ---
# Make pybind11 use the Python found above
set(PYBIND11_PYTHON_EXECUTABLE ${Python_EXECUTABLE})
find_package(pybind11 CONFIG REQUIRED)
message(STATUS "Found Target pybind11 includes: ${pybind11_INCLUDE_DIRS}")

# Include pybind11 headers globally for subprojects
include_directories(${pybind11_INCLUDE_DIRS})

# --- Add Subdirectories for Each Extension ---
# CMake will look for CMakeLists.txt inside these directories
add_subdirectory(mes)
add_subdirectory(mes_add1)
