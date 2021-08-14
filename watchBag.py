import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from twilio.rest import Client
import logging
import random
import secrets  # from secrets.py in this folder

MAIN_SECTIONS = ["NEW", "WOMEN", "MEN"]
BAG_MODEL = "N41605"
LV_BASE_URL = "https://us.louisvuitton.com/eng-us/homepage"
BAG_URL = "https://us.louisvuitton.com/eng-us/products/neverfull-mm-damier-azur-canvas-008109#N41605"


def random_sleep(base_time=1, upper_bound=10):
    time.sleep(base_time + random.randint(0, upper_bound))


def init_webdriver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    # options.add_argument("--no-sandbox")
    # options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    return driver


def visit_homepage_and_nav_to_bag_and_check_avail(driver):
    is_available = False

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
                        logging.info("Item determined to be unavailable based on div text '{}'".format(div_text))
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

    return is_available


def visit_random_item(driver):
    try:
        logging.debug("Starting up some random navigation to try and fool LV bot detection...")
        section_to_visit = MAIN_SECTIONS[random.randint(0, len(MAIN_SECTIONS)-1)]
        logging.debug("Navigating to main section '{}'".format(section_to_visit))

        driver.get(LV_BASE_URL)
        random_sleep()
        logging.debug("On homepage, finding main section list....")
        header_element = driver.find_element_by_id("header")

        if header_element:
            logging.debug("Found header element")
            nav_elements = header_element.find_elements_by_class_name("lv-header-main-nav__item")

            if nav_elements:
                for element in nav_elements:
                    if element.tag_name == "button" and element.text == section_to_visit:
                        logging.debug("Found desired nav button: '{}', clicking it...".format(section_to_visit))
                        element.click()
                        random_sleep(3, 3)
                        logging.debug("Finding all elements we can click on...")
                        nav_panel_elements = header_element.find_elements_by_class_name("lv-header-main-nav-panel")
                        if nav_panel_elements:
                            for ele in nav_panel_elements:
                                if "none" not in ele.get_attribute("style"):
                                    buttons = ele.find_elements_by_tag_name("button")
                                    logging.debug("Found visible ele with {} buttons".format(len(buttons)))
                                    button_to_click = random.randint(0, len(buttons)-1)
                                    logging.debug("Clicking button '{}' with ID '{}'".format(buttons[button_to_click].text, buttons[button_to_click].get_attribute("id")))
                                    buttons[button_to_click].click()
                                    random_sleep(3, 3)
                                    content_element_id = buttons[button_to_click].get_attribute("id").replace("button", "content")
                                    logging.debug("Now finding actual content to click on for ID '{}'".format(content_element_id))

                                    content_element = header_element.find_element_by_id(content_element_id)
                                    if content_element:
                                        logging.debug("Found content element for button '{}'".format(buttons[button_to_click].text))
                                        logging.debug("Finding all buttons in the content element '{}'...".format(content_element.get_attribute("id")))
                                        content_buttons = content_element.find_elements_by_class_name("lv-smart-link")
                                        if content_buttons:
                                            content_button_to_click = random.randint(0, len(content_buttons)-1)
                                            logging.debug("Found {} content buttons, clicking button '{}'".format(len(content_buttons), content_buttons[content_button_to_click].text))
                                            content_buttons[content_button_to_click].click()
                                            random_sleep(3, 3)
                                            logging.debug("Now do some scrolling....")
                                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                            logging.info("Navigated to page with title '{}'".format(driver.title))
                                            random_sleep()
                        break
        else:
            logging.warning("Could not find main nav list elements")
    except Exception as e:
        logging.error("Caught exception trying to navigate...somewhere. Continuing on.")


def setup_twilio_client():
    account_sid = secrets.TWILIO_ACCOUNT_SID
    auth_token = secrets.TWILIO_AUTH_TOKEN
    return Client(account_sid, auth_token)


def send_in_stock_notification():
    try:
        twilio_client = setup_twilio_client()
        msg = "Your item is available for purchase: {}".format(BAG_URL)
        twilio_client.messages.create(
            body=msg,
            from_=secrets.TWILIO_FROM_NUMBER,
            to=secrets.PHONE_NUMBER_1
        )
        twilio_client.messages.create(
            body=msg,
            from_=secrets.TWILIO_FROM_NUMBER,
            to=secrets.PHONE_NUMBER_2
        )
    except Exception as e:
        logging.error("Unable to send SMS notification", e)


def send_start_up_notification():
    random_sleep(30)
    try:
        twilio_client = setup_twilio_client()
        twilio_client.messages.create(
            body="Starting up Louis Vitton Bag watcher",
            from_=secrets.TWILIO_FROM_NUMBER,
            to=secrets.PHONE_NUMBER_1
        )

        twilio_client.messages.create(
            body="Starting up Louis Vitton Bag watcher",
            from_=secrets.TWILIO_FROM_NUMBER,
            to=secrets.PHONE_NUMBER_2
        )
    except Exception as e:
        logging.error("Unable to send SMS notification", e)


def check_inventory(driver):
    if visit_homepage_and_nav_to_bag_and_check_avail(driver):
        logging.info("!!!!!!!!!!!!!!!Bag is available!!!!!!!!!!!!!")
        send_in_stock_notification()


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    count_check = 0
    logging.info("Starting script to check for availability of bag '{}'".format(BAG_MODEL))
    send_start_up_notification()

    driver = init_webdriver()
    while True:
        rand_pages_visited = 0
        num_pages_to_visit = random.randint(2, 5)
        logging.info("Doing some navigation to {} random pages".format(num_pages_to_visit))

        while rand_pages_visited < num_pages_to_visit:
            visit_random_item(driver)
            random_sleep(3, 5)
            rand_pages_visited = rand_pages_visited + 1

        logging.info("Checking site for stock of '{}'...".format(BAG_MODEL))
        check_inventory(driver)

        count_check = count_check + 1
        if count_check % 10 == 0:
            logging.info("Checked for in-stock status {:,} times so far".format(count_check))
        else:
            logging.debug("Checked or in-stock status {:,} times so far".format(count_check))

        random_sleep(20, 30)
