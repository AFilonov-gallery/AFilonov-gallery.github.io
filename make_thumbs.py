# -*- coding: utf-8 -*-
"""make_thumbs.py — ужимает фото из photos/ в photos/small/ (для плиток)."""
from pathlib import Path
from PIL import Image

SRC = Path("photos")
DST = SRC / "small"
MAX_SIDE = 1600   # большая сторона миниатюры, px
QUALITY = 80      # качество JPEG, 0-100

if not SRC.is_dir():
    raise SystemExit("Папка photos/ не найдена — скрипт запускать из корня репозитория")

DST.mkdir(exist_ok=True)
done = skipped = 0

for f in sorted(SRC.iterdir()):
    if not f.is_file() or f.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        continue
    try:
        img = Image.open(f)
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        k = min(1.0, MAX_SIDE / max(w, h))
        if k < 1.0:
            img = img.resize((round(w * k), round(h * k)), Image.LANCZOS)
        # сохраняем под тем же именем; даже .png пишем как JPEG —
        # браузер узнаёт формат по содержимому, а вес решает всё
        img.save(DST / f.name, "JPEG", quality=QUALITY, optimize=True)
        done += 1
        print(f"OK    {f.name}")
    except Exception as e:
        skipped += 1
        print(f"SKIP  {f.name} — {e}")

print(f"Готово: {done} ужато, {skipped} пропущено")
