# -*- coding: utf-8 -*-
"""
bot/utils/phone.py — O'zbekiston telefon raqamlarini normalizatsiya qilish.

Foydalanuvchi raqamni qanday formatda yozishidan qat'i nazar
(998901234567, 901234567, +998901234567, oralarida bo'shliq/tire bilan
va hokazo) natija har doim bitta standart ko'rinishga keltiriladi:

    Saqlash uchun:   +998901234567
    Ko'rsatish uchun: +998 90 123 45 67
"""
from __future__ import annotations

import re
from typing import Optional

_UZ_OPERATOR_CODES = {
    "33", "88", "90", "91", "93", "94", "95", "97", "98", "99", "20", "77",
}


def _only_digits(raw: str) -> str:
    return re.sub(r"\D", "", raw)


def normalize_phone(raw: str) -> Optional[str]:
    """Turli formatdagi telefon raqamlarni +998XXXXXXXXX ko'rinishiga keltiradi.

    Returns None agar raqam yaroqsiz bo'lsa.
    """
    if not raw:
        return None

    digits = _only_digits(raw)

    # 998901234567 (12 ta raqam, 998 bilan boshlanadi)
    if len(digits) == 12 and digits.startswith("998"):
        national = digits[3:]
    # 901234567 (9 ta raqam, operator kodi bilan boshlanadi)
    elif len(digits) == 9:
        national = digits
    # 8901234567 yoki 09012345678 kabi holatlar uchun tozalash
    elif len(digits) == 13 and digits.startswith("998"):
        return None
    else:
        return None

    if len(national) != 9:
        return None

    operator_code = national[:2]
    if operator_code not in _UZ_OPERATOR_CODES:
        return None

    return f"+998{national}"


def format_phone_pretty(normalized: str) -> str:
    """+998901234567 -> +998 90 123 45 67"""
    if not normalized or not normalized.startswith("+998") or len(normalized) != 13:
        return normalized
    digits = normalized[4:]  # 901234567
    return f"+998 {digits[0:2]} {digits[2:5]} {digits[5:7]} {digits[7:9]}"


_PHONE_PATTERN_IN_TEXT = re.compile(
    r"(\+?998[\s\-]?\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})|(\b\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b)"
)


def text_contains_phone(text: str) -> bool:
    """Matn ichida allaqachon telefon raqami mavjudligini aniqlaydi.

    Bu funksiya reklama matniga avtomatik ravishda ikkinchi marta telefon
    raqami qo'shib yuborilishining oldini olish uchun ishlatiladi.
    """
    if not text:
        return False
    candidates = re.findall(r"[\d\s\-\+\(\)]{7,}", text)
    for candidate in candidates:
        if normalize_phone(candidate) is not None:
            return True
    return False
