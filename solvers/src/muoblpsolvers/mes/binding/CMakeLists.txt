cmake_minimum_required(VERSION 3.30)
project(mes)

find_package(pybind11 REQUIRED)
set(CMAKE_CXX_STANDARD 11)
set (PYBIND11_PYTHON_VERSION "3.11")
set(PYBIND11_FINDPYTHON ON)
SET(CMAKE_CXX_FLAGS "-Ofast")
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(mes mes.cpp)
