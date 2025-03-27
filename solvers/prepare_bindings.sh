echo "Prepare C++ bindings"
START_DIR=$PWD

rm -rf src/muoblpsolvers/mes/binding/build
mkdir src/muoblpsolvers/mes/binding/build
cd src/muoblpsolvers/mes/binding/build
cmake ..
make

cd $START_DIR

rm -rf src/muoblpsolvers/mes_add1/binding/build
mkdir src/muoblpsolvers/mes_add1/binding/build
cd src/muoblpsolvers/mes_add1/binding/build
cmake ..
make
