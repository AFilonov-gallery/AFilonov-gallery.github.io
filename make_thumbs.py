#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ужимает все JPEG/PNG из photos/ и кладёт миниатюры в photos/small/"""
import os
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

if __name__ == "__main__":
    main()
