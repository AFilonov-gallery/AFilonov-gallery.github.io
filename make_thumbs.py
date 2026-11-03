#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ужимает JPEG/PNG из photos/ в photos/small/, конвертирует HEIC -> JPEG
   (с сохранением EXIF), и генерирует photos.js в корне.

   HEIC-файлы после конвертации удаляются из photos/ — браузеры их не
   показывают, а в списке должны жить JPEG. Конвертация идёт один раз,
   при первом же прогоне после загрузки кадра.

   Требование окружения: pip install pillow-heif
   (для JPEG/PNG достаточно одного Pillow, библиотека подхватывается
    мягко: если её нет — HEIC просто пропускается с предупреждением).
"""
import os
import re
from PIL import Image, ImageOps

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_OK = True
except Exception:
    HEIF_OK = False

SRC_DIR = "photos"
DST_DIR = os.path.join(SRC_DIR, "small")
MAX_SIDE = 900    # большая сторона миниатюры, px
QUALITY = 78      # качество JPEG миниатюр, 0-100
FULL_QUALITY = 92 # качество полноразмерных JPEG, конвертируемых из HEIC

IMG_EXTS = (".jpg", ".jpeg", ".png")
HEIC_EXTS = (".heic", ".heif")


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    for name in sorted(os.listdir(SRC_DIR)):
        path = os.path.join(SRC_DIR, name)
        if not os.path.isfile(path):
            continue
        low = name.lower()
        if low.endswith(HEIC_EXTS):
            convert_heic(path, name)
            continue
        if not low.endswith(IMG_EXTS):
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


def convert_heic(path, name):
    """HEIC -> полноразмерный JPEG с сохранением EXIF; оригинал удаляется."""
    if not HEIF_OK:
        print("SKIP ", name, "- нет библиотеки pillow-heif (pip install pillow-heif)")
        return
    stem = os.path.splitext(name)[0]
    target = os.path.join(SRC_DIR, stem + ".jpg")
    if os.path.isfile(target):
        print("SKIP ", name, "- уже есть", stem + ".jpg, конфликт имён")
        return
    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)  # разворот по EXIF, ориентация -> 1
        exif_bytes = img.info.get("exif")   # полный EXIF уже с исправленной ориентацией
        img = img.convert("RGB")
        img.save(target, "JPEG", quality=FULL_QUALITY, optimize=True,
                 **({"exif": exif_bytes} if exif_bytes else {}))
    except Exception as e:
        print("SKIP ", name, "-", e)
        return
    try:
        os.remove(path)  # HEIC из репозитория больше не нужен
    except OSError as e:
        print("WARN ", name, "- не удалось удалить оригинал:", e)

    # миниатюра для только что созданного JPEG
    try:
        img = Image.open(target)
        img = ImageOps.exif_transpose(img).convert("RGB")
        w, h = img.size
        k = min(1.0, MAX_SIDE / float(max(w, h)))
        nw, nh = int(w * k), int(h * k)
        if k < 1.0:
            img = img.resize((nw, nh), Image.LANCZOS)
        img.save(os.path.join(DST_DIR, stem + ".jpg"), "JPEG",
                 quality=QUALITY, optimize=True)
    except Exception as e:
        print("WARN ", stem + ".jpg", "- миниатюра не создалась:", e)
    print("HEIC ", name, "->", stem + ".jpg (EXIF сохранён)")


# ---------- Генерация photos.js ----------
def write_photo_list():
    list_path = "photos.js"

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
        if f.lower().endswith(IMG_EXTS) and os.path.isfile(os.path.join(SRC_DIR, f))
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
    parts = []
    for s in ordered:
        t = esc(old_titles.get(s) or title_from_name(s.split("photos/", 1)[-1]))
        parts.append('  {src:"' + s + '", title:"' + t + '"}')
    items = ",\n".join(parts)

    with open(list_path, "w", encoding="utf-8") as fh:
        fh.write("/* Порядок строк на сайте = порядок строк здесь. Расставьте как хотите -\n")
        fh.write("   скрипт запомнит ваш порядок. Новые кадры дописываются в начало списка,\n")
        fh.write("   названия их берутся из имени файла - потом поправьте здесь руками. */\n")
        fh.write("window.PHOTOS = [\n" + items + "\n];\n")
    print("Список фото:", len(ordered))

if __name__ == "__main__":
    main()
    write_photo_list()
