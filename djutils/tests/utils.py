from djutils.test import TestCase
from djutils.utils.strings import split_words_at


class StringUtilsTestCase(TestCase):
    def test_split_words_at(self):
        s = 'aa bb cc dd'

        self.assertEqual(split_words_at(s, 1), 'aa')
        self.assertEqual(split_words_at(s, 1, False), 'a')
        self.assertEqual(split_words_at(s, 2), 'aa')
        self.assertEqual(split_words_at(s, 2, False), 'aa')
        self.assertEqual(split_words_at(s, 3), 'aa bb')
        self.assertEqual(split_words_at(s, 3, False), 'aa')

        self.assertEqual(split_words_at(s, 100), 'aa bb cc dd')
        self.assertEqual(split_words_at(s, 100, False), 'aa bb cc dd')
