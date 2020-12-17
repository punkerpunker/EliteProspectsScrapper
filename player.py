import uuid
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
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
    name_field = "ep-entity-header__name"
    ep_list = "ep-list"
    stats_table_id = "league-stats"

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

    def get_name(self):
        return self.driver.find_element_by_class_name(self.name_field).text

    def get_personal_info(self):
        info = {}
        ep_list = self.driver.find_element_by_class_name(self.ep_list)
        fields = ep_list.find_elements_by_xpath('.//*')
        fields = [x for x in fields if x.find_element_by_xpath('..').get_attribute('class') == self.ep_list]
        for field in fields:
            key = field.text.split('\n')[0]
            value = field.text.lstrip(key).replace('\n', ',').lstrip(',')
            info[key] = value
        return info

    def get_statistics(self):
        stats_table = self.driver.find_element_by_id(self.stats_table_id)
        table = stats_table.find_element_by_xpath(".//table[contains(@class, player-stats)]")
        stats = pd.read_html(table.get_attribute('outerHTML'))[0]
        stats['S'] = stats['S'].fillna(method='ffill')
        return stats


df = pd.read_csv('source/forwards_clean.csv')
for index, row in df.iterrows():
    player_page = PlayerPage.load(row['url'])
    print(player_page.get_name())
    print(player_page.get_personal_info())
    print(player_page.get_statistics())
    break
