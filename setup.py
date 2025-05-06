# C:\nmdose\setup.py

from setuptools import setup, find_packages

setup(
    name="nmdose",
    version="0.1.0",
    description="NMDOSE DICOM retrieval and processing toolkit",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "PyYAML",
        # 필요한 라이브러리를 여기에 추가하세요
    ],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "nmdose = nmdose.main:cli",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
