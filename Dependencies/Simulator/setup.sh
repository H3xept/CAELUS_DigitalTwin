if [ ! -d "build" ] 
then
    mkdir "build"
fi

cd build
cmake ..
cmake --install .
make