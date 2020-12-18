import uuid
import os
import tqdm
import pandas as pd
import multiprocessing as mp
from multiprocessing import Pool
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from settings import CHROMEDRIVER_PATH


url_file = 'source/forwards_clean.csv'
capabilities = DesiredCapabilities.CHROME
capabilities["pageLoadStrategy"] = "eager"


class Object:
    def __init__(self, **kwargs):
        self.id = str(uuid.uuid4())
        for field in kwargs:
            setattr(self, field, kwargs[field])

    def __repr__(self):
        return str(vars(self))


class Player(Object):
    file = 'Player.csv'

    def __init__(self, url, **kwargs):
        self.url = url
        super().__init__(**kwargs)

    def save(self):
        pd.DataFrame([vars(self)]).to_csv(self.file, header=not os.path.isfile(self.file), mode='a')


class PlayerSeasonStats:
    file = 'PlayerSeasonStats.csv'

    def __init__(self, player_id, stats):
        self.stats = stats
        self.stats['player_id'] = player_id

    def __repr__(self):
        return str(self.stats)

    def save(self):
        self.stats.to_csv(self.file, header=not os.path.isfile(self.file), mode='a')


class PlayerPage:
    name_field = "ep-entity-header__name"
    ep_list = "ep-list"
    stats_table_id = "league-stats"

    def __init__(self, driver):
        self.driver = driver

    @classmethod
    def load(cls, url, headless=True):
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


def gather_player_info(url):
    player_page = PlayerPage.load(url)
    name = player_page.get_name()
    info = player_page.get_personal_info()
    stats = player_page.get_statistics()
    info['name'] = name
    player = Player(url, **info)
    player_season_stats = PlayerSeasonStats(player.id, stats)
    player_season_stats.save()
    player.save()


if __name__ == '__main__':
    df = pd.read_csv('source/forwards_clean.csv')
    num_processes = mp.cpu_count() - 2
    with Pool(num_processes) as p:
        list(tqdm.tqdm(p.imap(gather_player_info, df['url'].tolist()), total=df.shape[0]))

