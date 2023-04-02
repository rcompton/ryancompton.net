import unittest
import assessor_api

class TestAssessorAPI(unittest.TestCase):

    def test_fetch_address_ain(self):
        ain = assessor_api.fetch_address_ain("1543 Euclid St j, Santa Monica, CA 90404, USA")
        self.assertEqual(ain, "4282033015")

        ain = assessor_api.fetch_address_ain("28743 Shire Oaks Dr, Rancho Palos Verdes, CA")
        self.assertEqual(ain, "7585019005")

if __name__ == '__main__':
    unittest.main()
