import time
import random
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import os


class LinkedInScraper:
    def __init__(self):
        self.config = self.read_config()
        self.data = pd.DataFrame(columns=["profile_url", "name", "location"])
        self.unique_urls = set()
        self.load_existing_data()

    def read_config(self):
        config = {}
        try:
            with open("config.txt", "r") as f:
                for line in f:
                    key, value = line.strip().split(" ", 1)
                    config[key.strip()] = value.strip()
        except FileNotFoundError:
            print("Config file not found. Please create a config.txt file.")
            exit(1)
        except ValueError:
            print(
                "Invalid config file format. Each line should be in the format: key = value"
            )
            exit(1)
        return config

    def scroll_page(self, driver):
        for _ in range(2):
            scroll_amount = random.randint(300, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(1, 3))

    def login(self, driver):
        driver.get("https://www.linkedin.com/login")
        driver.find_element(By.ID, "username").send_keys(self.config["username"])
        driver.find_element(By.ID, "password").send_keys(self.config["password"])
        driver.find_element(By.XPATH, "//*[@type='submit']").click()

    def load_existing_data(self):
        self.load_from_csv()

    def load_from_csv(self):
        file_name = "data.csv"
        if os.path.exists(file_name):
            self.data = pd.read_csv(file_name, delimiter=";")
            self.unique_urls.update(self.data["profile_url"].tolist())

    def scrape_page(self, driver, page_number):
        search_url = self.config["search_url"].format(page_number)
        driver.get(search_url)
        driver.maximize_window()
        print(f"Scraping Page {page_number} data")

        self.scroll_page(driver)

        search = BeautifulSoup(driver.page_source, "lxml")
        peoples = search.findAll("div", class_="mb1")

        new_profiles = 0
        for people in peoples:
            profile_link = people.find("a", class_="app-aware-link")
            if profile_link:
                profile_url = profile_link["href"].split("?")[0]
                if profile_url not in self.unique_urls:
                    self.unique_urls.add(profile_url)
                    name = profile_link.get_text(strip=True).split("View")[0].strip()
                    location_div = people.find(
                        "div", class_="entity-result__secondary-subtitle"
                    )
                    location = (
                        location_div.get_text(strip=True) if location_div else "None"
                    )
                    self.data = self.data.append(
                        {
                            "profile_url": profile_url,
                            "name": name,
                            "location": location,
                        },
                        ignore_index=True,
                    )
                    new_profiles += 1

        print(f"Data scraped successfully! {new_profiles} new profiles added.")
        return new_profiles

    def scrape_data(self):
        driver = webdriver.Safari()
        self.login(driver)

        try:
            for page_number in range(1, 100):
                self.scrape_page(driver, page_number)
        except Exception as e:
            print(f"An error occurred: {e}. Exiting gracefully.")
        finally:
            driver.quit()
            self.write_data()

    def write_data(self):
        self.data.to_csv("data.csv", index=False, sep=";")
        self.data.to_excel("data.xlsx", index=False, sheet_name="Peoples")

    def start(self):
        self.scrape_data()


if __name__ == "__main__":
    scraper = LinkedInScraper()
    scraper.start()
