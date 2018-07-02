from __future__ import unicode_literals
from __future__ import absolute_import

import datetime

from django.contrib.gis.geos import Point

from model_mommy.mommy import make
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from oregoninvasiveshotline.tests import FunctionalTestCase
from oregoninvasiveshotline.species.models import Category, Severity, Species
from oregoninvasiveshotline.reports.models import Report
from oregoninvasiveshotline.reports.tests.base import SuppressPostSaveMixin

ORIGIN = Point(0, 0)


def get_report_list_entries(browser):
    return browser.find_elements_by_css_selector('tr.report-list-entry')


def get_report_element_name(report):
    return 'report-list-entry-{}'.format(report.pk)


class ReportSearchFunctionalTestCase(SuppressPostSaveMixin, FunctionalTestCase):
    """
    TBD
    """
    def test_search_order_by(self):
        """
        Validates proper functioning of report list result ordering.
        """
        category = make(Category)
        another_category = make(Category)
        reported_species = make(Species, category=category)
        actual_species = make(Species, category=another_category)

        first_report = make(Report,
                            is_public=True,
                            actual_species=None,
                            reported_species=None,
                            point=ORIGIN)
        second_report = make(Report,
                             is_public=True,
                             actual_species=actual_species,
                             reported_species=reported_species,
                             point=ORIGIN)

        self.login('staff_login')
        self.get('reports-list')
        entries = get_report_list_entries(self.browser)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].get_attribute('id'),
                         get_report_element_name(second_report))

        second_report.created_on = datetime.datetime.now() - datetime.timedelta(days=1)
        second_report.save()
        order_by = self.browser.find_element_by_id('id_orderby_-created_on')
        order_by.click()
        entries = get_report_list_entries(self.browser)
        self.assertEqual(entries[0].get_attribute('id'),
                         get_report_element_name(first_report))
