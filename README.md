# Rover Code

This is a main repo for communication & intelligence team. There are three sub-folders.

<ul>
    <li> <b>components</b>: This folder is for individual parts, components, or experiments
    <li> <b>src</b>: This folder contains the code that will be running on the rover. It is ROS2 workspace. 
    <li> <b>tutorial</b>: A trining module for new members.
</ul>

## Setup

The folder [src](./src/) is the main folder to work with.
This ROS working space is tested on ROS Humble on Ubuntu 22.04 LTS.
Installation guide can be found in [tutorial](./tutorial/)
To run the code, you will need to compile and install.

### Python Virtual Environment

If you use Python virtual environment, you will need to create the virtual environment using extra option as below

```bash
python3 -m venv .venv --system-site-packages
```

### To compile

```bash
colcon build
```

Note: You might need to install colcon by

```bash
sudo apt install python3-colcon-common-extensions
```

You can selectively build packages by

```bash
colcon build --packages-select <name-of-pkg>
```

After compilation, you will see a folder `install` appear.
You can install packages by

```bash
source install/setup.bash
```

Note: You could use `symlink-install` along with `colcon build` to avoid building and installing every time you make changes on the code.
However, this only works with Python packages.

```bash
colcon build --symlink-install
```

Note2: If you use virtual environment, you should use the following command to compile the code.

```bash
python -m colcon build
```

## Dependencies

Some packages have dependencies.
We use `rosdep` to manage them.

```bash
# run the following code only once
sudo apt-get install python3-rosdep
sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src --rosdistro humble --os=ubuntu:jammy
```

All dependencies should be mentioned in each package's `package.xml` whenever possible. Use the following command for install dependencies.

```bash
# run this command from ROS workspace
rosdep install --from-paths src -y --ignore-src
```

Use the following list and this [tutorial](https://docs.ros.org/en/humble/Tutorials/Intermediate/Rosdep.html).

- [ROS base](https://github.com/ros/rosdistro/blob/master/rosdep/base.yaml)
- [Python](https://github.com/ros/rosdistro/blob/master/rosdep/python.yaml)

### Automated Setup

Run `source setup.bash` for automatic setup.
This script will take care of building and installing packages from both `brc_msgs` and `rover-code`.

## ODrive

Since we are using legacy ODrive, we need to upgrade firmware and matching Python module with the firmware version.
To upgrade firmware, see [this](./components/odrive/README.md).
If the firmware is >0.5.5 and <0.6.0, there will be no precompiled package available from PyPi.
Therefore, we need to install from source.
First, clone or download the source code from [GitHub](https://github.com/odriverobotics/ODrive/tags).
Next run the following command in `tools` folder.

```bash
python3 setup.py sdist
```

It will compile and generate a package in `dist/odrive-x.y.z.tar.gz`.
Lastly, install it by

```bash
pip install dist/odrive-x.y.z.tar.gz
```
