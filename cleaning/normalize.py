import unicodedata
from itertools import chain

import regex

ARABIC_TO_URDU_LETTERS = {
    "ARABIC LETTER YEH": "ARABIC LETTER FARSI YEH",
    "ARABIC LETTER ALEF MAKSURA": "ARABIC LETTER FARSI YEH",
    "ARABIC LETTER KAF": "ARABIC LETTER KEHEH",
    "ARABIC LETTER HEH": "ARABIC LETTER HEH GOAL",
    "ARABIC LETTER HEH WITH YEH ABOVE": "ARABIC LETTER HEH GOAL WITH HAMZA ABOVE",
    "ARABIC LETTER TEH MARBUTA": "ARABIC LETTER TEH MARBUTA GOAL",
}

REMOVED_CHARACTERS = [
    "ARABIC TATWEEL",
    "SOFT HYPHEN",
    "ZERO WIDTH SPACE",
    "ZERO WIDTH JOINER",
    "ZERO WIDTH NO-BREAK SPACE",
    "INVISIBLE SEPARATOR",
    "LEFT-TO-RIGHT MARK",
    "RIGHT-TO-LEFT MARK",
    "ARABIC LETTER MARK",
    "LEFT-TO-RIGHT EMBEDDING",
    "RIGHT-TO-LEFT EMBEDDING",
    "POP DIRECTIONAL FORMATTING",
    "LEFT-TO-RIGHT OVERRIDE",
    "RIGHT-TO-LEFT OVERRIDE",
    "LEFT-TO-RIGHT ISOLATE",
    "RIGHT-TO-LEFT ISOLATE",
    "FIRST STRONG ISOLATE",
    "POP DIRECTIONAL ISOLATE",
]

LINE_SEPARATORS = ["CARRIAGE RETURN", "LINE SEPARATOR", "PARAGRAPH SEPARATOR"]

ARABIC_INDIC_DIGITS = range(0x0660, 0x066A)
EXTENDED_ARABIC_INDIC_DIGITS = range(0x06F0, 0x06FA)
PRESENTATION_FORMS = chain(range(0xFB50, 0xFE00), range(0xFE70, 0xFEFF))

URDU_LETTERS = str.maketrans(
    {unicodedata.lookup(arabic): unicodedata.lookup(urdu) for arabic, urdu in ARABIC_TO_URDU_LETTERS.items()}
)


def base_letters(code):
    return unicodedata.normalize("NFKC", chr(code)).translate(URDU_LETTERS)


TRANSLATION = {
    **{code: base_letters(code) for code in PRESENTATION_FORMS if base_letters(code) != chr(code)},
    **URDU_LETTERS,
    **{code: str(unicodedata.digit(chr(code))) for code in chain(ARABIC_INDIC_DIGITS, EXTENDED_ARABIC_INDIC_DIGITS)},
    **{ord(unicodedata.lookup(name)): None for name in REMOVED_CHARACTERS},
    **{ord(unicodedata.lookup(name)): "\n" for name in LINE_SEPARATORS},
}

ZWNJ = unicodedata.lookup("ZERO WIDTH NON-JOINER")
REPEATED_ZWNJ = regex.compile(r"\N{ZERO WIDTH NON-JOINER}{2,}")
STRAY_ZWNJ = regex.compile(r"(?<![\p{L}\p{M}])\N{ZERO WIDTH NON-JOINER}|\N{ZERO WIDTH NON-JOINER}(?!\p{L})")
SPACES = regex.compile(r"[\p{Zs}\t]+")
LINE_BREAKS = regex.compile(r" *\n[ \n]*")


def normalize(text):
    text = unicodedata.normalize("NFC", text)
    text = text.translate(TRANSLATION)
    text = REPEATED_ZWNJ.sub(ZWNJ, text)
    text = STRAY_ZWNJ.sub("", text)
    text = SPACES.sub(" ", text)
    text = LINE_BREAKS.sub("\n", text)
    return text.strip()
