# RIV
`riv` is a Reference Image Viewer. A canvas for placing, manipulating, and viewing images.

Open source, minimal, and cross-platform using C++ and Qt.




## Features
- Modifications are non-destructive. RIV simply displays images.
- Add images via drag and drop, from the web, file browser, or import manually
- Pan/Zoom
- Toggle color/grayscale
- Flip images
- Resize images
- Save/Load projects
- Simple row packing of selection


## Data
Data is stored in a single file with images embedded. This comes at a speed and file size penalty when saving but is portable and easier to manage compared to using absolute/relative file paths and directory structures.


## Usage
- Drag and drop images onto canvas
- Select and move items with mouse
- Pan with spacebar + left click or middle click
- Zoom with mouse wheel
- Right click to bring up menu
- Resize item(s) by holding CTRL + left click


## Known Issues
- Incorrect placement on packing/drag and drop
- Remaining in resize state when coming out of menu. Fix with ESC.


## Compiling from source
### Dependencies
- Qt 6
- CMake


### Linux


cd riv
mkdir -p build-release
cd build-release
cmake ..
make



## License
[GPLv3](https://choosealicense.com/licenses/gpl-3.0/)

