from typing import List, Self, override
from abc import abstractmethod
from pathlib import Path
import time
import glob
import os

from mpmath import mpf, ceil
from PIL import Image as Img
from PIL.Image import Image

# Selenium
# On Arch: python-selenium and geckodriver packages are required
from selenium.webdriver import Firefox, FirefoxService
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# TODO:
# - Detect swapped east/west or south/north bounds
# - Choose output name/folder

class Position:
    x: mpf
    y: mpf
    z: int

    def __init__(self, x: mpf = mpf('15.0'), y: mpf = mpf('50.0'), z: int = 16):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y, self.z)

    def __sub__(self, other):
        return Position(self.x - other.x, self.y - other.y, self.z)

    def __neg__(self):
        return Position(self.x, self.y, self.z)

    def __str__(self) -> str:
        return f"Position (x = {self.x}, y = {self.y}, z = {self.z})"

class Website:
    browser: WebDriver

    # Default WebDriver executable path
    # driver: str = "/usr/bin/geckodriver"
    # NixOS WebDriver executable path
    driver: str = "/run/current-system/sw/bin/geckodriver"

    def __init__(self, browser: WebDriver | None = None):
        if browser is None:
            service: FirefoxService = FirefoxService(executable_path=self.driver)
            self.browser = Firefox(service=service)
        else:
            self.browser = browser

    def close(self):
        self.browser.close()

    def set_position(self, pos: Position):
        '''
        Load a map with the specified Position
        '''
        self.browser.get(self.pos_to_url(pos))

    def get_position(
            self,
            message: str,
            capture: str,
            starting_pos: Position | None = None
        ) -> Position:
        '''
        Display a map and let the user choose
        a location, then read the location from the URL
        '''
        if starting_pos is not None:
            self.set_position(starting_pos)

        self.prepare_position()
        print(message)
        input(f"Press Enter to {capture}...")

        captured: Position = self.url_to_pos(self.browser.current_url)
        print("Captured: " + str(captured))

        return captured

    @abstractmethod
    def prepare_position(self):
        '''
        Prepares the website such that the user
        can select a position (for the `get_position` fucntion)

        For example add a cursor or a zoom box
        '''
        raise NotImplementedError()

    @abstractmethod
    def prepare_screenshot(self):
        '''
        Prepares the page for screenshot
        (e.g. remove UI elements, etc.)
        '''
        raise NotImplementedError()

    def save_screenshot(self, name: Path):
        '''
        Save a screenshot of the bare map
        to a specified location
        '''
        try:
            WebDriverWait(
                    self.browser,
                    100
            ).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.tiles')))
            print("Page loaded...")
        except TimeoutException:
            time.sleep(2)
            print("Loading took too much time!")

        self.prepare_screenshot()
        self.browser.save_screenshot(name)

    @abstractmethod
    def pos_to_url(self, pos: Position) -> str:
        '''
        Return a URL corresponding to the given Position
        '''
        raise NotImplementedError()

    @abstractmethod
    def url_to_pos(self, url: str) -> Position:
        '''
        Extract the Position from the given URL
        '''
        raise NotImplementedError()

class MapyCZ(Website):
    def hide_ui(self):
        '''
        Hide the UI elements of the website
        '''

        ui_script = f'''\
            // Hide UI elements
            let controls = document.getElementById('all-controls');
            controls.style.display = 'none';

            // Mobile UI - still TODO change map class from smap to map
            let block_map = document.getElementById('block-map');
            block_map.style.display = 'none';

            let layout_content = document.getElementById('layout-content');
            layout_content.style.display = 'none';
        '''

        self.browser.execute_script(ui_script)

    def hide_paid_poi(self):
        '''
        Hides the paid popup POIs that are
        just annoying >:(
        '''

        script = '''
            document.styleSheets[0].insertRule(".type-paid {display: none !important;}", 0 )
            '''
        self.browser.execute_script(script)

    def add_crosshair(self):
        '''
        Add a crosshair to the center of the screen
        to make alignment easier
        '''

        crosshair_path = os.path.dirname(__file__) + '/crosshair.html' 
        with open(crosshair_path) as file:
            crosshair = file.read().replace('\n', ' ')

        crosshair_script = f'''\
            // Remove UI elements
            let controls = document.getElementById('all-controls');
            controls.style.display = 'none';

            // Add crosshair
            let scene = document.getElementById('scene');
            let crosshair = document.createElement('div');
            crosshair.innerHTML=`%s`
            scene.appendChild(crosshair)
        ''' % crosshair

        self.browser.execute_script(crosshair_script)


    @override
    def prepare_position(self):
        '''
        Prepare the website for selecting a position
        '''

        # TODO: Maybe implement a zoom box?
        self.hide_ui()
        self.hide_paid_poi()
        self.add_crosshair()


    @override
    def prepare_screenshot(self):
        '''
        Prepare the website for taking a screenshot
        '''

        # TODO: Maybe hide certain icons?
        self.hide_ui()
        self.hide_paid_poi()

    @override
    def pos_to_url(self, pos: Position) -> str:
        '''
        Convert a Position to the corresponding website URL
        '''
        return f"https://mapy.cz/turisticka?l=0&x={pos.x}&y={pos.y}&z={pos.z}"

    @override
    def url_to_pos(self, url: str) -> Position:
        '''
        Extract a Position from the Website URL
        '''
        pos: Position = Position()
        params: List[str] = url.split("?")[1].split("&")

        for param in params:
            (key, val) = param.split("=")
            try:
                match key:
                    case "x":
                        pos.x = mpf(val)
                    case "y":
                        pos.y = mpf(val)
                    case "z":
                        pos.z = int(val)
            except ValueError:
                print(f"Failed to parse parameter {key}.")

        return pos


class MapBuilder:
    website: Website

    # Top-left position
    start: Position
    width: mpf
    height: mpf

    u_shift: mpf
    r_shift: mpf

    def __init__(self,
                 website: Website,
                 start: Position,
                 width: mpf,
                 height: mpf,
                 u_shift: mpf,
                 r_shift: mpf,
                ):
        self.website = website
        self.start = start
        self.width = width
        self.height = height
        self.u_shift = u_shift
        self.r_shift = r_shift

    @staticmethod
    def get_shift(website: Website) -> tuple[Position, mpf, mpf]:
        '''
        Get the starting position and the up/right shift to use
        between frames
        '''

        # First capture the starting position
        # (the centre of the map)
        start_pos: Position = website.get_position(
            "Get to your desired start location and set your zoom level.",
            "start measuring",
            Position()
        )

        # Get the shift amount between frames
        # the shift such that the frames overlap only by a little
        #
        # This is something
        message: str = "Move {} until only a small part of the area overlaps"
        capture: str = "{} shift"

        direction: str = "right"
        right_shift_pos: Position = website.get_position(
            message.format(direction),
            capture.format(direction),
            start_pos
        )

        direction: str = "up"
        up_shift_pos: Position = website.get_position(
            message.format(direction),
            capture.format(direction),
            start_pos
        )

        right_shift: mpf = right_shift_pos.x - start_pos.x
        up_shift: mpf = up_shift_pos.y - start_pos.y

        # Both should be positive
        assert right_shift > 0
        assert up_shift > 0

        print(f"Using right shift of {right_shift} and up shift of {up_shift}")

        return (start_pos, right_shift, up_shift)

    @classmethod
    def from_box(cls, website: Website) -> Self:
        (start_pos, right_shift, up_shift) = cls.get_shift(website)

        message = "Go to the most {} point of your map"
        capture = "capture the {} corner"

        corner = "top-left"
        top_left_pos: Position = website.get_position(
            message.format(corner),
            capture.format(corner),
            start_pos
        )
        # Set zoom level to be the same as start_pos
        # for taking screenshots later
        top_left_pos.z = start_pos.z

        corner = "down-right"
        down_right_pos: Position = website.get_position(
            message.format(corner),
            capture.format(corner),
        )

        width: mpf = (down_right_pos.x - top_left_pos.x) / right_shift
        height: mpf = (top_left_pos.y - down_right_pos.y) / up_shift
        print(f"Width: {width} (({down_right_pos.x} - {top_left_pos.x}) / {right_shift}), Height: {height} (({top_left_pos.y} - {down_right_pos.y}) / {up_shift})") 

        assert width > 0
        assert height > 0

        return cls(website, top_left_pos, height, width, up_shift, right_shift)

    @classmethod
    def from_center(cls, website: Website) -> Self:
        # TODO: Fix start_pos in Self constructor to be top-left point
        print("Warning: This method is broken!")

        (start_pos, right_shift, up_shift) = cls.get_shift(website)

        move: str = "Move as {} as you want the map to go."
        boundary: str = "the {} boundary"

        direction: str = "north"
        north_pos: Position = website.get_position(
            move.format(direction),
            boundary.format(direction),
            start_pos
        )

        direction: str = "south"
        south_pos: Position = website.get_position(
            move.format(direction),
            boundary.format(direction),
            start_pos
        )

        direction: str = "east"
        east_pos: Position = website.get_position(
            move.format(direction),
            boundary.format(direction),
            start_pos
        )

        direction: str = "west"
        west_pos: Position = website.get_position(
            move.format(direction),
            boundary.format(direction),
            start_pos
        )

        width: Position = east_pos - west_pos
        print(f"Width: {width}")

        height: Position = north_pos - south_pos
        print(f"Height: {height}")

        return cls(website, start_pos, width.x, height.y, up_shift, right_shift)

    def take_frames(self, folder: Path) -> list[list[str]]:
        '''
        Takes individual frames and stores them with the appropriate name
        to the requested folder

        Also gives the option to retake any imperfect frames
        '''
        frames: list[list[str]] = []

        y: mpf = 0
        while(y < ceil(self.height)):
            if len(frames) <= y:
                frames.append([])

            x: mpf = 0
            while(x < ceil(self.width)):
                frames[y].append(self.take_frame(x, y, folder))
                x += 1

            y += 1

        while True:
            again = input("Do you want to retake any frames? ").lower()
            if again == 'n':
                break

            retakes = [ s.split(',') for s in input("What do you want to retake?\nExample (y,x): 1,3;2,3\n").split(';') ]
            frames = [ [ int(n) for n in retake ] for retake in retakes ]

            print("Reshooting frames: ", frames)
            for frame in frames:
                self.take_frame(frame[1], frame[0], folder)

        return frames

    def take_frame(self, x: int, y: int, folder: Path) -> Path:
        '''
        Take a specified frame
        '''
        print(f"Taking frame {x}, {y}")
        pos: Position = Position(self.start.x + x * self.r_shift,
                                 self.start.y - y * self.u_shift,
                                 self.start.z)
        name: str = f"frame-{y}-{x}.png"
        path: Path = folder / name

        # Take a frame
        self.website.set_position(pos)
        time.sleep(1)
        self.website.save_screenshot(path)

        return path

    def assemble(self, pictures: list[list[str]], name: Path):
        '''
        Assemble frames into one picture
        '''
        assert len(pictures) > 0 and len(pictures[0]) > 0

        x_offset = 0
        y_offset = 0

        height = len(pictures)
        width = len(pictures[0])
        (fwidth, fheight) = Img.open(pictures[0][0]).size

        # TODO: Do this automatically
        while True:
            adj = input(f"Adjustment ({x_offset}, {y_offset}): ")
            (x_offset, y_offset) = [ int(i) for i in adj.split(',') ] if adj else (0,0)

            # Create blank image that can fit all the tiles
            # + account for offsets
            full_img: Image = Img.new("RGB", (width * fwidth - x_offset * width, height * fheight - y_offset * height))
            for (y, row) in enumerate(pictures):
                for (x, pic) in enumerate(row):
                    img = Img.open(pic)
                    img.convert("RGB")
                    print(f"Row: {full_img.width}, {full_img.height}, Img: {img.width}, {img.height}")
                    full_img.paste(img, (x * fwidth - x_offset * x, y * fheight - y_offset * y))

            # Show a preview
            full_img.show()

            # TODO: Adjusting on only 3-5 sample images
            cont = input("Do you want to adjust?").lower()
            if cont == 'n':
                full_img.save(name)
                break

    def build(self):
        # TODO: Temporary folder
        tmp_folder = "map_tmp"
        tmp_path = Path(f"./{tmp_folder}")

        files = []
        if os.path.exists(tmp_path):
            files = glob.glob(f"./{tmp_folder}/*")
        else:
            os.mkdir(tmp_path)

        if len(files):
            print("Exsiting files: ", files)
        else:
            print("No existing files")

        pictures: list[list[str]] = []

        reuse = input("Do you want to reuse previous screenshots? ").lower()
        if reuse != 'n':
            # Reuse pictures
            for file in files:
                name: str = os.path.basename(file)
                # Remove filetype
                name = name.split('.')[0]
                (frame,y,x) = name.split('-')
                x = int(x)
                y = int(y)

                # Extend the list far enough
                # (file names might be out of order)
                while len(pictures) <= y:
                    pictures.append([])

                while len(pictures[y]) <= x:
                    pictures[y].append('')

                pictures[y][x] = file

        else:
            for file in files:
                os.remove(file)
            print("Removed existing files in temp. folder")

            input("Start taking frames in 3 seconds?")
            time.sleep(3)

            print("Taking frames ...")
            pictures = self.take_frames(tmp_path)

        print("Assembling frames into a map ...")
        name: Path = Path("map.png")
        self.assemble(pictures, name)

        print(f"Final map: {name}")

    def close(self):
        self.website.close()

if __name__ == "__main__":
    website: Website = MapyCZ()
    builder: MapBuilder = MapBuilder.from_box(website)

    # Default
    # builder: MapBuilder = MapBuilder(website,
    #                                  Position(15, 50, 16),
    #                                  mpf('2.428566307326'),
    #                                  mpf('2.40825490636835'),
    #                                  mpf('0.0124532000000031'),
    #                                  mpf('0.0195264999999996')
    #                                  )

    # Test with zoom 16
    # 18,15
    # builder: MapBuilder = MapBuilder(website,
    #                                  Position(mpf('15.6491'), mpf('49.7036793'), 16),
    #                                  mpf('5.0'), # width
    #                                  mpf('9.0'), # height
    #                                  mpf('0.0177041'), # u_shift
    #                                  mpf('0.054245') # r_shift
    #                                  )

    # Test with zoom 15
    # 25,30
    # builder: MapBuilder = MapBuilder(website,
    #                                  Position(mpf('15.6491'), mpf('49.7036793'), 15),
    #                                  mpf('3.0'), # width
    #                                  mpf('5.0'), # height
    #                                  mpf('0.0349381'), # u_shift
    #                                  mpf('0.1082325') # r_shift
    #                                  )

    builder.build()
    builder.close()
