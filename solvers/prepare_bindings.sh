echo "Prepare C++ bindings"
START_DIR=$PWD

rm -rf solvers/mes/binding/build
mkdir solvers/mes/binding/build
cd solvers/mes/binding/build
cmake ..
make

cd $START_DIR

rm -rf solvers/mes_add1/binding/build
mkdir solvers/mes_add1/binding/build
cd solvers/mes_add1/binding/build
cmake ..
make
