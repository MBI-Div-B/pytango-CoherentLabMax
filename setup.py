from setuptools import setup, find_packages

setup(
    name="tangods_coherentlabmax",
    version="0.0.1",
    description="Device Server for controlling Coherent LabMax-Top Power and Energy Meter",
    author="Leon Werner",
    author_email="",
    python_requires=">=3.6",
    entry_points={"console_scripts": ["CoherentLabMaxTop = tangods_coherentlabmax:main"]},
    license="MIT",
    packages=["tangods_coherentlabmax"],
    install_requires=[
        "pytango",
        "pyserial",
    ],
    url="https://github.com/MBI-Div-b/pytango-CoherentLabMax",
    keywords=[
        "tango device",
        "tango",
        "pytango",
    ],
)
