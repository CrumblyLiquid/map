# Map
Collection of scripts to create custom maps out of map screenshots

## Requirements
- [Python 3.12](https://www.python.org/downloads)
- [Firefox](https://www.mozilla.org/en-US/firefox/new)
- [GeckoDriver](https://github.com/mozilla/geckodriver)
- [Pillow](https://pypi.org/project/pillow/)
- [mpmath](https://mpmath.org/)

## Usage
Make sure that the DRIVER variable (at the top of `map.py`)
is pointing to the location of the GeckoDriver executable

Run the script: `python map.py`

## How does it work?
I'm using [Mapy.cz](https://mapy.cz) as a source of screenshots which are
then stitched together into a composite.

### Mapy.cz
As far as I know [Mapy.cz](https://mapy.cz) have only a couple
of URL parameters:
- l = 0/1 (open sidebar)
- lgnd = anything? (show legend in sidebar - open or closed)
- x = longitude
- y = latitude
- z = 2 - 19 (zoom level)
