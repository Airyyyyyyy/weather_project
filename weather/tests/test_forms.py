from django.test import SimpleTestCase

from weather.forms import CityForm


class CityFormTests(SimpleTestCase):
    def test_valid_city_name(self):
        form = CityForm(data={'name': 'London'})
        self.assertTrue(form.is_valid())

    def test_blank_name_is_invalid(self):
        form = CityForm(data={'name': ''})
        self.assertFalse(form.is_valid())

    def test_name_strips_are_not_enforced_by_form(self):
        # Whitespace trimming happens in the view, not the form itself.
        form = CityForm(data={'name': '  Paris  '})
        self.assertTrue(form.is_valid())

    def test_max_length_boundary(self):
        form = CityForm(data={'name': 'a' * 100})
        self.assertTrue(form.is_valid())

        form = CityForm(data={'name': 'a' * 101})
        self.assertFalse(form.is_valid())