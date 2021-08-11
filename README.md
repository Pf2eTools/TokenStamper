# RPG Token Stamper

## Tokens of Nethys
Small scripts to download creature images from the [Archives of Nethys](https://2e.aonprd.com/), and turn them into circular token images for virtual table top simulators.

## Usage

0. Install [Python and Pip](https://python.org/downloads)
0. Open a terminal or command prompt in the folder for this repository.
1. Run `pip install -r requirements.txt`
2. To download all images from AoN run `py nethys-scraper.py`. Alternatively, place images you want to turn into tokens into the `input` directory.
3. Place token borders and backgrounds in the `token` directory. Matching background and border should be of the same size. Some samples are provided.
4. Run `py generate-tokens.py`. If `meta.json` is present, the script will automatically create the token images. Otherwise, follow the instructions on the GUI. You can interrupt the program by pressing `CTRL+C` in your terminal/command prompt.
