import argparse
import datetime
import hashlib
import itertools
import os
import random
import re
import sys
import time
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import subprocess


def rand_sleep(max_seconds=5):
    """Pause to avoid spamming requests."""
    seconds = random.randint(2, max_seconds)
    print(f"Sleeping for {seconds} seconds...", end="")
    sys.stdout.flush()
    time.sleep(seconds)
    print("done.")


class AmzChromeDriver:
    """ChromeDriver to login to Amazon and fetch URLs using Selenium."""

    def __init__(self):
        from selenium import webdriver
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(5)

    def login(self, email, password):
        driver = self.driver
        driver.get("https://www.amazon.com.au/")
        rand_sleep()
        driver.find_element(By.CSS_SELECTOR, "#nav-signin-tooltip > a > span").click()
        rand_sleep()
        driver.find_element(By.ID, "ap_email").send_keys(email)

        try:
            driver.find_element(By.ID, "continue").click()
            rand_sleep()
        except NoSuchElementException:
            print("No continue button found; proceeding...")

        driver.find_element(By.ID, "ap_password").send_keys(password)
        driver.find_element(By.ID, "signInSubmit").click()
        time.sleep(10)

    def get_url(self, url):
        """Fetch the page URL, attempt twice."""
        self.driver.get(url)
        time.sleep(1)
        self.driver.get(url)
        return self.driver.page_source

    def clean_up(self):
        self.driver.quit()


class AmzScraper:
    base_url = "https://www.amazon.com.au"
    start_url = base_url + "/gp/css/history/orders/view.html?orderFilter=year-{yr}&startAtIndex=1000"
    order_url = base_url + "/gp/css/summary/print.html/ref=od_aui_print_invoice?ie=UTF8&orderID={oid}"
    order_date_re = re.compile(r"Order Placed:")
    order_id_re = re.compile(r"orderID=([0-9-]+)")

    def __init__(self, year, user, password, dest_dir, brcls=AmzChromeDriver):
        self.year = year
        self.orders_dir = dest_dir
        self.br = brcls()
        self.br.login(user, password)

    def _fetch_url(self, url):
        print(f"Fetching {url}...")
        html = self.br.get_url(url)
        rand_sleep()
        return html

    def get_order_nums(self):
        order_nums = set()
        url = self.start_url.format(yr=self.year)
        for page_num in itertools.count(2):
            html = self._fetch_url(url)
            soup = BeautifulSoup(html, "lxml")
            order_links = soup.find_all("a", href=self.order_id_re)
            order_nums.update(self.order_id_re.search(link["href"]).group(1) for link in order_links)

            if not soup.find_all("a", text=str(page_num)):
                break
            url = self.base_url + soup.find_all("a", text=str(page_num))[0]["href"]

        print(f"Found {len(order_nums)} orders in {self.year}.")
        return order_nums

    def run(self):
        order_nums = self.get_order_nums()
        for oid in order_nums:
            if any(f"{oid}.pdf" in o for o in os.listdir(self.orders_dir)):
                print(f"Skipping order {oid} (already exists).")
                continue

            url = self.order_url.format(oid=oid)
            html = self._fetch_url(url)
            if "Dispatched on" not in html:
                print(f"Skipping order {oid} (not final).")
                continue

            soup = BeautifulSoup(html, "lxml")
            order_txt = soup.find_all(text=self.order_date_re)[0]
            date = order_txt.parent.next_sibling.get_text().strip()
            date = datetime.datetime.strptime(date, "%d %B %Y").strftime("%Y-%m-%d")
            fn = os.path.join(self.orders_dir, f"amazon_order_{date}_{oid}.")

            # Save the HTML file
            with open(fn + "html", "w", encoding="utf-8") as f:
                f.write(html)

            # Convert HTML to PDF using wkhtmltopdf
            subprocess.check_call([
                "wkhtmltopdf",
                "--no-images",
                "--disable-javascript",
                fn + "html",
                fn + "pdf"
            ])

            # Remove the temporary HTML file
            os.remove(fn + "html")


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape an Amazon account and create order PDFs.")
    parser.add_argument("-u", "--user", help="Amazon username (email).", default=os.environ["AMAZON_USER"])
    parser.add_argument("-p", "--password", help="Amazon password.", default=os.environ["AMAZON_PASSWORD"])
    parser.add_argument("--dest-dir", required=False, default="orders/", help='Destination for order PDFs.')
    parser.add_argument("year", nargs="*", type=int, default=[datetime.datetime.today().year],
                        help="Years to scrape orders for.")
    return parser.parse_args()


def main():
    args = vars(parse_args())
    years = args.pop("year")
    for year in years:
        AmzScraper(year=year, **args).run()


if __name__ == "__main__":
    main()
