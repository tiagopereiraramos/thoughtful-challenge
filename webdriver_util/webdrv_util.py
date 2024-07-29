import difflib
import os
import random
import re
import traceback
from Log.logs import Logs
from dotenv import load_dotenv
from RPA.Browser.Selenium import Selenium
from time import sleep
from selenium.common import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    JavascriptException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from helpers.selector import Selector
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta


# Personal library with Selenium methods for better web scraping.
load_dotenv("config/.env")
logger = Logs.Returnlog(os.getenv("name_app"), "Scraping")

TIMEOUT = 5
RETRYATTEMPTS = 2


def parse_time_ago(text) -> datetime | None:
    """
    Parses a time string like "1h" or "1m" and returns a datetime object.

    Args:
        text (str): The text to be parsed.

    Returns:
        datetime: The parsed datetime or None if not found or error.
    """
    pattern = r"(\d+)\s+(hour|minute)s?\s+ago"
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        logger.error("Pattern not found in the provided string.")
        return None

    value, unit = match.groups()
    value = int(value)

    now = datetime.now()

    if "hour" in unit:
        result_time = now - timedelta(hours=value)
    elif "minute" in unit:
        result_time = now - timedelta(minutes=value)
    else:
        raise ValueError("Unrecognized time unit.")

    return result_time


def wait_for_modal(driver, timeout=15, search_click=True):
    """
    Waits for a modal to close. This is a blocking function that scrolls down to activate the modal and waits for it to close.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        timeout (int): The number of seconds to wait before timing out.
        search_click (bool): Whether or not to search for the modal.

    Returns:
        bool: True if the modal was closed, False otherwise.
    """
    driver.execute_script("document.body.innerHTML += '';")
    logger.info("Modal closed.")
    return True


def extract_names_from_list_items(driver):
    """
    Returns the elements of a list containing the types of the list.

    Args:
        driver (WebDriver): The WebDriver object.

    Returns:
        list: A list of names.
    """
    spans = driver.driver.find_elements(
        By.XPATH, "//div[@class='search-filter-menu-wrapper']//li//span"
    )
    names = [span.text for span in spans if span.text.strip()]

    return names


def search_and_click_topics(driver, names: list, target_name):
    """
    Search and click topics. This is a helper function for find_fuzzy.

    Args:
        driver (WebDriver): The Selenium driver.
        names (list): List of topics to search.
        target_name (str): Name of the topic to click.

    Returns:
        tuple: (bool, bool) indicating if topics were found and clicked.
    """
    best_match_name = find_fuzzy(names, lambda x: x, target_name)

    if not len(best_match_name.strip()) > 0:
        logger.error(f"Topic not found '{target_name}'.")
        return False, True
    else:
        try:
            span = find_element(
                driver,
                Selector(
                    xpath=f"//div[@class='search-filter-menu-wrapper']//li//span[text()='{best_match_name}']"
                ),
            )

            span.click()
            logger.info(f"Element '{best_match_name}' was clicked.")
            return True, True
        except NoSuchElementException:
            print(f"Element '{best_match_name}' not found.")
            return False, False


def get_driver(site_url: str, headless: bool = False) -> Selenium | None:
    """
    Returns a Selenium object to interact with the site. It is used for testing purposes.

    Args:
        site_url (str): URL of the site to connect to.
        headless (bool): True if you want to use headless mode.
        use_proxy (bool): True if you want to use a proxy.

    Returns:
        Selenium | None: Instance of Selenium that is ready to interact, or None if an error occurs.
    """
    try:
        # Create a new Selenium browser instance
        browser = Selenium()
        logger.info("Creating browser object")

        # Set up Chrome options
        options = Options()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-infobars")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        # Add headless mode options if required
        if headless:
            options.add_argument("--headless")
            options.add_argument(
                "--disable-gpu"
            )  # Necessary to work around a bug in headless mode
            options.add_argument("--disable-extensions")

        # Open the browser and navigate to the site
        browser.open_browser(url="about:blank", browser="chrome", options=options)
        browser.maximize_browser_window()
        browser.set_selenium_page_load_timeout(60)
        browser.set_browser_implicit_wait(3)
        logger.info(f"Accessing the site: {site_url}")
        browser.go_to(url=site_url)
        browser.delete_all_cookies()

        # Execute JavaScript to remove the webdriver property
        browser.driver.execute_script(
            'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        )

        # Set a custom user agent if not in headless mode
        if not headless:
            browser.execute_cdp(
                "Network.setUserAgentOverride",
                {
                    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117.0.0.0 Safari/537.36"
                },
            )

        logger.info(browser.execute_javascript("return navigator.userAgent;"))
        return browser

    except WebDriverException as e:
        logger.error(f"WebDriverException encountered: {traceback.format_exc()}")
        return None
    except Exception as e:
        logger.error(f"An error occurred in get_driver: {traceback.format_exc()}")
        return None


def normalize(t: str) -> str:
    """
    Normalizes a string by converting it to lowercase and stripping leading and trailing whitespace.

    Args:
        t (str): The string to normalize.

    Returns:
        str: The normalized string.
    """
    return t.lower().strip()


def center_element(driver, elm):
    """
    Centers an element on the page.
    """
    if elm:
        driver.execute_script(
            "arguments[0].scrollIntoView({'block':'center','inline':'center'})", elm
        )
    return elm


def slow_send_keys(el, text, unfocus_on_complete=True):
    """
    Sends keys to an element slowly, one character at a time. There will be a random delay between each character.
    This is useful to avoid bot detection when inserting text into a field.

    Args:
        el (WebElement): Selenium element.
        text (str): Text to insert.
        unfocus_on_complete (bool): Whether to unfocus the element on completion.
    """
    if el:
        el.click()
        try:
            el.clear()
        except:
            pass
        for c in text:
            el.send_keys(c)
            sleep(0.03 * random.uniform(0.9, 1.2))

        if unfocus_on_complete:
            el.send_keys(Keys.TAB)


def js_click(driver, elm):
    """
    Clicks an element with JavaScript. Useful for elements that are not clickable or displayed.

    Args:
        driver (WebDriver): Chrome driver.
        elm (WebElement): Selenium element.

    Returns:
        WebElement: The clicked element.
    """
    try:
        if elm:
            driver.execute_script("arguments[0].click();", elm)
        return elm
    except ElementClickInterceptedException:
        logger.error(
            "Element click was intercepted. Ensure the element is visible and clickable."
        )
    except ElementNotInteractableException:
        logger.error(
            "Element is not interactable. Ensure the element is visible and enabled."
        )
    except JavascriptException:
        logger.error(
            "JavaScript execution failed. Check the JavaScript code and element state."
        )
    except NoSuchElementException:
        logger.error(
            "No such element found for clicking. Verify the selector and element presence."
        )
    except TimeoutException:
        logger.error("Operation timed out while trying to click the element.")
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
    return None


def click_elm(driver, elm, timeout=TIMEOUT):
    """
    Attempts to click an element using WebDriverWait to ensure it is clickable.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        elm (WebElement): The WebElement to be clicked.
        timeout (int): The maximum time to wait for the element to be clickable.

    Returns:
        None: Returns None if the element could not be clicked or an exception occurred.

    Raises:
        ElementClickInterceptedException: If the click was intercepted by another element.
        ElementNotInteractableException: If the element is not interactable.
        JavascriptException: If a JavaScript error occurs.
        NoSuchElementException: If the element could not be found.
        TimeoutException: If the click operation times out.
        WebDriverException: If an unexpected WebDriver error occurs.
        Exception: If any other unexpected error occurs.
    """
    try:
        label = "Trying to click"

        def get():
            return [
                WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(elm))
            ]

        element_to_click = find_it(driver, elements=get, timeout=timeout, label=label)
        if element_to_click:
            return element_to_click.click()
        else:
            return None
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return None
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return None
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return None


def find_with_label(driver, tag, label, timeout=TIMEOUT):
    """
    Finds an element by its tag and aria-label attribute.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        tag (str): The HTML tag of the element to find.
        label (str): The value of the aria-label attribute to match.
        timeout (int): The maximum time to wait for the element to be found.

    Returns:
        WebElement: The found WebElement if successful, None otherwise.

    Raises:
        ElementClickInterceptedException: If the click was intercepted by another element.
        ElementNotInteractableException: If the element is not interactable.
        JavascriptException: If a JavaScript error occurs.
        NoSuchElementException: If the element could not be found.
        TimeoutException: If the find operation times out.
        WebDriverException: If an unexpected WebDriver error occurs.
        Exception: If any other unexpected error occurs.
    """
    try:
        return find_with_attribute(driver, tag, "aria-label", label, timeout)
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return None
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return None
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return None


def find_all_with_attribute(driver, tag, attr, value, timeout=TIMEOUT):
    """
    Finds all elements with a specified tag and attribute value.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        tag (str): The HTML tag of the elements to find.
        attr (str): The attribute to match.
        value (str): The value of the attribute to match.
        timeout (int): The maximum time to wait for the elements to be found.

    Returns:
        list[WebElement]: A list of found WebElements if successful, None otherwise.

    Raises:
        ElementClickInterceptedException: If the click was intercepted by another element.
        ElementNotInteractableException: If the element is not interactable.
        JavascriptException: If a JavaScript error occurs.
        NoSuchElementException: If the elements could not be found.
        TimeoutException: If the find operation times out.
        WebDriverException: If an unexpected WebDriver error occurs.
        Exception: If any other unexpected error occurs.
    """
    try:
        target = normalize(value)
        return [
            e
            for e in WebDriverWait(driver, timeout).until(
                EC.visibility_of_any_elements_located((By.TAG_NAME, tag))
            )
            if e.get_attribute(attr) and (target in normalize(e.get_attribute(attr)))
        ]
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return None
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return None
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return None


def find_all_elm_with_attribute(elm: WebElement, tag, attr, value, timeout=TIMEOUT):
    """
    Finds all elements within a parent element by a specified tag and attribute value.

    Args:
        elm (WebElement): The parent WebElement.
        tag (str): The HTML tag of the elements to find.
        attr (str): The attribute to match.
        value (str): The value of the attribute to match.
        timeout (int): The maximum time to wait for the elements to be found.

    Returns:
        list[WebElement]: A list of found WebElements if successful, None otherwise.

    Raises:
        ElementClickInterceptedException: If the click was intercepted by another element.
        ElementNotInteractableException: If the element is not interactable.
        JavascriptException: If a JavaScript error occurs.
        NoSuchElementException: If the elements could not be found.
        TimeoutException: If the find operation times out.
        WebDriverException: If an unexpected WebDriver error occurs.
        Exception: If any other unexpected error occurs.
    """
    try:
        target = normalize(value)
        return [
            e
            for e in elm.find_elements(By.TAG_NAME, tag)
            if e.get_attribute(attr) and (target in normalize(e.get_attribute(attr)))
        ]
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return None
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return None
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return None


def find_elm_picture(elm: WebElement, selector: Selector, timeout=TIMEOUT):
    """
    Finds an image element by CSS selector within a parent element and returns its 'src' attribute.

    Args:
        elm (WebElement): The parent WebElement.
        selector (Selector): The CSS selector to locate the image.
        timeout (int): The maximum time to wait for the element to be found.

    Returns:
        str: The 'src' attribute of the image element if found, None otherwise.

    Raises:
        NoSuchElementException: If the element could not be found.
        TimeoutException: If the find operation times out.
        WebDriverException: If an unexpected WebDriver error occurs.
        Exception: If any other unexpected error occurs.
    """
    try:
        logger.debug(f"Trying to find: {selector.css}")
        sleep(0.2)
        e = WebDriverWait(elm, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, selector.css))
        )
        if e:
            str_picture = e.get_attribute("src")
            sleep(0.4)
            return str_picture
    except (NoSuchElementException, TimeoutException):
        logger.debug(f"Not Found: {selector.css}")
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")


def find_with_attribute(driver, tag, attr, value, timeout=TIMEOUT):
    """
    Finds an element by tag and attribute value using a custom find function.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        tag (str): The HTML tag of the element to find.
        attr (str): The attribute to match.
        value (str): The value of the attribute to match.
        timeout (int): The maximum time to wait for the element to be found.

    Returns:
        WebElement: The found WebElement if successful, None otherwise.

    Raises:
        ElementClickInterceptedException: If the click was intercepted by another element.
        ElementNotInteractableException: If the element is not interactable.
        JavascriptException: If a JavaScript error occurs.
        NoSuchElementException: If the element could not be found.
        TimeoutException: If the find operation times out.
        WebDriverException: If an unexpected WebDriver error occurs.
        Exception: If any other unexpected error occurs.
    """
    try:
        label = "find_with_attribute %s %s %s" % (tag, attr, value)
        return find_it(
            driver,
            lambda: find_all_with_attribute(driver, tag, attr, value),
            timeout=timeout,
            label=label,
        )
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return None
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return None
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return None


def find_with_text(driver, tag, text, timeout=TIMEOUT):
    """
    Finds an element by tag and inner text using a custom find function.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        tag (str): The HTML tag of the element to find.
        text (str): The text content to match.
        timeout (int): The maximum time to wait for the element to be found.

    Returns:
        WebElement: The found WebElement if successful, None otherwise.

    Raises:
        ElementClickInterceptedException: If the click was intercepted by another element.
        ElementNotInteractableException: If the element is not interactable.
        JavascriptException: If a JavaScript error occurs.
        NoSuchElementException: If the element could not be found.
        TimeoutException: If the find operation times out.
        WebDriverException: If an unexpected WebDriver error occurs.
        Exception: If any other unexpected error occurs.
    """
    try:
        target = normalize(text)
        label = "find_with_text %s %s" % (tag, target)

        def get():
            return [
                e
                for e in WebDriverWait(driver, timeout).until(
                    EC.visibility_of_any_elements_located((By.TAG_NAME, tag))
                )
                if target in normalize(e.text)
            ]

        return find_it(driver, get, timeout=timeout, label=label)
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return None
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return None
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return None


def find_css_with_text(driver, css_selector, text, timeout=TIMEOUT):
    """
    Finds an element by CSS selector and inner text using a custom find function.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        css_selector (str): The CSS selector of the element to find.
        text (str): The text content to match.
        timeout (int): The maximum time to wait for the element to be found.

    Returns:
        WebElement: The found WebElement if successful, None otherwise.

    Raises:
        ElementClickInterceptedException: If the click was intercepted by another element.
        ElementNotInteractableException: If the element is not interactable.
        JavascriptException: If a JavaScript error occurs.
        NoSuchElementException: If the element could not be found.
        TimeoutException: If the find operation times out.
        WebDriverException: If an unexpected WebDriver error occurs.
        Exception: If any other unexpected error occurs.
    """
    try:
        target = normalize(text)
        label = f"find_css_with_text {css_selector} {target}"

        def get():
            return [
                e
                for e in WebDriverWait(driver, timeout).until(
                    EC.visibility_of_any_elements_located(
                        (By.CSS_SELECTOR, css_selector)
                    )
                )
                if target in normalize(e.text)
            ]

        return find_it(driver, get, timeout=timeout, label=label)
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return None
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return None
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return None


def find_css(driver, css_selector, timeout=TIMEOUT):
    """
    Finds an element by CSS selector using a custom find function.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        css_selector (str): The CSS selector of the element to find.
        timeout (int): The maximum time to wait for the element to be found.

    Returns:
        WebElement: The found WebElement if successful, None otherwise.

    Raises:
        ElementClickInterceptedException: If the click was intercepted by another element.
        ElementNotInteractableException: If the element is not interactable.
        JavascriptException: If a JavaScript error occurs.
        NoSuchElementException: If the element could not be found.
        TimeoutException: If the find operation times out.
        WebDriverException: If an unexpected WebDriver error occurs.
        Exception: If any other unexpected error occurs.
    """
    try:
        label = "find_css %s" % css_selector

        def get():
            return [
                e
                for e in WebDriverWait(driver, timeout).until(
                    EC.visibility_of_any_elements_located(
                        (By.CSS_SELECTOR, css_selector)
                    )
                )
            ]

        return find_it(driver, elements=get, timeout=timeout, label=label)
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return None
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return None
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return None


def find_all_css(driver: WebDriver, css_selector, timeout=TIMEOUT):
    """
    Finds all elements by CSS selector.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        css_selector (str): The CSS selector of the elements to find.
        timeout (int): The maximum time to wait for the elements to be found.

    Returns:
        list[WebElement]: A list of found WebElements if successful, None otherwise.

    Raises:
        ElementClickInterceptedException: If the click was intercepted by another element.
        ElementNotInteractableException: If the element is not interactable.
        JavascriptException: If a JavaScript error occurs.
        NoSuchElementException: If the elements could not be found.
        TimeoutException: If the find operation times out.
        WebDriverException: If an unexpected WebDriver error occurs.
        Exception: If any other unexpected error occurs.
    """
    try:
        return driver.find_elements(By.CSS_SELECTOR, css_selector)
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return None
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return None
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return None


def find_element(
    driver: WebDriver, selectors: Selector | list[Selector], timeout: int = TIMEOUT
) -> WebElement | None:
    """
    Find an element by CSS, text, or XPath. If a list of selectors is provided, it will try to find the first one that matches.

    Args:
        driver (WebDriver): Chrome driver.
        selectors (Selector | list[Selector]): List of Selectors.
        timeout (int): Timeout in seconds.

    Returns:
        WebElement: The element if found, None otherwise.
    """
    if not isinstance(selectors, list):
        selectors = [selectors]

    for selector in selectors:
        elm = None
        logger.debug(f"Trying to find {selector.css}")
        try:
            if selector.xpath:
                elm = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located(locator=[By.XPATH, selector.xpath])
                )
            elif selector.css and selector.attr:
                attr, value = selector.attr
                elm = find_with_attribute(driver, selector.css, attr, value, TIMEOUT)
            elif selector.css and selector.text:
                elm = find_css_with_text(
                    driver, selector.css, selector.text, timeout=TIMEOUT
                )
            elif selector.css:
                elm = find_css(driver, selector.css, timeout=TIMEOUT)
            if elm:
                logger.debug(f"Found element: {elm}")
                return elm
        except NoSuchElementException:
            logger.warning(f"Element not found using selector: {selector}")
        except TimeoutException:
            logger.warning(
                f"Timeout while waiting for element with selector: {selector}"
            )
        except Exception as e:
            logger.critical(f"Unexpected error occurred while finding element: {e}")


def find_elements(
    driver: WebDriver, selectors: Selector | list[Selector], timeout: int = TIMEOUT
) -> WebElement | None:
    """
    Find elements on a web page based on the provided selectors.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        selectors (Selector | list[Selector]): The selector or list of selectors to locate the elements.
        timeout (int): The maximum time to wait for the elements to be located (default is TIMEOUT).

    Returns:
        WebElement | None: The located elements or None if no elements are found.
    """
    try:
        if not isinstance(selectors, list):
            selectors = [selectors]

        for selector in selectors:
            elm = None
            logger.debug(f"Trying to find {selector.css}")
            try:
                if selector.xpath:
                    elm = WebDriverWait(driver, timeout).until(
                        EC.presence_of_all_elements_located((By.XPATH, selector.xpath))
                    )
                elif selector.css and selector.attr:
                    attr, value = selector.attr
                    elm = find_with_attribute(
                        driver, selector.css, attr, value, timeout
                    )
                elif selector.css and selector.text:
                    elm = find_css_with_text(
                        driver, selector.css, selector.text, timeout
                    )
                elif selector.css:
                    elm = find_all_css(driver, selector.css, timeout)
                if elm:
                    logger.debug(f"Found element: {elm}")
                    return elm
            except (TimeoutException, NoSuchElementException):
                continue
        return None
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return None
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return None
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return None


def select_option(select, option, to_string):
    """
    Select an option from a dropdown menu by matching it with the given value.

    Args:
        select: The dropdown WebElement to interact with.
        option: The option to select.
        to_string: A function to extract a string from an option element for comparison.

    Returns:
        bool: True if the option was successfully selected, False otherwise.
    """
    try:
        if not select:
            return False
        retry(select.click)
        sleep(0.5)

        possible_options = sorted(
            select.find_elements(By.TAG_NAME, "option"),
            key=lambda op: difflib.SequenceMatcher(
                None, normalize(to_string(op)), normalize(str(option))
            ).ratio(),
            reverse=True,
        )
        if possible_options:
            best = possible_options[0]
            retry(best.click)
            return True
        return False
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return False
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return False
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return False


def select_option_value(select, option):
    """
    Select an option from a dropdown menu by matching it with the value attribute.

    Args:
        select: The dropdown WebElement to interact with.
        option: The value attribute of the option to select.

    Returns:
        bool: True if the option was successfully selected, False otherwise.
    """
    select_option(select, option, lambda op: op.get_attribute("value"))


def select_option_text(select, option):
    """
    Select an option from a dropdown menu by matching it with the visible text.

    Args:
        select: The dropdown WebElement to interact with.
        option: The visible text of the option to select.

    Returns:
        bool: True if the option was successfully selected, False otherwise.
    """
    select_option(select, option, lambda op: op.text)


def select_first_option(select):
    """
    Select the first non-empty option from a dropdown menu.

    Args:
        select: The dropdown WebElement to interact with.

    Returns:
        bool: True if the first option was successfully selected, False otherwise.
    """
    try:
        options = [
            v
            for v in [
                o.get_attribute("value")
                for o in select.find_elements(By.CSS_SELECTOR, "option")
            ]
            if v.strip() != ""
        ]
        value = options[0]
        select_option_value(select, value)
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return False
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return False
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return False


def find_fuzzy(elements, to_string, target):
    """
    Find the element that most closely matches the target string using fuzzy matching.

    Args:
        elements: The list of elements to search through.
        to_string: A function to extract a string from an element for comparison.
        target: The target string to match.

    Returns:
        The element that best matches the target string, or None if no match is found.
    """
    try:
        return sorted(
            elements,
            key=lambda op: difflib.SequenceMatcher(
                None, normalize(to_string(op)), normalize(target)
            ).ratio(),
        )[-1]
    except Exception as e:
        logger.critical(f"Unexpected error occurred while finding fuzzy match: {e}")
        return None


def page_contains(driver, token, timeout=TIMEOUT):
    """
    Check if the page's content contains a specific token.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        token (str): The token to search for in the page's content.
        timeout (int): The maximum time to wait for the page content to be loaded (default is TIMEOUT).

    Returns:
        bool: True if the token is found in the page content, False otherwise.
    """
    try:
        haystack = (
            WebDriverWait(driver, timeout)
            .until(EC.visibility_of_any_elements_located((By.CSS_SELECTOR, "body")))[0]
            .get_attribute("innerHTML")
        )
        return re.search(token, haystack, re.IGNORECASE) is not None
    except (
        TimeoutException,
        NoSuchElementException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return False
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return False
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return False


def find_it(driver, elements, timeout=TIMEOUT, label=None):
    """
    Wait for and find an element based on the provided function.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        elements: A function that returns a list of elements.
        timeout (int): The maximum time to wait for the element to be found (default is TIMEOUT).
        label (str): An optional label for logging purposes.

    Returns:
        The first found element, or None if no element is found within the timeout period.
    """

    def get():
        results = elements()
        if len(results) > 0:
            return results[0]
        return None

    try:
        return wait_for(get, timeout=timeout, label=label)
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return None
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return None
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return None


def wait_for(fun, timeout=TIMEOUT, label=None):
    """
    Wait for a function to return a result within the specified timeout period.

    Args:
        fun: The function to be executed.
        timeout (int): The maximum time to wait for the function to return a result (default is TIMEOUT).
        label (str): An optional label for logging purposes.

    Returns:
        The result of the function if successful, or None if the timeout period expires.
    """
    try:
        t = 0
        while t < timeout:
            if label:
                logger.debug(f"Waiting for {label}")
            res = fun()
            delta = 0.25
            if res:
                logger.info(f"Found {label}")
                return res
            else:
                sleep(delta)
                t = t + delta
        return fun()
    except (
        ElementClickInterceptedException,
        ElementNotInteractableException,
        JavascriptException,
        NoSuchElementException,
        TimeoutException,
    ) as e:
        logger.critical(f"Exception occurred: {str(e)}")
        return None
    except WebDriverException as e:
        logger.critical(f"Unexpected WebDriver error occurred: {e}")
        return None
    except Exception as e:
        logger.critical(f"Unexpected error occurred: {e}")
        return None


def retry(fun, on_fail=lambda: True, sleep_time=1, attempts=RETRYATTEMPTS):
    """
    Retry executing a function multiple times with delays between attempts.

    Args:
        fun: The function to be executed.
        on_fail: A function to be called on failure (default does nothing).
        sleep_time (int): The time to sleep between attempts (default is 1 second).
        attempts (int): The maximum number of retry attempts (default is RETRYATTEMPTS).

    Returns:
        The result of the function if successful.

    Raises:
        Exception: If the function fails after the maximum number of attempts.
    """
    for attempt in range(0, attempts):
        try:
            if attempt > 0:
                logger.info(f"Retrying {fun.__name__}. Attempt #{attempt + 1}")
            return fun()
        except DontRetryException as e:
            raise e
        except Exception as e:
            attempt += 1
            on_fail()
            if attempt >= attempts:
                logger.critical(
                    f"Function {fun.__name__} failed after {attempts} attempts: {e}"
                )
                raise e
            lines = traceback.format_exception(e, limit=10)
            logger.warning(
                f"Retrying function due to error: {e}\n{''.join(lines)}, attempt={attempt} of {attempts}"
            )
            sleep(sleep_time)


class DontRetryException(Exception):
    pass


class KickedOutofFunnelException(DontRetryException):
    pass


class Fatal(Exception):
    def __init__(self, e, metadata={}):
        self._e = e
        self._meta = metadata

    def lines(self):
        return traceback.format_exception(self._e, limit=10)

    def metadata(self):
        base = self._meta
        base["retriable"] = not isinstance(self._e, DontRetryException)
        base["exception_name"] = self._e.__class__.__name__
        base["exception_message"] = str(self._e)
        return base
