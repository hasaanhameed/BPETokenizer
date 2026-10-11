import random
import tempfile
import unittest
from pathlib import Path

from tokenizer.bpe import END_OF_TEXT, END_OF_TEXT_ID, BPETokenizer, pretokenize, train_reference

KAF = tuple("ک".encode("utf-8"))
SAMPLE_MERGES = [KAF, (32, 257), (ord("t"), ord("h"))]

ROUND_TRIP_TEXTS = [
    "",
    "😀👍🏽 emoji",
    "Hello, world! It's 2026.",
    "line one\nline two\n\n\ttabbed  \r\n",
    "اُردُو ایک خوبصورت زبان ہے۔",
    "کتاب پڑھیں" + END_OF_TEXT + "نئی دستاویز" + END_OF_TEXT,
    END_OF_TEXT + END_OF_TEXT,
    "<|endof" + "text|>",
]


def random_text(rng, length):
    code_points = []
    while len(code_points) < length:
        cp = rng.randrange(0x110000)
        if not 0xD800 <= cp <= 0xDFFF:
            code_points.append(chr(cp))
    return "".join(code_points)


class PretokenizeTest(unittest.TestCase):
    def test_pieces_join_back_to_text(self):
        rng = random.Random(0)
        for text in ROUND_TRIP_TEXTS + [random_text(rng, 200) for _ in range(50)]:
            self.assertEqual("".join(pretokenize(text)), text)

    def test_diacritics_stay_in_word(self):
        self.assertEqual(pretokenize("اُردُو"), ["اُردُو"])

    def test_zwnj_stays_in_word(self):
        self.assertEqual(pretokenize("بے‌شمار"), ["بے‌شمار"])

    def test_leading_space_attaches_to_next_word(self):
        self.assertEqual(pretokenize("میں اردو بولتا ہوں"), ["میں", " اردو", " بولتا", " ہوں"])

    def test_numbers_split_into_three_digit_chunks(self):
        self.assertEqual(pretokenize(" 1234567"), [" 123", "456", "7"])


class BPETokenizerTest(unittest.TestCase):
    def setUp(self):
        self.tokenizer = BPETokenizer(SAMPLE_MERGES)

    def test_round_trip(self):
        rng = random.Random(1)
        for text in ROUND_TRIP_TEXTS + [random_text(rng, 200) for _ in range(50)]:
            self.assertEqual(self.tokenizer.decode(self.tokenizer.encode(text)), text)

    def test_vocab_layout(self):
        vocab = self.tokenizer.vocab
        self.assertEqual([vocab[i] for i in range(256)], [bytes([i]) for i in range(256)])
        self.assertEqual(vocab[END_OF_TEXT_ID], END_OF_TEXT.encode("utf-8"))
        self.assertEqual(vocab[257], "ک".encode("utf-8"))
        self.assertEqual(vocab[258], " ک".encode("utf-8"))
        self.assertEqual(len(vocab), 257 + len(SAMPLE_MERGES))

    def test_merges_applied(self):
        self.assertEqual(self.tokenizer.encode(" ک"), [258])
        self.assertEqual(self.tokenizer.encode("the"), [259, ord("e")])

    def test_special_token_is_one_id(self):
        self.assertEqual(self.tokenizer.encode("a" + END_OF_TEXT + "b"), [ord("a"), END_OF_TEXT_ID, ord("b")])

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.merges"
            self.tokenizer.save(path)
            self.assertEqual(path.read_text(encoding="utf-8").splitlines()[0], f"{KAF[0]} {KAF[1]}")
            self.assertEqual(BPETokenizer.load(path).merges, SAMPLE_MERGES)


class ReferenceTrainerTest(unittest.TestCase):
    def test_sanity_check_worked_by_hand(self):
        a, b, c, d = map(ord, "abcd")
        expected = [(a, a), (257, a), (258, b), (d, 259), (260, a), (261, c), (259, 262)]
        self.assertEqual(train_reference("aaabdaaabac", 10), expected)

    def test_tie_goes_to_greater_byte_pair(self):
        self.assertEqual(train_reference("ab ba", 1), [(ord("b"), ord("a"))])

    def test_special_token_never_merged(self):
        self.assertEqual(train_reference(END_OF_TEXT * 50 + "xy", 10), [(ord("x"), ord("y"))])

    def test_merges_never_cross_words(self):
        self.assertEqual(train_reference("x y", 10), [(ord(" "), ord("y"))])

    def test_trained_tokenizer_round_trips(self):
        text = "اُردُو ایک خوبصورت زبان ہے۔ اردو پاکستان کی قومی زبان ہے۔" * 3
        tokenizer = BPETokenizer(train_reference(text, 40))
        self.assertLess(len(tokenizer.encode(text)), len(text.encode("utf-8")))
        self.assertEqual(tokenizer.decode(tokenizer.encode(text)), text)


if __name__ == "__main__":
    unittest.main()
