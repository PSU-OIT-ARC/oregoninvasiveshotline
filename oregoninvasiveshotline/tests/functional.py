from __future__ import unicode_literals
from __future__ import absolute_import

import urllib.parse
import os, os.path
import logging

import xvfbwrapper

from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium import webdriver

from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings

from .base import TestCaseMixin

logger = logging.getLogger(__name__)


class WebDriverConfigurationError(Exception):
    """
    TBD
    """

def get_chrome_kwargs():
    if not hasattr(settings, 'WEBDRIVER'):
        msg = "'WEBDRIVER' must be set."
        raise WebDriverConfigurationError(msg)
    return {'executable_path': os.path.join(os.path.dirname(__file__), settings.WEBDRIVER),
            'service_log_path': './chromedriver.log'}


class FunctionalTestCase(TestCaseMixin, StaticLiveServerTestCase):
    login_url_pattern = 'login'
    logout_url_pattern = 'logout'

    btn_cls = 'btn-primary'
    browsers = {
        'chrome': {'capabilities': DesiredCapabilities.CHROME,
                   'driver': webdriver.Chrome,
                   'kwargs': get_chrome_kwargs}
    }

    @classmethod
    def configure_webdriver(cls):
        defs = cls.browsers['chrome']
        if callable(defs['capabilities']):
            defs['capabilities'] = defs['capabilities']()

        webdriver_path = getattr(settings, 'REMOTE_WEBDRIVER', None)
        if webdriver_path is not None:
            msg = "Using REMOTE_WEBDRIVER='%s'"
            logger.info(msg % (settings.REMOTE_WEBDRIVER))
            cls.browser = webdriver.Remote(command_executor=webdriver_path,
                                           desired_capabilities=defs['capabilities'])
        else:
            run_nodisplay = getattr(settings, 'TEST_WEBDRIVER_NO_DISPLAY', True)
            if run_nodisplay:
                logger.info("Running browser in virtual framebuffer")
                cls.display = xvfbwrapper.Xvfb(width=1600, height=1200)
                cls.display.start()
            kwargs = defs['kwargs']
            if callable(kwargs):
                kwargs = kwargs()
            cls.browser = defs['driver'](**kwargs)

    @classmethod
    def setUpClass(cls):
        cls.configure_webdriver()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'display'):
            cls.display.stop()
        cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        self.create_user()

        super().setUp()

    def tearDown(self):
        super().tearDown()

        if self._user_logged_in:
            self.logout()

    def create_user(self):
        password = get_user_model().objects.make_random_password()
        self.user = super().create_user(password=password)
        self.user.is_active = True
        self.user.is_staff = True
        self.user.save()

        self._password = password
        self._user_logged_in = False

    def login(self, mode):
        self.get(self.login_url_pattern)
        username = self.browser.find_element_by_name('username')
        username.send_keys(self.user.email)
        password = self.browser.find_element_by_name('password')
        password.send_keys(self._password)

        self.submit(element_id=mode)
        self._user_logged_in = True

    def logout(self):
        self.get(self.logout_url_pattern)

    def get_submit_button(self, element_id=None, name=None):
        if element_id is not None:
            return self.browser.find_element_by_id(element_id)
        elif name is None:
            return self.browser.find_element_by_class_name(self.btn_cls)
        for element in self.browser.find_elements_by_name(self.btn_cls):
            if element.get_attribute('name') == name:
                return element
        return self.browser.find_element_by_name(name)

    def submit(self, element_id=None, name=None, wait_on_load=True):
        button = self.get_submit_button(element_id=element_id, name=name)
        button.click()

        if wait_on_load:
            self.wait()

    def wait(self, tag_name='body', timeout=1000):
        def test_func(driver):
            return driver.find_element_by_tag_name(tag_name)
        WebDriverWait(self.browser, timeout).until(test_func)

    def wait_for_element_by_id(self, element_id, timeout=500):
        def test_func(driver):
            return driver.find_element_by_id(element_id)
        WebDriverWait(self.browser, timeout).until(test_func)
        return self.browser.find_element_by_id(element_id)

    def wait_element_is_visible(self, element, timeout=500):
        def find_func(driver):
            if not element.is_displayed():
                return False
            return element
        WebDriverWait(self.browser, timeout).until(find_func)

    def wait_element_has_changed(self, element_, attr, value, timeout=1000):
        def test_func(driver):
            element = self.browser.find_element_by_id(element_.get_attribute('id'))
            current_value = type(value)(element.get_attribute(attr))
            return current_value != value
        WebDriverWait(self.browser, timeout).until(test_func)

    def _click_multiple_input(self, type_, name, value):
        selector = "input[type='%s'][name='%s'][value='%s']"
        self.browser.find_element_by_css_selector(
            selector % (type_, name, value)).click()

    def click_radio_button(self, name, value):
        self._click_multiple_input('radio', name, value)

    def click_checkbox(self, name, value):
        self._click_multiple_input('checkbox', name, value)

    def select_chosen_dropdown(self, element_or_id, value, index=1, multiple=False):
        element = element_or_id
        if isinstance(element_or_id, str):
            element = self.browser.find_element_by_id(element_or_id)
        element.click()

        xpath = "//div[@id='%(id)s']/div/div/input"
        if multiple:
            element.click()
            xpath = "//div[@id='%(id)s']/ul/li/input"

        text_input = element.find_element_by_xpath(
            xpath % {'id': element.get_attribute('id')})
        text_input.send_keys(value)

        xpath = "(//div[@id='%(id)s']/div//li[contains(@class,'active-result')]/em)[%(index)d]"
        self.browser.find_element_by_xpath(
            xpath % {'id': element.get_attribute('id'), 'index': index}).click()

    @property
    def request_host(self):
        if hasattr(self, '_request_host') and self._request_host:
            return self._request_host
        request_host = self.live_server_url
        if hasattr(settings, 'REMOTE_WEBDRIVER_REQUEST_ADDRESS'):
            request_host = settings.REMOTE_WEBDRIVER_REQUEST_ADDRESS
            logger.info("Using client request address: %s" % (request_host))
        self._request_host = request_host
        return request_host

    def request(self, pattern, *args, **kwargs):
        path = reverse(pattern, *args, **kwargs)
        return urllib.parse.urljoin(self.request_host, path)

    def get(self, pattern, *args, **kwargs):
        url = self.request(pattern, *args, **kwargs)
        self.browser.get(url)
        self.wait()
        logger.info("Got URL %s - '%s'" % (url, self.browser.title))

    def send_to_input(self, id=None, value=None):
        form_input = self.wait_for_element_by_id(id)
        form_input.send_keys(value)

    def select_chosen_js(self, id=None, value=None):
        js = ("$('#{0}').trigger('mousedown'); "
             "$('#{0} li:contains(\"{1}\")').trigger('mouseup');").format(id, value)
        self.browser.execute_script(js)
