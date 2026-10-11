import unittest

from cleaning.normalize import normalize

URDU_YEH = "\N{ARABIC LETTER FARSI YEH}"
URDU_KAF = "\N{ARABIC LETTER KEHEH}"
GOL_HEH = "\N{ARABIC LETTER HEH GOAL}"
DO_CHASHMI_HEH = "\N{ARABIC LETTER HEH DOACHASHMEE}"
ZWNJ = "\N{ZERO WIDTH NON-JOINER}"


class TestLetters(unittest.TestCase):
    def test_arabic_yeh_and_alef_maksura_become_urdu_yeh(self):
        self.assertEqual(normalize("\N{ARABIC LETTER YEH}"), URDU_YEH)
        self.assertEqual(normalize("\N{ARABIC LETTER ALEF MAKSURA}"), URDU_YEH)

    def test_arabic_kaf_becomes_urdu_kaf(self):
        self.assertEqual(normalize("\N{ARABIC LETTER KAF}"), URDU_KAF)

    def test_arabic_heh_becomes_gol_heh(self):
        self.assertEqual(normalize("\N{ARABIC LETTER HEH}"), GOL_HEH)

    def test_gol_heh_and_do_chashmi_heh_stay_distinct(self):
        self.assertEqual(normalize(GOL_HEH + DO_CHASHMI_HEH), GOL_HEH + DO_CHASHMI_HEH)

    def test_heh_with_yeh_above_becomes_heh_goal_with_hamza(self):
        self.assertEqual(
            normalize("\N{ARABIC LETTER HEH WITH YEH ABOVE}"), "\N{ARABIC LETTER HEH GOAL WITH HAMZA ABOVE}"
        )

    def test_yeh_with_hamza_survives(self):
        yeh_with_hamza = "\N{ARABIC LETTER YEH WITH HAMZA ABOVE}"
        self.assertEqual(normalize(yeh_with_hamza), yeh_with_hamza)
        self.assertEqual(normalize("\N{ARABIC LETTER YEH}\N{ARABIC HAMZA ABOVE}"), yeh_with_hamza)

    def test_decomposed_alef_madda_is_composed(self):
        self.assertEqual(normalize("\N{ARABIC LETTER ALEF}\N{ARABIC MADDAH ABOVE}"), "\N{ARABIC LETTER ALEF WITH MADDA ABOVE}")

    def test_presentation_forms_become_base_letters(self):
        self.assertEqual(normalize("\N{ARABIC LETTER KEHEH ISOLATED FORM}"), URDU_KAF)
        self.assertEqual(normalize("\N{ARABIC LIGATURE ALLAH ISOLATED FORM}"), "الل" + GOL_HEH)


class TestRemovedCharacters(unittest.TestCase):
    def test_tatweel_is_removed(self):
        self.assertEqual(normalize("ک\N{ARABIC TATWEEL}تاب"), "کتاب")

    def test_invisible_characters_are_removed(self):
        invisible = "\N{ZERO WIDTH SPACE}\N{ZERO WIDTH JOINER}\N{LEFT-TO-RIGHT MARK}\N{RIGHT-TO-LEFT MARK}\N{ARABIC LETTER MARK}\N{ZERO WIDTH NO-BREAK SPACE}"
        self.assertEqual(normalize(f"کت{invisible}اب"), "کتاب")


class TestZwnj(unittest.TestCase):
    def test_zwnj_between_letters_is_kept(self):
        self.assertEqual(normalize(f"بے{ZWNJ}شمار"), f"بے{ZWNJ}شمار")

    def test_zwnj_at_word_edges_is_removed(self):
        self.assertEqual(normalize(f"{ZWNJ}کتاب{ZWNJ} ہے"), "کتاب ہے")

    def test_repeated_zwnj_is_collapsed(self):
        self.assertEqual(normalize(f"بے{ZWNJ}{ZWNJ}شمار"), f"بے{ZWNJ}شمار")


class TestDigits(unittest.TestCase):
    def test_extended_arabic_indic_digits_become_ascii(self):
        self.assertEqual(normalize("۲۰۲۶"), "2026")

    def test_arabic_indic_digits_become_ascii(self):
        self.assertEqual(normalize("٢٠٢٦"), "2026")


class TestWhitespace(unittest.TestCase):
    def test_spaces_are_collapsed(self):
        self.assertEqual(normalize("ایک\N{NO-BREAK SPACE} دو\t\tتین"), "ایک دو تین")

    def test_line_breaks_are_collapsed(self):
        self.assertEqual(normalize("  پہلی سطر  \r\n\n\n  دوسری سطر\N{LINE SEPARATOR}تیسری  "), "پہلی سطر\nدوسری سطر\nتیسری")


class TestIdempotence(unittest.TestCase):
    def test_normalizing_twice_changes_nothing(self):
        text = f"\N{ARABIC LETTER KAF}ت\N{ARABIC TATWEEL}اب{ZWNJ}{ZWNJ} ۲۰۲۶\r\n\n بے{ZWNJ}شمار\N{NO-BREAK SPACE}"
        self.assertEqual(normalize(normalize(text)), normalize(text))


if __name__ == "__main__":
    unittest.main()
