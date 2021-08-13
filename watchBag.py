import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from twilio.rest import Client
import logging
import random
import secrets  # from secrets.py in this folder
BAG_MODEL = "N41605"
LV_BASE_URL = "https://us.louisvuitton.com/eng-us/homepage"
BAG_URL = "https://us.louisvuitton.com/eng-us/products/neverfull-mm-damier-azur-canvas-008109#N41605"


def random_sleep(base_time=1, upper_bound=10):
    time.sleep(base_time + random.randint(0, 10))


def visit_homepage_and_nav_to_bag_and_check_avail():
    is_available = False

    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    # options.add_argument("--no-sandbox")
    # options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    try:
        logging.debug("Navigating to homepage...")
        driver.get(LV_BASE_URL)
        random_sleep()
        logging.debug("On homepage, finding search box....")
        search_box = driver.find_element_by_id("searchHeaderInput")
        if search_box:
            logging.debug("Found search box, entering text...")
            search_box.clear()
            search_box.click()
            search_box.send_keys(BAG_MODEL)
            search_box.send_keys(Keys.ENTER)

            if BAG_MODEL in driver.title:
                logging.debug("On target bag page. Title is {}".format(driver.title))
                random_sleep()

                stock_span = driver.find_element_by_class_name("lv-stock-indicator")

                if stock_span:
                    logging.debug("Found stock span")
                    div_text = stock_span.text
                    if "Out" in div_text:
                        logging.debug("Item determined to be unavailable based on div text '{}'".format(div_text))
                    elif "Information Not Available" in div_text:
                        logging.warning("Unable to determine stock status from text '{}'".format(div_text))
                    else:
                        logging.info("Item determined to be available based on div text '{}'".format(div_text))
                        is_available = True
                else:
                    logging.warning("Did not find stock span, make sure this is correct....")
            else:
                logging.warning("Did not make it to the desired bag page. Current page title is '{}'".format(driver.title))
        else:
            logging.warning("Could not find search box...")
    except Exception as e:
        logging.error("Caught exception trying to determine bag status", e)
    finally:
        driver.close()

    return is_available


def setup_twilio_client():
    account_sid = secrets.TWILIO_ACCOUNT_SID
    auth_token = secrets.TWILIO_AUTH_TOKEN
    return Client(account_sid, auth_token)


def send_in_stock_notification():
    try:
        twilio_client = setup_twilio_client()
        twilio_client.messages.create(
            body="Your item is available for purchase: {}".format(BAG_URL),
            from_=secrets.TWILIO_FROM_NUMBER,
            to=secrets.MY_PHONE_NUMBER
        )
    except Exception as e:
        logging.error("Unable to send SMS notification", e)


def send_start_up_notification():
    try:
        twilio_client = setup_twilio_client()
        twilio_client.messages.create(
            body="Starting up Louis Vitton Bag watcher".format(BAG_URL),
            from_=secrets.TWILIO_FROM_NUMBER,
            to=secrets.MY_PHONE_NUMBER
        )
    except Exception as e:
        logging.error("Unable to send SMS notification", e)


def check_inventory():
    if visit_homepage_and_nav_to_bag_and_check_avail():
        logging.info("!!!!!!!!!!!!!!!Bag is available!!!!!!!!!!!!!")
        send_in_stock_notification()


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    count_check = 0
    logging.info("Starting script to check for availability of bag '{}'".format(BAG_MODEL))
    send_start_up_notification()
    random_sleep(30)
    while True:
        logging.debug("Checking site for stock...")
        check_inventory()

        count_check = count_check + 1
        if count_check % 10 == 0:
            logging.info("Checked site {:,} times so far".format(count_check))
        else:
            logging.debug("Checked site {:,} times so far".format(count_check))

        random_sleep(30, 90)
