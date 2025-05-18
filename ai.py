import json
import random
import re
from pathlib import Path

class ShiritoriAI:
    def __init__(self, word_file="data/words.json", unknown_file="data/unknown.json"):
        self.word_file = Path(word_file)
        self.unknown_file = Path(unknown_file)
        self.word_dict = {}
        self.reading_to_word = {}
        self.used_words = set()
        self.used_readings = set()  # Дублирование этой переменной удалим
        self.unknown_words = set()

        # Загрузка словаря
        if self.word_file.exists():
            with open(self.word_file, "r", encoding="utf-8") as f:
                raw_words = json.load(f)
            for entry in raw_words:
                kanji, reading = self.split_word(entry)
                self.word_dict[kanji] = reading
                self.reading_to_word[reading] = kanji

        # Загрузка неизвестных слов
        if self.unknown_file.exists():
            with open(self.unknown_file, "r", encoding="utf-8") as f:
                self.unknown_words = set(json.load(f))

    def split_word(self, word):
        match = re.match(r"(.+?)\[(.+?)\]", word)
        if match:
            return match.group(1), match.group(2)
        return word, word  # Если без фуриганы

    def get_reading(self, word):
        return self.word_dict.get(word, "")

    def get_last_kana(self, word):
        reading = self.get_reading(word)
        if not reading:
            return ""
        i = -1
        while -i <= len(reading):
            if reading[i] not in ["ん", "ー"]:
                return reading[i]
            i -= 1
        return ""

    def get_next_word(self, last_kana):
        if not last_kana or last_kana in ["ん", "ー"]:
            return None  # Конец игры

        candidates = [
            (k, r) for k, r in self.word_dict.items()
            if (r.startswith(last_kana) or k.startswith(last_kana)) and k not in self.used_words
        ]
        if not candidates:
            return None
        kanji, _ = random.choice(candidates)
        self.used_words.add(kanji)
        return kanji

    def is_valid(self, word, last_kana):
        if word in self.used_words:
            return False
        reading = self.get_reading(word)
        if not reading:
            return False
        if reading[0] == "ん":
            return False
        return reading.startswith(last_kana)

    def add_unknown(self, word):
        self.unknown_words.add(word)
        with open(self.unknown_file, "w", encoding="utf-8") as f:
            json.dump(sorted(list(self.unknown_words)), f, ensure_ascii=False, indent=2)

    def reset(self):
        self.used_words.clear()
        self.unknown_words.clear()
