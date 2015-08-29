"""
My personalized driver
"""
import os
from selenium import webdriver
from pyvirtualdisplay import Display


class LattesDriver(object):

    """This class represents a driver instance."""

    def __init__(self):
        """Constructs a wedbriver with its propers settings."""
        self.profile = webdriver.FirefoxProfile()
        self.profile.set_preference("browser.download.folderList", 2)
        self.profile.set_preference("browser.download.dir",
                                    os.getcwd() + '/xmls/')
        self.profile.set_preference("browser.download.manager.showWhenStarting",
                                    False)
        self.profile.set_preference("browser.helperApps.alwaysAsk.force",
                                    False)
        self.profile.set_preference("browser.helperApps.neverAsk.saveToDisk",
                                    "application/zip")
        display = Display(visible=0, size=(800, 600))
        display.start()
        self.driver = webdriver.Firefox(firefox_profile=self.profile)
        self.driver.implicitly_wait(5)

    def get_driver(self):
        """Returns the created and configured webdriver."""
        return self.driver
