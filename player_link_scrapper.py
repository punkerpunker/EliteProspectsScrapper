from typing import Dict
import sqlalchemy
import pandas as pd
from settings import CHROMEDRIVER_PATH
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

capabilities = DesiredCapabilities.CHROME
capabilities["pageLoadStrategy"] = "eager"
db_name = 'postgres'
db_hostname = 'localhost'
db_user = 'postgres'
db_password = 'Vazhega1'
db_table = 'players_list'


class PlayersSearch:
    url = 'https://www.eliteprospects.com/search/player'
    form_id = "advanced-search"
    load_timeout = 20
    dropdown_filters = ['position', 'gender', 'nation', 'contract', 'secondaryNation',
                        'shoots', 'status', 'height', 'weight', 'draftEligibility']

    def __init__(self, driver):
        self.driver = driver

    @classmethod
    def load(cls, headless=False):
        options = Options()
        options.headless = headless
        driver = webdriver.Chrome(CHROMEDRIVER_PATH, options=options,
                                  desired_capabilities=capabilities)
        try:
            driver.get(cls.url)
        except TimeoutException:
            raise TimeoutException("Page not loaded")
        return cls(driver)

    def get_player_list(self, filters: Dict):
        form = self.driver.find_element_by_id(self.form_id)
        for key, value in filters.items():
            if key in self.dropdown_filters:
                dropdown = Select(form.find_element_by_id(key))
                dropdown.select_by_visible_text(value)
        form.submit()

    def get_page_urls(self):
        wait = WebDriverWait(self.driver, self.load_timeout)
        xpath = "//table[contains(@class, 'table table-condensed table-striped players')]"
        table = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        urls = table.find_elements_by_xpath(".//a[contains(@href, 'player')]")
        players = [x.get_attribute('href') for x in urls]
        return players

    def next_page(self):
        wait = WebDriverWait(self.driver, self.load_timeout)
        xpath = "//div[contains(@class, 'table-pagination')]"
        pagination = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        pagination.find_element_by_link_text("Next page").click()

    def quit(self):
        self.driver.quit()


def save_table(df):
    df['checked'] = 0
    engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_hostname}/{db_name}')
    df.to_sql(db_table, con=engine, index=False)
    with engine.connect() as con:
        con.execute(f"""CREATE INDEX url_index_btree ON {db_table} USING btree(url)""")


if __name__ == '__main__':
    filename = 'forwards.csv'
    p = PlayersSearch.load()
    p.get_player_list({'position': "Forwards"})

    i = 0
    while True:
        urls = pd.DataFrame({'url': p.get_page_urls()})
        print(urls)
        if i == 0:
            urls.to_csv(filename, mode='a', index=False)
            i += 1
        else:
            urls.to_csv(filename, mode='a', index=False, header=False)
        try:
            p.next_page()
        except NoSuchElementException:
            p.quit()
            break
    urls = pd.read_csv(filename)
    save_table(urls)
