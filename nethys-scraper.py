from bs4 import BeautifulSoup
import requests
import json
import shutil
import os


def getSoup(url):
    html = requests.get(url).text
    return BeautifulSoup(html, 'lxml')


def verifySoup(soup):
    if "Object reference not set to an instance of an object" in soup.title.text:
        print(f"\tIvalid Url.", end="")
        return False
    return True


def scrapeImages(soup):
    name = soup.find('h1', class_='title').contents[0].strip()
    source = soup.find('a', class_='external-link').contents[0].contents[0].split("pg.")[0].strip()
    clean_source = "".join(x for x in source if (x.isalnum() or x in "._- ")).lower()
    size = soup.find('span', class_='traitsize').contents[0].strip().lower()
    if size == "large":
        token_size = 2
    elif size == "huge":
        token_size = 3
    elif size == "gargantuan":
        token_size = 4
    else:
        token_size = 1

    img = soup.find('img', class_='thumbnail')
    if img:
        url = f"{BASE_URL}{img['src']}".replace("\\", "/")
        image = {"url": url, "meta": {"size": token_size, "x": 0, "y": 0, "r": 0}}

        if DOWNLOAD_DIR:
            out_folder = f"{DOWNLOAD_DIR}/{clean_source}"
            if not os.path.exists(out_folder):
                os.makedirs(out_folder)
            req = requests.get(url, stream=True)
            if req.status_code == 200:
                req.raw.decode_content = True
                filename = f"{out_folder}/{name}.{url.split('.')[-1]}"
                print(f"\tSaving to '{filename}'...", end="")
                with open(filename, "wb") as out:
                    shutil.copyfileobj(req.raw, out)
            else:
                print(f"\tFailed. Request status code '{req.status_code}'!")

        try:
            SCRAPED[clean_source][name] = image
        except KeyError:
            SCRAPED[clean_source] = {name: image}
    else:
        print(f"\tNo image found.", end="")


def scrapeNethys(baseURL, initialIx=1):
    fails = 0
    idx = initialIx
    while fails < 5:
        url = f'{baseURL}{idx}'
        print(f'\nScraping {url}...', end="")
        soup = getSoup(url)
        if verifySoup(soup):
            fails = 0
            scrapeImages(soup)
        else:
            fails += 1
        idx += 1
    print("\n")


def dump(file):
    print(f"\nDumping to '{file}'...")

    with open(file, "w") as f:
        json.dump(SCRAPED, f, indent=2, separators=(',', ': '), )


def download_from_meta():
    print(f"Downloading all images refrenced in '{META}'.")
    with open(META, "r") as m:
        meta = json.load(m)
    for source in meta:
        out_folder = f"{DOWNLOAD_DIR}/{source}"
        if not os.path.exists(out_folder):
            os.makedirs(out_folder)
        for creature in meta[source]:
            url = meta[source][creature]["url"]
            req = requests.get(url, stream=True)
            if req.status_code == 200:
                req.raw.decode_content = True
                filename = f"{out_folder}/{creature}.{url.split('.')[-1]}"
                print(f"Saving image to '{filename}'...")
                with open(filename, "wb") as out:
                    shutil.copyfileobj(req.raw, out)
            else:
                print(f"Getting image from {url} failed. Request status code '{req.status_code}'!")


# CONFIG ###############################################################################################################
META = "meta.json"
DOWNLOAD_DIR = "input"
BASE_URL = "https://2e.aonprd.com/"
MONSTERS_URL = "https://2e.aonprd.com/Monsters.aspx?ID="
########################################################################################################################

if __name__ == "__main__":
    SCRAPED = dict()
    # scrapeNethys(MONSTERS_URL)
    # scrapeNethys(MONSTERS_URL, 975)
    # dump(META)

    download_from_meta()
