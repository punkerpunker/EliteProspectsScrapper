import uuid
import tqdm
import pandas as pd
import sqlalchemy
from multiprocessing import Pool
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from settings import CHROMEDRIVER_PATH
from tor import Tor

capabilities = DesiredCapabilities.CHROME
capabilities["pageLoadStrategy"] = "eager"
db_name = 'postgres'
db_hostname = 'localhost'
db_user = 'postgres'
db_password = 'tttBBB777'
db_table = 'players_list'
engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_hostname}/{db_name}')


class Object:
    def __init__(self, **kwargs):
        self.id = str(uuid.uuid4())
        for field in kwargs:
            setattr(self, field, kwargs[field])

    def __repr__(self):
        return str(vars(self))


class Player(Object):
    table = 'player'

    def __init__(self, url, name, **kwargs):
        self.url = url
        self.name = name
        super().__init__(**kwargs)

    def save(self):
        pd.DataFrame([vars(self)]).astype(str).to_sql(self.table, con=engine, index=False, if_exists='append')
        with engine.connect() as con:
            con.execute(f"""UPDATE {db_table} set checked = 1 where url = '{self.url.replace('%', '%%')}'""")


class PlayerSeasonStats:
    table = 'player_season'

    def __init__(self, player_id, stats):
        self.stats = stats
        self.stats['player_id'] = player_id

    def __repr__(self):
        return str(self.stats)

    def save(self):
        self.stats.astype(str).to_sql(self.table, con=engine, index=False, if_exists='append')


class PlayerPage:
    name_field = "ep-entity-header__name"
    ep_list = "ep-list"
    stats_table_id = "league-stats"

    def __init__(self, driver):
        self.driver = driver

    @classmethod
    def load(cls, url, headless=True):
        options = Options()
        options.add_argument('--proxy-server=%s' % Tor.proxies['https'])
        options.headless = headless
        driver = webdriver.Chrome(CHROMEDRIVER_PATH, options=options,
                                  desired_capabilities=capabilities)
        driver.get(url)
        try:
            driver.find_element_by_class_name(cls.name_field)
        except NoSuchElementException:
            raise KeyError("Page not loaded correctly")
        return cls(driver)

    def close(self):
        self.driver.close()
        self.driver.quit()

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
        try:
            stats_table = self.driver.find_element_by_id(self.stats_table_id)
        except NoSuchElementException:
            return None
        table = stats_table.find_element_by_xpath(".//table[contains(@class, player-stats)]")
        stats = pd.read_html(table.get_attribute('outerHTML'))[0]
        stats['S'] = stats['S'].fillna(method='ffill')
        return stats


def gather_player_info(url):
    while True:
        try:
            player_page = PlayerPage.load(url)
            break
        except (KeyError, WebDriverException):
            print(url)
            Tor.renew_connection()
    name = player_page.get_name()
    info = player_page.get_personal_info()
    stats = player_page.get_statistics()
    if stats is not None:
        player = Player(url, name, **info)
        player_season_stats = PlayerSeasonStats(player.id, stats)
        player_season_stats.save()
        player.save()
    player_page.close()


if __name__ == '__main__':
    df = pd.read_sql(f"select url from {db_table} where checked = 0 and url is not NULL", engine)
    num_processes = 10
    with Pool(num_processes) as p:
        list(tqdm.tqdm(p.imap(gather_player_info, df['url'].tolist()), total=df.shape[0]))
