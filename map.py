from typing import List
from math import ceil

DRIVER: str ="/usr/bin/geckodriver"

# Selenium
# On Arch: python-selenium and geckodriver packages are required
from selenium.webdriver import Firefox, FirefoxService
from selenium.webdriver.firefox.webdriver import WebDriver

class Position:
    x: float
    y: float
    z: int

    def __init__(self, x: float = 15.0, y: float = 50.0, z: int = 16):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self) -> str:
        return f"Position: x = {self.x}, y = {self.y}, z = {self.z}"

def get_url(pos: Position):
    return f"https://mapy.cz/turisticka?l=0&x={pos.x}&y={pos.y}&z={pos.z}"

def extract_pos(url: str) -> Position:
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

def get_position(
        webdriver: WebDriver,
        message: str,
        capture: str,
        pos: Position | None = None
    ) -> Position:

    if pos is not None:
        webdriver.get(get_url(pos))

    print(message)
    input(f"Press Enter to {capture}...")

    new_pos: Position = extract_pos(webdriver.current_url)
    print("Captured: " + str(new_pos))

    return new_pos

class Settings:
    start: Position
    u_shift: float
    r_shift: float
    up: int
    down: int
    left: int
    right: int

    def __init__(self,
                 start: Position,
                 u_shift: float,
                 r_shift: float,
                 up: int = 1,
                 down: int = 1,
                 left: int = 1,
                 right: int = 1
                ):
        self.start = start
        self.u_shift = u_shift
        self.r_shift = r_shift
        self.up = up
        self.down = down
        self.right = right
        self.left = left

def get_start() -> Settings:
    service: FirefoxService = FirefoxService(executable_path=DRIVER)
    browser: Firefox = Firefox(service=service)

    start_pos: Position = get_position(
        browser,
        "Get to your desired start location and set your zoom level.",
        "start measuring",
        Position()
    )

    right_pos: Position = get_position(
        browser,
        "Move east until only a small part of the area overlaps",
        "east shift"
    )

    up_pos: Position = get_position(
        browser,
        "Move north until only a small part of the area overlaps",
        "north shift",
        start_pos
    )

    right_shift: float = right_pos.x - start_pos.x
    up_shift: float = up_pos.y - start_pos.y
    print(f"Using east shift of {right_shift} and north shift of {up_shift}")

    move: str = "Move as {} as you want the map to go."
    boundary: str = "the {} boundary"

    direction: str = "north"
    north_pos: Position = get_position(
        browser,
        move.format(direction),
        boundary.format(direction),
        start_pos
    )
    up: int = ceil((start_pos.y - north_pos.y) / up_shift)

    direction = "south"
    south_pos: Position = get_position(
        browser,
        move.format(direction),
        boundary.format(direction),
        start_pos
    )
    down: int = ceil((south_pos.y - start_pos.y) / up_shift)

    direction = "east"
    east_pos: Position = get_position(
        browser,
        move.format(direction),
        boundary.format(direction),
        start_pos
    )
    right: int = ceil((east_pos.x - start_pos.x) / right_shift)

    direction = "west"
    west_pos: Position = get_position(
        browser,
        move.format(direction),
        boundary.format(direction),
        start_pos
    )
    left: int = ceil((start_pos.x - west_pos.x) / right_shift)

    return Settings(start_pos, up_shift, right_shift, up, down, left, right)

# Takes prictures via Selenium webdriver and stores them with the appropriate name
# at the appropriate place
def take_pictures(x: float, y: float, z: int, width: int, height: int) -> list[str]:
    return []

def assemble_pictures() -> str:
    return ""

if __name__ == "__main__":
    settings: Settings = get_start()
