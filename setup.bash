#!/bin/bash

# current directory
cwd=$(pwd)

# build packages
echo ' '
echo 'installing packages...'
cd "${cwd}"
colcon build --base-paths src
source install/setup.bash