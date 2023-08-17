import os
import re
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from PIL import Image

# Vygenerovat linky pro stažení jednotlivých obrázků
ix = 2.2
iy = 2.2
z = 16

X_STEP = 0.035
Y_STEP = 0.01
DOWNLOAD = "~/Downloads"

size = (4, 6)

def download():
    # x = ix - X_STEP
    x = ix
    first = True
    try:
        browser = webdriver.Firefox()

        for i in range(0, size[0]):
            # y = iy - Y_STEP
            y = iy
            for j in range(0, size[1]):
                url = f"https://mapy.cz/turisticka?l=0&x={x}&y={y}&z={z}"
                # webbrowser.open(url, new=0, autoraise=True)
                browser.get(url)
                if first:
                    first = False
                    input("Continue?")
                delay = 10
                try:
                    time.sleep(5)
                    tools = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CLASS_NAME, "tools")))
                    tools.click()
                    down = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-name=\"picture\"]")))
                    down.click()
                    last = os.listdir(DOWNLOAD)
                    while(1):
                        new = os.listdir(DOWNLOAD)
                        if(last != new):
                            break
                        time.sleep(1)

                except TimeoutException:
                    print("Loading took too much time! WHYYYYYY")
                    exit(1)

                y += Y_STEP
            x += X_STEP

        browser.close()
        browser.quit()
    except Exception as err:
        print(err)
        input("Close browser?")
        browser.close()
        browser.quit()

def crop():
    # Ořezat obrázky
    files = [f for f in os.listdir(DOWNLOAD) if re.match(r'mapy(\(([0-9])+\))*.png', f)]
    for file in files:
        print(file)
        with Image.open(f"{DOWNLOAD}/{file}") as img:
            left = 0
            top = 0
            right = 1896
            bottom = 860
            imc = img.crop((left, top, right, bottom))
            name = file.split(".")[0]
            imc.save(f"{DOWNLOAD}/cr-{name}.png")

download()
crop()

# Použít Hugin pro sešití obrázků
