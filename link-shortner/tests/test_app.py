import unittest
from api.base import Application


class LinkShortenerTestCase(unittest.TestCase):
    def test_encode_string_with_expiry_date_and_not_expired(self):
        self.app = Application()
        result = self.app.encode("This is abiola", expires="2019-02-12")
        print(result)
        decoded = self.app.decode(result)
        self.assertEqual(decoded['text'], "This is abiola")
        self.assertFalse(decoded['expired'])
        self.assertEqual(decoded['expires'], "2019-02-12")

    def test_encode_string_with_expiry_date_and_expired(self):
        app = Application()
        result = app.encode("This is abiola", expires="2018-12-10")
        print(result)
        decoded = app.decode(result)
        self.assertEqual(decoded['text'], 'This is abiola')
        self.assertTrue(decoded['expired'])
        self.assertEqual(decoded['expires'], "2018-12-10")

    def test_encode_string_without_expiry_date(self):
        app = Application()
        result = app.encode("23/323", domain="03")
        print(result)
        decoded = app.decode(result)
        self.assertEqual(decoded['text'], "23/323")
        self.assertFalse(decoded['expired'])
        self.assertIsNone(decoded['expires'])
        self.assertEqual(
            app.generate_url(decoded, path="/"),
            f"https://app.careerlyft.com/23/323")

    def test_encode_string_with_domain(self):
        app = Application()
        result = app.encode("23/32323", expires="2019-12-10", domain="03")
        print(result)
        decoded = app.decode(result)
        self.assertEqual(decoded['text'], "23/32323")
        self.assertFalse(decoded['expired'])
        self.assertEqual(decoded['expires'], "2019-12-10")
        self.assertEqual(decoded['domain'], 'https://app.careerlyft.com')
        self.assertEqual(
            app.generate_url(decoded, '/resumes/'),
            f'https://app.careerlyft.com/resumes/1575932400000.0/23/32323')


if __name__ == '__main__':
    unittest.main()
