# CMakeLists.txt for the 'mes' extension

message(STATUS "Configuring mes module")

# Define the Python module target
# It automatically uses pybind11 includes from the parent scope
pybind11_add_module(mes SHARED mes.cpp)

# Link Python library (inherited target from parent's find_package)
target_link_libraries(mes PRIVATE Python::Python)

# Add any specific include directories or link libraries for ONLY the mes module here
# target_include_directories(mes PRIVATE ...)
# target_link_libraries(mes PRIVATE ...)

# Installation instructions for the module if needed (scikit-build-core usually handles this)
# install(TARGETS mes LIBRARY DESTINATION muoblpsolvers) # Adjust destination
