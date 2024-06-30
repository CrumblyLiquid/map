from typing import List, Self
from math import ceil

# Selenium
# On Arch: python-selenium and geckodriver packages are required
from selenium.webdriver import Firefox, FirefoxService
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# TODO:
# - Detect swapped east/west or south/north bounds
# - Choose output name/folder

class Position:
    x: float
    y: float
    z: int

    def __init__(self, x: float = 15.0, y: float = 50.0, z: int = 16):
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
    driver: str = "/usr/bin/geckodriver"

    def __init__(self, browser: WebDriver | None = None):
        if browser is None:
            service: FirefoxService = FirefoxService(executable_path=self.driver)
            self.browser = Firefox(service=service)
        else:
            self.browser = browser

    def get_position(
            self,
            message: str,
            capture: str,
            starting_pos: Position | None = None
        ) -> Position:
        if starting_pos is not None:
            self.browser.get(self.pos_to_url(starting_pos))

        print(message)
        input(f"Press Enter to {capture}...")

        captured: Position = self.url_to_pos(self.browser.current_url)
        print("Captured: " + str(captured))

        return captured

    def pos_to_url(self, pos: Position) -> str:
        raise NotImplementedError

    def url_to_pos(self, url: str) -> Position:
        raise NotImplementedError

class MapyCZ(Website):
    def pos_to_url(self, pos: Position) -> str:
        return f"https://mapy.cz/turisticka?l=0&x={pos.x}&y={pos.y}&z={pos.z}"

    def url_to_pos(self, url: str) -> Position:
        pos: Position = Position()
        params: List[str] = url.split("?")[1].split("&")

        for param in params:
            (key, val) = param.split("=")
            try:
                match key:
                    case "x":
                        pos.x = float(val)
                    case "y":
                        pos.y = float(val)
                    case "z":
                        pos.z = int(val)
            except ValueError:
                print(f"Failed to parse parameter {key}.")

        return pos


class MapBuilder:
    website: Website

    # Top-left position
    start: Position
    width: float
    height: float

    u_shift: float
    r_shift: float

    def __init__(self,
                 website: Website,
                 start: Position,
                 width: float,
                 height: float,
                 u_shift: float,
                 r_shift: float,
                ):
        self.website = website
        self.start = start
        self.width = width
        self.height = height
        self.u_shift = u_shift
        self.r_shift = r_shift

    def from_area(website: Website) -> Self:
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

        # TODO: Verify correct right/up shift signs
        right_shift: float = right_shift_pos.x - start_pos.x
        up_shift: float = up_shift_pos.y - start_pos.y
        print(f"Using right shift of {right_shift} and up shift of {up_shift}")

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

        # TODO: Fix start_pos to be top-left point
        return MapBuilder(website, start_pos, width.x, height.y, up_shift, right_shift)


    # Takes frames via Selenium webdriver and stores them with the appropriate name
    # at the appropriate place
    def take_frames(self) -> list[str]:
        # TODO: Temporary folder
        frames: list[str] = []
        return frames

    def take_frame(self, pos: Position, id: int) -> str:
        filename: str = f"frame-{id}.png"

        # Take a frame
        # TODO: Screenshot or save picture via website
        # Screenshot is website agnostic
        # Any downsides to screenshot vs site specific download?

        self.browser.get(pos.to_url())
        # TODO: Does this work?
        self.browser.save_screenshot(filename)

        return filename

    # Assembles frames into one picture
    def assemble(pictures: list[str]) -> str:
        return "map.png"

    def build(self):
        print("Taking frames ...")
        pictures: list[str] = self.take_frames()
        print("Assembling frames into a map ...")
        result: str = self.assemble()
        print(f"Final map: {result}")

    def close(self):
        self.browser.close()
        self.browser.quit()

if __name__ == "__main__":
    website: Website = MapyCZ()
    builder: MapBuilder = MapBuilder.from_area(website)
    builder.build()
    builder.close()

