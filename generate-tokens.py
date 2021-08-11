import cv2 as cv
import numpy as np
import tkinter as tk
from PIL import ImageTk, Image
import os
import json


def add_images(img1, img2, size):
    alpha1 = img1[:, :, 3] / 255.0
    alpha2 = 1.0 - alpha1
    out = np.zeros((size, size, 4), np.uint8)
    for c in range(0, 4):
        out[:, :, c] = (alpha1 * img1[:, :, c] + alpha2 * img2[:, :, c])
    return out


def do_save(img, token, circleMeta, out_path):
    print(f"Saving Token '{out_path}'...", end=" ")
    try:
        bg = token["bg"]
    except KeyError:
        bg = None
    img = img["cv"]
    token = token["cv"]

    # resize image (We assume token is a square image)
    out_size = token.shape[0] - token.shape[0] % 2
    r = out_size // 2
    img = cv.copyMakeBorder(img, r, r, r, r, cv.BORDER_CONSTANT, value=(0, 0, 0, 0))
    scale = out_size / (circleMeta["r"] * 2)
    resized = cv.resize(img, (int(scale * img.shape[1]), int(scale * img.shape[0])), interpolation=cv.INTER_AREA)
    center = [int((circleMeta["y"] + r) * scale), int((circleMeta["x"] + r) * scale)]

    # crop images to size
    cropped_img = resized[center[0] - r:center[0] + r, center[1] - r:center[1] + r]
    cropped_token = token[out_size - 2 * r:out_size, out_size - 2 * r:out_size]

    # add the background
    if bg is not None:
        if type(bg) is tuple:
            background = np.zeros((out_size, out_size, 4), np.uint8)
            background[:] = (bg[2], bg[1], bg[0], 255)
        else:
            background = cv.imread(bg, -1)
            if background.shape[2] != 4:
                background = cv.cvtColor(background, cv.COLOR_RGB2RGBA)
        cropped_img = add_images(cropped_img, background, out_size)

    # mask original image
    mask = np.zeros((out_size, out_size), np.uint8)
    cv.circle(mask, (r, r), r - 10, (255, 255, 255), -1)
    masked = cv.bitwise_and(cropped_img, cropped_img, mask=mask)

    # add token border to image
    out = add_images(cropped_token, masked, out_size)

    cv.imwrite(out_path, out)
    print("Done.", end="\n")


def save_meta(path, to_save, meta):
    try:
        obj = meta[path[0]]
    except KeyError:
        meta[path[0]] = dict()
        obj = meta[path[0]]
    try:
        obj = obj[path[1]]
    except KeyError:
        obj[path[1]] = dict()
        obj = obj[path[1]]
    obj["meta"] = to_save
    with open(META, "w") as f:
        json.dump(meta, f, indent=2, separators=(',', ': '), )


def exit_ui(root):
    root.destroy()


def init_ui(img, tokens, out_path, meta):
    root = tk.Tk()
    root.title(img["url"])
    root.focus_force()

    frame = tk.Frame(root, height=100, width=img["w"])
    frame.pack()

    def onRadio():
        v = radio.get()
        for i in range(4):
            if i != v:
                try:
                    canvas.delete(tokens[i]["canvas"])
                except KeyError:
                    pass
        if circleMeta["r"] != 0:
            t = Image.open(tokens[v]["url"]).resize((int(2 * circleMeta["r"]), int(2 * circleMeta["r"])),
                                                    Image.ANTIALIAS)
            tokens[v]["tk"] = ImageTk.PhotoImage(t)
            tokens[v]["canvas"] = canvas.create_image(circleMeta["x"], circleMeta["y"], image=tokens[v]["tk"],
                                                      anchor="c")

    radio = tk.IntVar()
    tk.Radiobutton(frame, anchor="e", variable=radio, value=0, text="1x1 Token", command=onRadio).pack()
    tk.Radiobutton(frame, anchor="e", variable=radio, value=1, text="2x2 Token", command=onRadio).pack()
    tk.Radiobutton(frame, anchor="e", variable=radio, value=2, text="3x3 Token", command=onRadio).pack()
    tk.Radiobutton(frame, anchor="e", variable=radio, value=3, text="4x4 Token", command=onRadio).pack()
    radio.set(0)
    try:
        s = img["meta"]["size"]
        radio.set(s - 1)
    except KeyError:
        pass

    label_text = """Click+Drag to create and move token border.
                 Right click to unset token border.
                 Press "S" to save as token; "W" to exit."""
    tk.Label(frame, text=label_text).pack()

    canvas = tk.Canvas(root, height=img["h"], width=img["w"])
    canvas.pack(fill="both")
    img["tk"] = ImageTk.PhotoImage(Image.open(img["url"]))
    img["canvas"] = canvas.create_image(0, 0, image=img["tk"], anchor="nw")
    circleMeta = {"x": 0, "y": 0, "r": 0, "circle": None, "released": False}

    def onClick(evt):
        circleMeta["released"] = False
        circleMeta["x"] = int(evt.x)
        circleMeta["y"] = int(evt.y)
        circleMeta["r"] = 10
        circleMeta["circle"] = canvas.create_oval(circleMeta["x"] - circleMeta["r"], circleMeta["y"] - circleMeta["r"],
                                                  circleMeta["x"] + circleMeta["r"], circleMeta["y"] + circleMeta["r"])

    def onDrag(evt):
        if not circleMeta["circle"]:
            circleMeta["circle"] = canvas.create_oval(circleMeta["x"] - circleMeta["r"],
                                                      circleMeta["y"] - circleMeta["r"],
                                                      circleMeta["x"] + circleMeta["r"],
                                                      circleMeta["y"] + circleMeta["r"])
        if not circleMeta["released"]:
            circleMeta["r"] = int(
                np.linalg.norm(np.array([circleMeta["x"], circleMeta["y"]]) - np.array([evt.x, evt.y])))
        else:
            circleMeta["x"] = int(evt.x)
            circleMeta["y"] = int(evt.y)

        canvas.coords(circleMeta["circle"], circleMeta["x"] - circleMeta["r"], circleMeta["y"] - circleMeta["r"],
                      circleMeta["x"] + circleMeta["r"], circleMeta["y"] + circleMeta["r"])

    def onRelease(evt):
        if circleMeta["circle"]:
            canvas.delete(circleMeta["circle"])
            circleMeta["circle"] = None
        circleMeta["released"] = True
        canvas.unbind("<ButtonPress-1>")
        t = Image.open(tokens[radio.get()]["url"]).resize((int(2 * circleMeta["r"]), int(2 * circleMeta["r"])),
                                                          Image.ANTIALIAS)
        tokens[radio.get()]["tk"] = ImageTk.PhotoImage(t)
        tokens[radio.get()]["canvas"] = canvas.create_image(circleMeta["x"], circleMeta["y"],
                                                            image=tokens[radio.get()]["tk"], anchor="c")

    def onRightClick(evt):
        if circleMeta["circle"]:
            canvas.delete(circleMeta["circle"])
            circleMeta["circle"] = None
        try:
            canvas.delete(tokens[radio.get()]["canvas"])
        except KeyError:
            pass
        canvas.unbind("<ButtonPress-1>")
        canvas.bind("<ButtonPress-1>", onClick)

    def onKey(evt):
        char = evt.char.lower()
        if char == "s":
            if circleMeta["r"] == 0:
                raise Exception("You need to select an area first.")
            else:
                path = [img["url"].split("\\")[-2], img["url"].split("\\")[-1].split(".")[0]]
                to_save = {"x": circleMeta["x"], "y": circleMeta["y"], "r": circleMeta["r"], "size": radio.get() + 1}
                save_meta(path, to_save, meta)
                do_save(img, tokens[radio.get()], circleMeta, out_path)
                exit_ui(root)
        elif char == "w" or char == "q":
            print(f"Closing '{img['url']}'. No token created.")
            exit_ui(root)

    canvas.bind("<ButtonPress-1>", onClick)
    canvas.bind("<ButtonPress-3>", onRightClick)
    canvas.bind("<B1-Motion>", onDrag)
    canvas.bind("<ButtonRelease-1>", onRelease)
    root.bind("<Key>", onKey)

    return root


def get_image(url):
    img_cv = cv.imread(url, -1)
    imgHeight, imgWidth, channels = img_cv.shape
    # creating an alpha channel
    if channels != 4:
        img_cv = cv.cvtColor(img_cv, cv.COLOR_RGB2RGBA)

    return {"url": url, "cv": img_cv, "h": imgHeight, "w": imgWidth, "tk": None}


def get_token_images():
    out = []
    for i in range(len(TOKEN_FILES)):
        token = get_image(TOKEN_FILES[i])
        token["bg"] = TOKEN_BG[i]
        out.append(token)
    return out


def main():
    try:
        with open(META, "r") as m:
            meta = json.load(m)
    except FileNotFoundError:
        meta = dict()
    tokens = get_token_images()
    for subdir, _, files in os.walk(INPATH):
        for file in files:
            filename, extension = os.path.splitext(file)
            if extension in IMAGE_EXTENSIONS:
                image = get_image(os.path.join(subdir, file))
                try:
                    image["meta"] = meta[subdir.split("\\")[-1]][filename]["meta"]
                except KeyError:
                    image["meta"] = {"x": 0, "y": 0, "r": 0, "size": 1}

                out_folder = subdir.replace(INPATH, OUTPATH)
                if not os.path.exists(out_folder):
                    os.makedirs(out_folder)
                if image["meta"]["x"] and image["meta"]["y"] and image["meta"]["r"]:
                    token_idx = 0
                    if image["meta"]["size"]:
                        token_idx = image["meta"]["size"] - 1
                    do_save(image, tokens[token_idx],
                            {"x": image["meta"]["x"], "y": image["meta"]["y"], "r": image["meta"]["r"]},
                            os.path.join(out_folder, file))
                else:
                    ui = init_ui(image, tokens, os.path.join(out_folder, file), meta)
                    ui.mainloop()


# CONFIG ###############################################################################################################
META = "meta.json"
TOKEN_FILES = ["token/1x1.png", "token/2x2.png", "token/3x3.png", "token/4x4.png"]
TOKEN_BG = ["token/bg1x1.png", "token/bg2x2.png", "token/bg3x3.png", "token/bg4x4.png"]
# TOKEN_BG = [None, None, None, None]                          # Uncomment this line for transparent backgrounds
# TOKEN_BG = [(94, 0, 0), (94, 0, 0), (94, 0, 0), (94, 0, 0)]  # Uncomment this line for solid color (R,G,B) backgrounds
INPATH = "input"
OUTPATH = "output"
IMAGE_EXTENSIONS = [".png", ".jpg"]
########################################################################################################################

if __name__ == "__main__":
    main()
