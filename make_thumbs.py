#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ужимает все JPEG/PNG из photos/ и кладёт миниатюры в photos/small/,
   а заодно собирает photos/photos.js — список фото для индекса."""
import os
import re
from PIL import Image, ImageOps

SRC_DIR = "photos"
DST_DIR = os.path.join("photos", "small")
MAX_SIDE = 900   # большая сторона миниатюры, px
QUALITY = 78     # качество JPEG, 0-100
EXTS = (".jpg", ".jpeg", ".png")

def main():
    os.makedirs(DST_DIR, exist_ok=True)
    for name in sorted(os.listdir(SRC_DIR)):
        path = os.path.join(SRC_DIR, name)
        if not os.path.isfile(path):
            continue
        if not name.lower().endswith(EXTS):
            continue
        try:
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            w, h = img.size
            k = min(1.0, MAX_SIDE / float(max(w, h)))
            nw, nh = int(w * k), int(h * k)
            if k < 1.0:
                img = img.resize((nw, nh), Image.LANCZOS)
            out = os.path.join(DST_DIR, name)
            img.save(out, "JPEG", quality=QUALITY, optimize=True)
            print("OK   ", name)
        except Exception as e:
            print("SKIP ", name, "-", e)

# ---------- Генерация photos/photos.js ----------
def write_photo_list():
    list_path = os.path.join(SRC_DIR, "photos.js")

    # читаем старый список: порядок строк и названия переносим как есть
    old_entries = []
    old_titles = {}
    if os.path.isfile(list_path):
        with open(list_path, encoding="utf-8") as fh:
            text = fh.read()
        for m in re.finditer(r'\{\s*src:\s*"([^"]+)"\s*,\s*title:\s*"((?:[^"\\]|\\.)*)"', text):
            old_entries.append(m.group(1))
            old_titles[m.group(1)] = m.group(2)

    def title_from_name(name):
        stem = re.sub(r"\s+", " ", os.path.splitext(name)[0].replace("-", " ").replace("_", " ")).strip()
        return stem[:1].upper() + stem[1:] if stem else name

    def esc(s):
        return s.replace("\\", "\\\\").replace('"', '\\"')

    files = set(
        f for f in os.listdir(SRC_DIR)
        if f.lower().endswith(EXTS) and os.path.isfile(os.path.join(SRC_DIR, f))
    )

    kept = []      # кадры из старого списка, которые ещё на диске — порядок как был
    kept_names = set()
    for src in old_entries:
        name = src.split("photos/", 1)[-1]
        if name in files:
            kept.append(src)
            kept_names.add(name)

    new = sorted(f for f in files if f not in kept_names)  # новинки — в начало списка

    ordered = ["photos/" + f for f in new] + kept
    items = ",\n".join(
        '  {src:"{s}", title:"{t}"}'.format(
            s=s, t=esc(old_titles.get(s) or title_from_name(s.split("photos/", 1)[-1]))
        )
        for s in ordered
    )

    with open(list_path, "w", encoding="utf-8") as fh:
        fh.write("/* Порядок строк на сайте = порядок строк здесь. Расставьте как хотите -\n")
        fh.write("   скрипт запомнит ваш порядок. Новые кадры дописываются в начало списка,\n")
        fh.write("   названия их берутся из имени файла - потом поправьте здесь руками. */\n")
        fh.write("window.PHOTOS = [\n" + items + "\n];\n")
    print("Список фото:", len(ordered))

if __name__ == "__main__":
    main()
    write_photo_list()
