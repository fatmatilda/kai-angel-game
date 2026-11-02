#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Создаёт audio_manifest.json по MP3-файлам в папках audios/*.

Формат имени файла:
    artist_track-name.mp3

Правило разбора:
    часть до первого '_'  -> исполнитель
    часть после '_'      -> название трека
    дефисы '-'           -> пробелы

Пример:
    oKAk_on-me.mp3 -> artist='oKAk', title='on me'

Запускай скрипт из любой папки: пути определяются относительно самого .py.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
AUDIO_ROOT = ROOT / "audios"
OUTPUT_FILE = ROOT / "audio_manifest.json"
FOLDERS = ("start", "random", "beat", "rewind", "best")
AUDIO_EXTENSIONS = {".mp3"}


def clean_part(value: str) -> str:
    """Заменяет дефисы пробелами и приводит пробелы к аккуратному виду."""
    value = value.replace("-", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_filename(path: Path) -> dict[str, str] | None:
    """Разбирает имя artist_track.mp3; разделителем считается первый '_'."""
    stem = path.stem
    if "_" not in stem:
        return None

    artist_raw, title_raw = stem.split("_", 1)
    artist = clean_part(artist_raw)
    title = clean_part(title_raw)
    if not artist or not title:
        return None

    return {
        "file": path.name,
        "artist": artist,
        "title": title,
    }


def scan_folder(folder_name: str) -> tuple[list[dict[str, str]], list[str]]:
    folder = AUDIO_ROOT / folder_name
    entries: list[dict[str, str]] = []
    warnings: list[str] = []

    if not folder.exists():
        warnings.append(f"Папка не найдена: {folder.relative_to(ROOT)}")
        return entries, warnings
    if not folder.is_dir():
        warnings.append(f"Путь не является папкой: {folder.relative_to(ROOT)}")
        return entries, warnings

    files = sorted(
        (p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS),
        key=lambda p: p.name.casefold(),
    )

    seen: set[tuple[str, str]] = set()
    for path in files:
        parsed = parse_filename(path)
        if parsed is None:
            warnings.append(
                f"Пропущен файл без формата artist_track.mp3: {path.relative_to(ROOT)}"
            )
            continue

        key = (parsed["artist"].casefold(), parsed["title"].casefold())
        if key in seen:
            warnings.append(
                f"Повтор пары исполнитель/трек в {folder_name}: "
                f"{parsed['artist']} — {parsed['title']} ({path.name})"
            )
        seen.add(key)
        entries.append(parsed)

    return entries, warnings


def main() -> int:
    manifest: dict[str, Any] = {}
    total = 0
    all_warnings: list[str] = []

    for folder_name in FOLDERS:
        entries, warnings = scan_folder(folder_name)
        manifest[folder_name] = entries
        total += len(entries)
        all_warnings.extend(warnings)
        print(f"audios/{folder_name}: {len(entries)} MP3")

    OUTPUT_FILE.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\nГотово: {OUTPUT_FILE}")
    print(f"Всего файлов добавлено в манифест: {total}")
    if all_warnings:
        print("\nПредупреждения:")
        for warning in all_warnings:
            print(f" - {warning}")
    else:
        print("Ошибок в именах файлов не найдено.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
