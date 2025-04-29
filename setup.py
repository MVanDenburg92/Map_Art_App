from setuptools import setup, find_packages

setup(
    name="map_art_app",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.13",
    install_requires=[
        "streamlit>=1.30.0",
        "streamlit-folium>=0.15.0",
        "folium>=0.14.0",
        "osmnx>=1.6.0",
        "matplotlib>=3.8.0",
        "numpy>=1.26.0",
    ],
    author="Miles Van Denburg",
    author_email="miles.vandenburg@gmail.com",
    description="A Streamlit app for creating map art",
    keywords="streamlit, maps, art, visualization, osmnx",
    url="https://github.com/yourusername/map_art_app",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.13",
        "Topic :: Artistic Software",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
)