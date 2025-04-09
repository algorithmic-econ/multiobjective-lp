# CMakeLists.txt for the 'mes_add1' extension

message(STATUS "Configuring mes_add1 module")

# Define the Python module target
pybind11_add_module(mes_add1 SHARED mes_add1.cpp) # Use the correct source file name

# Link Python library
#target_link_libraries(mes_add1 PRIVATE Python::Python)

# Add any specific include directories or link libraries for ONLY the mes_add1 module here
# target_include_directories(mes_add1 PRIVATE ...)
# target_link_libraries(mes_add1 PRIVATE ...)

# Installation instructions for the module if needed
# install(TARGETS mes_add1 LIBRARY DESTINATION muoblpsolvers) # Adjust destination
