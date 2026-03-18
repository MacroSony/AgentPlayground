import unittest
from file_tools.weather_tools import get_weather

class TestWeatherTools(unittest.TestCase):
    def test_get_weather_valid_location(self):
        result = get_weather("London")
        self.assertIn("Weather for London", result)
        self.assertIn("Condition:", result)
        self.assertIn("Temperature:", result)
        self.assertIn("Wind Speed:", result)

    def test_get_weather_invalid_location(self):
        result = get_weather("NonExistentCity12345")
        self.assertIn("Error: Location 'NonExistentCity12345' not found.", result)

if __name__ == '__main__':
    unittest.main()
