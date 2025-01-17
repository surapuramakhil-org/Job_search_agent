from gc import callbacks
import random
import time
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver

from logger import logger
import pygame
import constants

# Module-level variable to store the default driver
__DEFAULT_DRIVER: Optional[webdriver.Chrome] = None


def set_default_driver(driver: webdriver.Chrome):
    """
    Store the main.py's driver in a module-level variable so other
    functions can use it when no driver is explicitly provided.
    """
    global __DEFAULT_DRIVER
    __DEFAULT_DRIVER = driver
    logger.debug("Default driver has been set for browser_utils.")


def _get_driver(driver: Optional[webdriver.Chrome]) -> webdriver.Chrome:
    """
    Internal helper to either return the provided driver or fall back
    to the stored default driver if none is provided.
    """
    if driver is not None:
        return driver
    if __DEFAULT_DRIVER is not None:
        return __DEFAULT_DRIVER
    raise RuntimeError(
        "No driver provided and no default driver is set in browser_utils."
    )


def is_scrollable(element):
    scroll_height = element.get_attribute("scrollHeight")
    client_height = element.get_attribute("clientHeight")
    scrollable = int(scroll_height) > int(client_height)
    logger.debug(
        f"Element scrollable check: scrollHeight={scroll_height}, clientHeight={client_height}, scrollable={scrollable}"
    )
    return scrollable


def scroll_slow(driver, scrollable_element, start=0, end=3600, step=300, reverse=False):
    logger.debug(
        f"Starting slow scroll: start={start}, end={end}, step={step}, reverse={reverse}"
    )

    if reverse:
        start, end = end, start
        step = -step

    if step == 0:
        logger.error("Step value cannot be zero.")
        raise ValueError("Step cannot be zero.")

    max_scroll_height = int(scrollable_element.get_attribute("scrollHeight"))
    current_scroll_position = int(float(scrollable_element.get_attribute("scrollTop")))
    logger.debug(f"Max scroll height of the element: {max_scroll_height}")
    logger.debug(f"Current scroll position: {current_scroll_position}")

    if reverse:
        if current_scroll_position < start:
            start = current_scroll_position
        logger.debug(f"Adjusted start position for upward scroll: {start}")
    else:
        if end > max_scroll_height:
            logger.warning(
                f"End value exceeds the scroll height. Adjusting end to {max_scroll_height}"
            )
            end = max_scroll_height

    script_scroll_to = "arguments[0].scrollTop = arguments[1];"

    try:
        if scrollable_element.is_displayed():
            if not is_scrollable(scrollable_element):
                logger.warning("The element is not scrollable.")
                return

            if (step > 0 and start >= end) or (step < 0 and start <= end):
                logger.warning(
                    "No scrolling will occur due to incorrect start/end values."
                )
                return

            position = start
            previous_position = (
                None  # Tracking the previous position to avoid duplicate scrolls
            )
            while (step > 0 and position < end) or (step < 0 and position > end):
                if position == previous_position:
                    # Avoid re-scrolling to the same position
                    logger.debug(
                        f"Stopping scroll as position hasn't changed: {position}"
                    )
                    break

                try:
                    driver.execute_script(
                        script_scroll_to, scrollable_element, position
                    )
                    logger.debug(f"Scrolled to position: {position}")
                except Exception as e:
                    logger.error(f"Error during scrolling: {e}")

                previous_position = position
                position += step

                # Decrease the step but ensure it doesn't reverse direction
                step = max(10, abs(step) - 10) * (-1 if reverse else 1)

                time.sleep(random.uniform(0.6, 1.5))

            # Ensure the final scroll position is correct
            driver.execute_script(script_scroll_to, scrollable_element, end)
            logger.debug(f"Scrolled to final position: {end}")
            time.sleep(0.5)
        else:
            logger.warning("The element is not visible.")
    except Exception as e:
        logger.error(f"Exception occurred during scrolling: {e}")


def remove_focus_active_element(driver):
    driver.execute_script("document.activeElement.blur();")
    logger.debug("Removed focus from active element.")


# Todo: detection of captcha won't work
def handle_security_checks(driver=None):
    """
    Handles security checks like CAPTCHAs by notifying the user and waiting for completion.
    Assumes the page is already loaded.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    if driver is None:
        driver = _get_driver(driver)
        if driver is None:
            raise ValueError("No driver provided and no default driver set.")

    try:
        logger.debug("Checking for CAPTCHA...")
        # Locate the hCaptcha iframe
        captcha_iframe = driver.find_element(
            By.XPATH, "//iframe[contains(@src, 'hcaptcha')]"
        )

        # Switch to the iframe
        driver.switch_to.frame(captcha_iframe)

        try:
            # Check for specific elements inside the iframe that indicate an active CAPTCHA
            visible_elements = driver.find_elements(
                By.XPATH, "//*[contains(@style, 'visibility: visible')]"
            )

            if len(visible_elements) > 0:
                logger.info("CAPTCHA detected. Bringing browser to the foreground.")

                # Bring browser window to foreground
                driver.switch_to.default_content()
                security_check(driver)

        except NoSuchElementException:
            logger.debug("No active CAPTCHA challenge detected inside iframe.")

        finally:
            # Switch back to default content
            driver.switch_to.default_content()

    except NoSuchElementException:
        logger.debug("No CAPTCHA detected on the page.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


def security_check(driver=None):

    if driver is None:
        driver = _get_driver(driver)
        if driver is None:
            raise ValueError("No driver provided and no default driver set.")

    driver.switch_to.window(driver.current_window_handle)

    # Play a notification sound
    logger.info("Playing notification sound...")
    pygame.mixer.init()
    pygame.mixer.music.load(constants.SECURITY_CHECK_ALERT_AUDIO)
    pygame.mixer.music.play()

    logger.info("Waiting for user to solve CAPTCHA...")

    # Wait for user to acknowledge by pressing any key
    input("Press Enter after solving the CAPTCHA to continue...")
