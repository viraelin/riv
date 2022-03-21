# RIV
`riv` is a Reference Image Viewer. A canvas for viewing images. Cross-platform with Python and Qt.


## Features
- Modifications are non-destructive. `riv` simply displays images.
- Add images with drag and drop from anywhere, or import manually.
- Pan/Zoom
- Toggle color/grayscale
- Flip images
- Resize images
- Save/Load projects
- Simple rectangle packing
- Export selection to directory
- Window opacity adjustment
- Always on top and ignore mouse toggles
- Minimal user interface


## Usage
- Drag and drop images onto canvas
- Select and move items with mouse
- Pan with spacebar and left click, or middle click
- Zoom with mouse wheel
- Right click to access action menu
- Resize item(s) by holding CTRL and left click
- When using ignore mouse, a small button is created in the top right of the display to enable mouse again.


## Data
Data is stored in a single uncompressed zip file. This has the benefit of being portable with no increase in image filesize and no performance overhead reading and writing.


## Known Issues
- Remaining in resize state when coming out of a menu.


## Dependencies
- Python 3.6+
- PyQt6

For modules, see `requirements.txt`.


## License
[GPLv3](https://choosealicense.com/licenses/gpl-3.0/)
