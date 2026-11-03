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

    # читаем старый список: сохраняем уже заданные названия
    old_titles = {}
    if os.path.isfile(list_path):
        with open(list_path, encoding="utf-8") as fh:
            for m in re.finditer(r'src:"([^"]+)"\s*,\s*title:"((?:[^"\\]|\\.)*)"', fh.read()):
                old_titles[m.group(1)] = m.group(2)

    def title_from_name(name):
        stem = re.sub(r"\s+", " ", os.path.splitext(name)[0].replace("-", " ").replace("_", " ")).strip()
        return stem[:1].upper() + stem[1:] if stem else name

    def esc(s):
        return s.replace("\\", "\\\\").replace('"', '\\"')

    files = sorted(
        f for f in os.listdir(SRC_DIR)
        if f.lower().endswith(EXTS) and os.path.isfile(os.path.join(SRC_DIR, f))
    )

    items = ",\n".join(
        '  {{src:"photos/{f}", title:"{t}"}},'.format(
            f=f, t=esc(old_titles.get("photos/" + f) or title_from_name(f))
        )
        for f in files
    )

    with open(list_path, "w", encoding="utf-8") as fh:
        fh.write("/* Сгенерировано автоматически из содержимого photos/ — файл make_thumbs.py.\n")
        fh.write("   Названия можно править: для уже добавленных кадров они сохраняются между запусками.\n")
        fh.write("   Для нового кадра название возьмётся из имени файла, потом поправьте руками. */\n")
        fh.write("window.PHOTOS = [\n" + items + "\n];\n")
    print("Список фото:", len(files))

if __name__ == "__main__":
    main()
    write_photo_list()
