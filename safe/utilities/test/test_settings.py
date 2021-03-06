# coding=utf-8
"""Test for Settings Utilities."""

import unittest
from safe.test.utilities import get_qgis_app
QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()
from PyQt4.QtCore import QSettings
from safe.definitions.constants import zero_default_value, RECENT
from safe.utilities.settings import (
    setting,
    set_setting,
    set_inasafe_default_value_qsetting,
    get_inasafe_default_value_qsetting,
)

__copyright__ = "Copyright 2016, The InaSAFE Project"
__license__ = "GPL version 3"
__email__ = "info@inasafe.org"
__revision__ = '$Format:%H$'


class TestSettings(unittest.TestCase):
    """Test Settings"""

    def setUp(self):
        """Fixture run before all tests"""
        self.qsetting = QSettings('InaSAFETest')
        self.qsetting.clear()

    def tearDown(self):
        """Fixture run after each test"""
        # Make sure it's empty
        self.qsetting.clear()

    def test_get_value(self):
        """Test we can get a value from a QSettings."""
        # The expected type does not match the default value.
        try:
            self.assertEqual(
                'default_value',
                setting('test', 'default_value', bool, self.qsetting))
        except Exception:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

        self.assertEqual(
            'default_value',
            setting('test', 'default_value', str, self.qsetting))

        self.assertIsNone(
            setting('test', None, str, self.qsetting))

        # Without default value.
        self.assertIsNone(setting('test', qsettings=self.qsetting))

    def test_inasafe_default_value_qsetting(self):
        """Test for set and get inasafe_default_value_qsetting."""
        # Make sure it's empty
        self.qsetting.clear()

        female_ratio_key = 'female_ratio'
        real_value = get_inasafe_default_value_qsetting(
            self.qsetting, RECENT, female_ratio_key)
        self.assertEqual(zero_default_value, real_value)

        female_ratio_value = 0.8
        set_inasafe_default_value_qsetting(
            self.qsetting, RECENT, female_ratio_key, female_ratio_value)
        real_value = get_inasafe_default_value_qsetting(
            self.qsetting, RECENT, female_ratio_key)
        self.assertEqual(female_ratio_value, real_value)


if __name__ == '__main__':
    unittest.main()
