import unittest
from collections import Counter

from cleaning.clean_corpus import is_mostly_urdu, is_spam, line_hash, urdu_lines, without_boilerplate


class TestUrduLineFilter(unittest.TestCase):
    def test_urdu_line_is_kept(self):
        self.assertTrue(is_mostly_urdu("پاکستان ایک خوبصورت ملک ہے۔"))

    def test_english_line_is_dropped(self):
        self.assertFalse(is_mostly_urdu("Click here to subscribe to our newsletter"))

    def test_urdu_with_english_words_is_kept(self):
        self.assertTrue(is_mostly_urdu("میں نے Google پر سرچ کیا اور جواب مل گیا"))

    def test_line_without_letters_is_dropped(self):
        self.assertFalse(is_mostly_urdu("2026 | 15:30 | ۔۔۔"))

    def test_only_non_urdu_lines_are_removed(self):
        text = "پہلی سطر اردو میں ہے\nThis line is English\nآخری سطر بھی اردو ہے"
        self.assertEqual(urdu_lines(text), "پہلی سطر اردو میں ہے\nآخری سطر بھی اردو ہے")


class TestSpam(unittest.TestCase):
    def test_forex_document_is_spam(self):
        self.assertTrue(is_spam("فاریکس ٹریڈنگ کے بہترین طریقے سیکھیں"))

    def test_binary_option_document_is_spam(self):
        self.assertTrue(is_spam("بائنری آپشن سے روزانہ منافع کمائیں"))

    def test_news_document_is_not_spam(self):
        self.assertFalse(is_spam("حکومت نے نئے بجٹ کا اعلان کر دیا"))


class TestBoilerplate(unittest.TestCase):
    def test_lines_repeated_across_documents_are_removed(self):
        share_line = "یہ خبر شیئر کریں"
        line_counts = Counter({line_hash(share_line): 5, line_hash("اصل خبر"): 1})
        self.assertEqual(without_boilerplate(f"اصل خبر\n{share_line}", line_counts), "اصل خبر")

    def test_lines_below_threshold_are_kept(self):
        line_counts = Counter({line_hash("ایک سطر"): 4})
        self.assertEqual(without_boilerplate("ایک سطر", line_counts), "ایک سطر")


if __name__ == "__main__":
    unittest.main()
