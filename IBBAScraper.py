#!/usr/bin/env python3
"""
    *******************************************************************************************
    IBBAScraper: IBBA (International Business Broker Association) Lead Scraper
    Author: Ali Toori, Python Developer [Bot Builder]
    Website: https://boteaz.com
    YouTube: https://youtube.com/@AliToori
    *******************************************************************************************
"""
import os
import re
import random
from time import sleep
import pandas as pd
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from multiprocessing import freeze_support
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service


class IBBAScraper:
    def __init__(self):
        self.PROJECT_ROOT = Path(os.path.abspath(os.path.dirname(__file__)))
        self.file_settings = str(self.PROJECT_ROOT / 'BotRes/Settings.json')
        self.file_companies = self.PROJECT_ROOT / 'BotRes/Companies.csv'
        self.proxies = self.get_proxies()
        self.user_agents = self.get_user_agents()
        self.settings = self.get_settings()
        self.LOGGER = self.get_logger()
        self.logged_in = False
        self.driver = None

    # Get self.LOGGER
    @staticmethod
    def get_logger():
        """
        Get logger file handler
        :return: LOGGER
        """
        logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": False,
            'formatters': {
                'colored': {
                    '()': 'colorlog.ColoredFormatter',  # colored output
                    # --> %(log_color)s is very important, that's what colors the line
                    'format': '[%(asctime)s,%(lineno)s] %(log_color)s[%(message)s]',
                    'log_colors': {
                        'DEBUG': 'green',
                        'INFO': 'cyan',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'bold_red',
                    },
                },
                'simple': {
                    'format': '[%(asctime)s,%(lineno)s] [%(message)s]',
                },
            },
            "handlers": {
                "console": {
                    "class": "colorlog.StreamHandler",
                    "level": "INFO",
                    "formatter": "colored",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "simple",
                    "filename": "IBBAScraper.log",
                    "maxBytes": 5 * 1024 * 1024,
                    "backupCount": 1
                },
            },
            "root": {"level": "INFO",
                     "handlers": ["console", "file"]
                     }
        })
        return logging.getLogger()

    @staticmethod
    def enable_cmd_colors():
        # Enables Windows New ANSI Support for Colored Printing on CMD
        from sys import platform
        if platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    @staticmethod
    def banner():
        pyfiglet.print_figlet(text='____________ IBBAScraper\n', colors='RED')
        print('IBBAScraper: IBBA (International Business Broker Association) Lead Scraper\n'
              'Author: Ali Toori, Python Developer [Bot Builder]\n',
              'Website: https://boteaz.com\n',
              'YouTube: https://youtube.com/@AliToori'
              '************************************************************************')

    def get_settings(self):
        """
        Creates default or loads existing settings file.
        :return: settings
        """
        if os.path.isfile(self.file_settings):
            with open(self.file_settings, 'r') as f:
                settings = json.load(f)
            return settings
        settings = {"Settings": {
            "ThreadsCount": 5
        }}
        with open(self.file_settings, 'w') as f:
            json.dump(settings, f, indent=4)
        with open(self.file_settings, 'r') as f:
            settings = json.load(f)
        return settings

    # Get random user agent
    def get_proxies(self):
        file_proxies = str(self.PROJECT_ROOT / 'BotRes/proxies.txt')
        with open(file_proxies) as f:
            content = f.readlines()
        return [x.strip() for x in content]

    # Get random user agent
    def get_user_agents(self):
        file_uagents = str(self.PROJECT_ROOT / 'BotRes/user_agents.txt')
        with open(file_uagents) as f:
            content = f.readlines()
        return [x.strip() for x in content]

    # Get web driver
    def get_driver(self, proxy=False, headless=False):
        driver_bin = str(self.PROJECT_ROOT / "BotRes/bin/chromedriver.exe")
        service = Service(executable_path=driver_bin)
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--dns-prefetch-disable")
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        prefs = {"directory_upgrade": True,
                 "credentials_enable_service": False,
                 "profile.password_manager_enabled": False,
                 "profile.default_content_settings.popups": False,
                 # "profile.managed_default_content_settings.images": 2,
                 f"download.default_directory": f"{self.directory_downloads}",
                 "profile.default_content_setting_values.geolocation": 2,
                 "profile.managed_default_content_setting_values.images": 2}
        options.add_experimental_option("prefs", prefs)
        options.add_argument(F'--user-agent={self.get_user_agent()}')
        if proxy:
            options.add_argument(f"--proxy-server={self.get_proxy()}")
        if headless:
            options.add_argument('--headless')
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    @staticmethod
    def wait_until_visible(driver, css_selector=None, element_id=None, name=None, class_name=None, tag_name=None, duration=10000, frequency=0.01):
        if css_selector:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
        elif element_id:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.ID, element_id)))
        elif name:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.NAME, name)))
        elif class_name:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.CLASS_NAME, class_name)))
        elif tag_name:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.TAG_NAME, tag_name)))

    def get_lead(self):
        driver = self.get_driver(headless=True)
        base_url = "https://www.ibba.org/state/"
        states = ["florida", "texas", "michigan"]
        for state in states:
            page = requests.get(base_url + state)
            soup = BeautifulSoup(page.content, 'html.parser')
            for i, company_url in enumerate(soup.find_all(name='a', class_='brokers__item--link')):
                print(f'Business URL #: {i}', company_url['href'], '\n')
                driver.get(company_url['href'])
                try:
                    # self.wait_until_visible(driver=driver, css_selector='[class="brokers__profile--leftPhone"]')
                    page_data = requests.get(company_url['href'])
                    soup_data = BeautifulSoup(page_data.content, 'html.parser')
                    name, company_name, address, phone, email = '', '', '', '', ''
                    try:
                        name = soup_data.find('h1', class_="brokers__profile--informationName").get_text().replace('\n',
                                                                                                                   ' ')
                    except:
                        print("Name not found for this lead\n")
                    try:
                        company_name = soup_data.find('div', class_='brokers__profile--leftAddress').find(
                            'span').get_text().replace('\n', ' ')
                    except:
                        print("Company name not found for this lead\n")
                    try:
                        address = soup_data.find('div', class_='brokers__profile--leftCity').get_text().replace('\n',
                                                                                                                '')
                    except:
                        print("Address not found for this lead\n")
                    try:
                        phone = soup_data.find('a', attrs={'href': re.compile("^tel")}).get_text()
                    except:
                        print("Phone not found for this lead\n")
                    try:
                        email = driver.find_elements(By.CSS_SELECTOR, '[class="brokers__profile--leftPhone"]')[
                            1].find_element(By.TAG_NAME, 'a').text
                    except:
                        print("Email not found for this lead\n")
                    # email = email_element.find_element(By.TAG_NAME, 'a').text
                    data_dict = {"Name": name, "Phone Number": phone, "Email": email, "Company Name": company_name,
                                 "Address": address}
                    print(data_dict)
                    df = pd.DataFrame([data_dict])
                    # if file does not exist write headers
                    if not os.path.isfile(self.file_phone_numbers):
                        df.to_csv(self.file_companies, index=False)
                    else:  # else if exists, append without writing the headers
                        df.to_csv(self.file_companies, mode='a', header=False, index=False)
                    print(f'Leads saved successfully')
                except:
                    pass

    def main(self):
        freeze_support()
        self.enable_cmd_colors()
        self.banner()
        self.LOGGER.info(f'IBBAScraper launched')
        self.get_lead()


if __name__ == '__main__':
    IBBAScraper().main()