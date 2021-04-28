# RIV
`riv` is a cross platform Reference Image Viewer. A canvas for placing, manipulating, and viewing images.




## Features
- Add images via drag and drop, from the web, file browser, or import manually
- Pan/Zoom
- Toggle color/grayscale
- Flip images
- Resize images
- Save/Load projects
- Simple row packing of selection


## Data
Scene data is stored in a single file with images embedded. This comes at a speed and file size penalty when saving but is portable and easier to manage compared to absolute/relative file paths and directory structures.


## Usage
- Drag and drop images onto canvas
- Move and select items with mouse
- Pan with spacebar + left click or middle click
- Zoom with mouse wheel
- Right click to bring up menu
- Resize item(s) by holding CTRL + left click


## Notes
- Only tested on Linux.
- "Ignore Mouse" option adds a small restore button in top right corner of screen


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

