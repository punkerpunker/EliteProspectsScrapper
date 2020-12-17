import uuid
import pandas as pd
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from settings import CHROMEDRIVER_PATH


url_file = 'source/forwards_clean.csv'
capabilities = DesiredCapabilities.CHROME
capabilities["pageLoadStrategy"] = "eager"


class Object:
    fields = []

    def __init__(self, **kwargs):
        self.id = str(uuid.uuid4())
        for field in kwargs:
            if field in self.fields:
                setattr(self, field, kwargs[field])

    def __repr__(self):
        return str(vars(self))


class Player(Object):
    file = 'Player.csv'

    def __init__(self, url, **kwargs):
        self.url = url
        super().__init__(**kwargs)


class PlayerRegularSeasonStats(Object):
    file = 'PlayerRegularSeasonStats.csv'

    def __init__(self, player_id, **kwargs):
        self.player_id = player_id
        super().__init__(**kwargs)


class PlayerPage:
    ep_list = "ep-list"

    def __init__(self, driver):
        self.driver = driver

    @classmethod
    def load(cls, url, headless=False):
        options = Options()
        options.headless = headless
        driver = webdriver.Chrome(CHROMEDRIVER_PATH, options=options,
                                  desired_capabilities=capabilities)
        driver.get(url)
        return cls(driver)

    def get_personal_info(self):
        info = {}
        ep_list = self.driver.find_element_by_class_name(self.ep_list)
        fields = ep_list.find_elements_by_xpath('.//*')
        fields = [x for x in fields if x.find_element_by_xpath('..').get_attribute('class') == self.ep_list]
        for field in fields:
            key = field.text.split('\n')[0]
            value = field.text.split('\n')[1]
            info[key] = value
        return info


df = pd.read_csv('source/forwards_clean.csv')
uri = df.loc[0, 'url']
player_page = PlayerPage.load(uri)
print(player_page.get_personal_info())
