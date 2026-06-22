import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import config as cfg
import pandas as pd
import time
import re

# configure logging so `logging.info` messages are visible
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)


def main():
    driver = webdriver.Chrome()
    all_records = []

    try:
        driver.get("https://www.angelone.in/stocks")

        wait = WebDriverWait(driver, 20)

        pages_to_scrape = cfg.number_of_pages()
        last_page_scraped = cfg.get_last_page()
        if last_page_scraped >= pages_to_scrape:
            logging.info("All pages already scraped. Exiting.")
            return

        for page in range(last_page_scraped, last_page_scraped + pages_to_scrape):

            logging.info(f"\nProcessing Page {page + 1}")

            # wait until table exists
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "tbody tr")
                )
            )

            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            rows = soup.select("tbody tr")

            logging.info(f"Rows Found: {len(rows)}")

            for row in rows:

                try:

                    company_link = row.select_one("div.A0jEHm a")

                    if not company_link:
                        continue

                    company = company_link.get_text(strip=True)

                    url = company_link.get("href", "")

                    symbol_div = row.select_one("div.u031Rg")

                    symbol = (
                        symbol_div.get_text(strip=True)
                        if symbol_div
                        else ""
                    )

                    # LTP Container
                    price_div = (
                        row.select_one("div.oTmjDz")
                        or row.select_one("div._cJd_o")
                    )

                    ltp = ""
                    change_value = ""
                    change_percent = ""

                    if price_div:

                        for item in price_div.contents:

                            if isinstance(item, str):

                                txt = item.strip()

                                if txt:
                                    ltp = txt
                                    break

                        change_div = price_div.select_one("div.fzL4jb")

                        if change_div:

                            change_text = change_div.get_text(strip=True)

                            match = re.search(
                                r'([-.\d]+)\(([-.\d]+)%\)',
                                change_text
                            )

                            if match:
                                change_value = match.group(1)
                                change_percent = match.group(2)

                    all_records.append({
                        "company": company,
                        "symbol": symbol,
                        "ltp": ltp,
                        "change_value": change_value,
                        "change_percent": change_percent,
                        "url": url,
                        "page_no": page + 1
                    })

                except Exception as e:
                    logging.error(f"Row Error: {e}")

            # Last page? Stop
            try:

                next_button = driver.find_element(
                    By.CSS_SELECTOR,
                    'button[aria-label="Go to next page"]'
                )

                # remember first row before click
                first_row_before = driver.find_element(
                    By.CSS_SELECTOR,
                    "tbody tr"
                ).text

                driver.execute_script(
                    "arguments[0].click();",
                    next_button
                )

                # wait for page change
                wait.until(
                    lambda d:
                    d.find_element(
                        By.CSS_SELECTOR,
                        "tbody tr"
                    ).text != first_row_before
                )

            except Exception:

                logging.info("No more pages available")
                break

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    # Post-processing and safe update of last page
    try:
        cfg.update_last_page(page)
        logging.info(f"Last page scraped: {page}")
    except NameError:
        logging.warning("No page variable available; skipping last page update")
    except Exception as e:
        logging.error(f"Failed to update last page: {e}")

    df = pd.DataFrame(all_records)
    if not df.empty:
        df['run_date'] = pd.to_datetime('today').date()
        logging.info('scraping date {}'.format(df['run_date'].iloc[0]))
    else:
        df['run_date'] = pd.to_datetime('today').date()

    logging.info(f"Total records scraped: {len(df)}")
    df.to_csv("stocks_output.csv", index=False)
    logging.info("Data saved to stocks_output.csv")


if __name__ == '__main__':
    main()