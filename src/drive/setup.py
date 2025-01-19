from setuptools import find_packages, setup
from glob import glob

package_name = "drive"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            "share/" + package_name + "/odrivelib",
            glob(package_name + "/odrivelib/*.yml"),
        ),
        ("lib/" + package_name, glob(package_name + "/odrivelib/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Tam Bureetes",
    maintainer_email="tbureete@purdue.edu",
    description="Drive controls for the rover.",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": ["diff_drive = drive.diff_drive:main"],
    },
)
