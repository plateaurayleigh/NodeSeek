# -- coding: utf-8 --
"""
Copyright (c) 2024 [Hosea]
Licensed under the MIT License.
See LICENSE file in the project root for full license information.

Optimized NodeSeek Automation Script
- Handles sign-in
- Comments on recent trade posts
- Attempts to give a chicken leg to one post
"""
import os
# from bs4 import BeautifulSoup # bs4 is imported but not used, can be removed
import random
import time
import traceback
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.keys import Keys # Keys is not directly used, ActionChains handles it
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# --- Configuration ---
# Read configuration from environment variables once
NS_RANDOM = os.environ.get("NS_RANDOM", "false").lower() == "true" # Example: Use for future random actions if needed
COOKIE = os.environ.get("NS_COOKIE") or os.environ.get("COOKIE")
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"

# Comment strings
RANDOM_INPUT_STR = ["bd", "绑定", "帮顶"]

# --- Helper Functions ---

def safe_click(driver, element, element_name="element"):
    """Attempts to click an element, falling back to JavaScript click if needed."""
    try:
        element.click()
        print(f"Clicked {element_name} successfully.")
    except WebDriverException as e:
        print(f"Standard click failed for {element_name}, attempting JavaScript click: {e}")
        try:
            driver.execute_script("arguments[0].click();", element)
            print(f"JavaScript click successful for {element_name}.")
        except Exception as js_e:
            print(f"JavaScript click also failed for {element_name}: {js_e}")
            raise # Re-raise the exception if both methods fail

def wait_and_find_element(driver, by, value, timeout=10, element_name="element"):
    """Waits for an element to be present and returns it."""
    try:
        print(f"Waiting for {element_name} ({by}: {value})...")
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        print(f"Found {element_name}.")
        return element
    except TimeoutException:
        print(f"Timeout waiting for {element_name} ({by}: {value}).")
        return None
    except Exception as e:
        print(f"An error occurred while waiting for {element_name}: {e}")
        return None

def wait_and_click_element(driver, by, value, timeout=10, element_name="element"):
    """Waits for an element to be clickable and clicks it."""
    try:
        print(f"Waiting for {element_name} ({by}: {value}) to be clickable...")
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        print(f"Found {element_name}, attempting click...")
        safe_click(driver, element, element_name)
        return True
    except TimeoutException:
        print(f"Timeout waiting for {element_name} to be clickable.")
        return False
    except Exception as e:
        print(f"An error occurred while waiting for or clicking {element_name}: {e}")
        return False

# --- Core Functions ---

def setup_driver_and_cookies():
    """
    Initializes the browser (undetected_chromedriver) and sets cookies.
    Returns: Configured driver instance or None if setup fails.
    """
    if not COOKIE:
        print("Error: COOKIE environment variable is not set.")
        return None

    print("Starting browser initialization...")
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu') # Often recommended for headless

    if HEADLESS:
        print("Running in headless mode.")
        options.add_argument('--headless=new') # Use new headless mode
        # Add arguments to try and bypass detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36') # Example UA

    try:
        driver = uc.Chrome(options=options)

        if HEADLESS:
             # Execute JS to hide webdriver property
             driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
             # Set window size again just in case (redundant with option, but harmless)
             # driver.set_window_size(1920, 1080) # Option should handle this

        print("Chrome started successfully.")

        print("Navigating to NodeSeek to set cookies...")
        driver.get('https://www.nodeseek.com')

        # Wait briefly for initial page load before adding cookies
        time.sleep(2) # A short sleep is often needed before adding cookies

        print("Setting cookies...")
        for cookie_item in COOKIE.split(';'):
            try:
                name, value = cookie_item.strip().split('=', 1)
                if name and value: # Ensure name and value are not empty
                     driver.add_cookie({
                         'name': name,
                         'value': value,
                         'domain': '.nodeseek.com', # Use root domain
                         'path': '/'
                     })
                else:
                    print(f"Skipping invalid cookie part: {cookie_item}")
            except Exception as e:
                print(f"Error setting cookie part '{cookie_item}': {e}")
                continue

        print("Cookies set. Refreshing page to apply cookies...")
        driver.refresh()

        # Wait for a common element that indicates the page is loaded and potentially logged in
        # The sign-in icon is a good indicator
        if wait_and_find_element(driver, By.XPATH, "//span[@title='签到']", timeout=15, element_name="sign-in icon after refresh"):
             print("Page refreshed and sign-in icon found. Cookie setup likely successful.")
             return driver
        else:
             print("Error: Sign-in icon not found after refresh. Cookie setup may have failed.")
             # Optional: Check for login specific elements if sign-in icon isn't reliable
             # try:
             #     WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.user-avatar')))
             #     print("User avatar found. Cookie setup likely successful.")
             #     return driver
             # except TimeoutException:
             #     print("User avatar not found. Cookie setup likely failed.")
             driver.quit()
             return None

    except Exception as e:
        print(f"An error occurred during browser setup or cookie configuration: {e}")
        traceback.print_exc()
        if driver:
            driver.quit()
        return None

def click_sign_icon(driver):
    """
    Attempts to click the sign-in icon and the '试试手气' button.
    Returns: True if the process was attempted, False otherwise.
    """
    print("Attempting sign-in process...")
    try:
        # Wait for and click the sign-in icon
        sign_icon = wait_and_find_element(driver, By.XPATH, "//span[@title='签到']", timeout=30, element_name="sign-in icon")
        if not sign_icon:
            print("Sign-in icon not found. Skipping sign-in.")
            return False

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sign_icon)
        time.sleep(0.5) # Short pause after scroll

        safe_click(driver, sign_icon, "sign-in icon")

        print("Sign-in icon clicked. Waiting for sign-in modal/page...")

        # Wait for the "试试手气" button to appear in the modal/new page
        # This button is the one to click to claim the daily reward
        if wait_and_click_element(driver, By.XPATH, "//button[contains(text(), '试试手气')]", timeout=10, element_name="'试试手气' button"):
            print("'试试手气' button clicked successfully.")
            # Add a small wait for the modal/dialog to process/close
            time.sleep(3) # Give time for the reward animation/dialog
        else:
            print("'试试手气' button not found or not clickable (possibly already signed in today).")

        # Optional: Check for a success message or the sign-in status change
        # This part is highly site-specific and might require inspecting the DOM after clicking

        print("Sign-in process attempted.")
        return True

    except Exception as e:
        print(f"An error occurred during the sign-in process: {e}")
        traceback.print_exc()
        return False

def click_chicken_leg(driver):
    """
    Attempts to click the '加鸡腿' (give chicken leg) icon on a post page.
    Handles the 7-day limit confirmation modal.
    Returns: True if chicken leg was successfully given, False otherwise.
    """
    print("Attempting to give a chicken leg...")
    try:
        # Wait for the chicken leg icon to be clickable
        chicken_btn = wait_and_find_element(driver, By.XPATH, '//div[@class="nsk-post"]//div[@title="加鸡腿"][1]', timeout=5, element_name="'加鸡腿' icon")
        if not chicken_btn:
            print("'加鸡腿' icon not found or not clickable.")
            return False

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chicken_btn)
        time.sleep(0.5) # Short pause after scroll

        safe_click(driver, chicken_btn, "'加鸡腿' icon")
        print("'加鸡腿' icon clicked. Waiting for confirmation modal...")

        # Wait for the confirmation modal to appear
        modal_present = wait_and_find_element(driver, By.CSS_SELECTOR, '.msc-confirm', timeout=5, element_name="confirmation modal")
        if not modal_present:
            print("Confirmation modal did not appear.")
            return False

        # Wait for either the "7天前" error title or the OK button within the modal
        try:
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@class='msc-confirm']//h3[contains(text(), '该评论创建于7天前')] | //div[@class='msc-confirm']//button[contains(@class, 'msc-ok')]"))
            )

            # Check if the error title is present and visible
            try:
                error_title = driver.find_element(By.XPATH, "//div[@class='msc-confirm']//h3[contains(text(), '该评论创建于7天前')]")
                if error_title.is_displayed():
                    print("Post is older than 7 days, cannot give chicken leg.")
                    # Still need to click OK to close the modal
                    ok_btn = wait_and_find_element(driver, By.CSS_SELECTOR, '.msc-confirm .msc-ok', timeout=3, element_name="modal OK button (error case)")
                    if ok_btn:
                        safe_click(driver, ok_btn, "modal OK button")
                        # Wait for modal to disappear
                        WebDriverWait(driver, 5).until_not(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '.msc-overlay'))
                        )
                    return False # Failed due to age
            except NoSuchElementException:
                 # Error title not found, proceed assuming it's the success/confirm case
                 pass # Continue to the next check

            # If error title wasn't found, wait for and click the OK button
            ok_btn = wait_and_click_element(driver, By.CSS_SELECTOR, '.msc-confirm .msc-ok', timeout=3, element_name="modal OK button (success case)")
            if ok_btn:
                print("Successfully confirmed giving chicken leg.")
                # Wait for modal to disappear
                WebDriverWait(driver, 5).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.msc-overlay'))
                )
                time.sleep(1) # Small extra wait
                return True # Successfully gave chicken leg
            else:
                 print("OK button not found or clickable in modal.")
                 return False # Failed to confirm

        except TimeoutException:
             print("Timeout waiting for modal content (error title or OK button).")
             # Attempt to close modal if it exists, just in case
             try:
                 ok_btn = driver.find_element(By.CSS_SELECTOR, '.msc-confirm .msc-ok')
                 if ok_btn.is_displayed() and ok_btn.is_enabled():
                      safe_click(driver, ok_btn, "modal OK button (fallback)")
                      WebDriverWait(driver, 5).until_not(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.msc-overlay'))
                      )
             except:
                 pass # Ignore if cannot find/click OK
             return False # Assume failure if modal handling failed

    except Exception as e:
        print(f"An error occurred during the '加鸡腿' operation: {e}")
        traceback.print_exc()
        return False

def nodeseek_comment(driver):
    """
    Navigates to the trade category, selects recent posts, and adds comments.
    Attempts to give a chicken leg to the first eligible post.
    """
    print("Starting NodeSeek commenting task...")
    target_url = 'https://www.nodeseek.com/categories/trade'
    try:
        driver.get(target_url)
        print(f"Navigated to {target_url}. Waiting for post list...")

        # Wait for post list items to load
        if not wait_and_find_element(driver, By.CSS_SELECTOR, '.post-list-item', timeout=30, element_name="post list items"):
            print("Failed to load post list. Skipping commenting task.")
            return

        print("Post list loaded.")

        # Get posts and filter out pinned ones
        posts = driver.find_elements(By.CSS_SELECTOR, '.post-list-item')
        print(f"Found {len(posts)} total posts.")
        valid_posts = [post for post in posts if not post.find_elements(By.CSS_SELECTOR, '.pined')]
        print(f"Found {len(valid_posts)} non-pinned posts.")

        # Select a random sample of recent posts (up to 20)
        num_posts_to_comment = min(20, len(valid_posts))
        if num_posts_to_comment == 0:
            print("No valid posts found to comment on.")
            return

        selected_posts = random.sample(valid_posts, num_posts_to_comment)

        # Collect URLs
        selected_urls = []
        for post in selected_posts:
            try:
                post_link = post.find_element(By.CSS_SELECTOR, '.post-title a')
                url = post_link.get_attribute('href')
                if url:
                    selected_urls.append(url)
            except NoSuchElementException:
                print("Warning: Could not find post link in a selected post element.")
                continue

        print(f"Selected {len(selected_urls)} posts for commenting.")

        is_chicken_leg_given = False # Flag to give chicken leg only once

        # Process each selected post
        for i, post_url in enumerate(selected_urls):
            try:
                print(f"\n--- Processing post {i+1}/{len(selected_urls)}: {post_url} ---")
                driver.get(post_url)

                # Wait for the post content area to load
                if not wait_and_find_element(driver, By.CSS_SELECTOR, '.nsk-post', timeout=15, element_name="post content area"):
                    print(f"Failed to load post content for {post_url}. Skipping.")
                    continue

                # Attempt to give chicken leg if not already given
                if not is_chicken_leg_given:
                    is_chicken_leg_given = click_chicken_leg(driver)
                    if is_chicken_leg_given:
                        print("Successfully gave chicken leg to this post.")
                    else:
                        print("Could not give chicken leg to this post (already given or post too old).")

                # Wait for the comment editor (CodeMirror)
                editor = wait_and_find_element(driver, By.CSS_SELECTOR, '.CodeMirror', timeout=15, element_name="comment editor")
                if not editor:
                    print("Comment editor not found. Skipping comment for this post.")
                    continue

                # Click editor to focus
                safe_click(driver, editor, "comment editor")
                time.sleep(0.5) # Short pause after focus

                # Simulate typing the comment
                input_text = random.choice(RANDOM_INPUT_STR)
                print(f"Typing comment: '{input_text}'")
                actions = ActionChains(driver)
                for char in input_text:
                    actions.send_keys(char)
                    actions.pause(random.uniform(0.05, 0.2)) # Simulate human typing speed
                actions.perform()

                # Wait for the submit button to be clickable
                submit_button_clicked = wait_and_click_element(
                    driver,
                    By.XPATH,
                    "//button[contains(@class, 'submit') and contains(@class, 'btn') and contains(text(), '发布评论')]",
                    timeout=10,
                    element_name="'发布评论' button"
                )

                if submit_button_clicked:
                    print("Comment submitted successfully.")
                    # Wait briefly for the comment to process/appear
                    time.sleep(random.uniform(3, 6))
                else:
                    print("Failed to find or click the '发布评论' button. Comment not submitted.")


                print(f"--- Finished processing post {i+1}/{len(selected_urls)} ---")

                # Random wait before processing the next post
                if i < len(selected_urls) - 1:
                     wait_time = random.uniform(5, 15) # Longer random wait between posts
                     print(f"Waiting {wait_time:.2f} seconds before next post...")
                     time.sleep(wait_time)

            except Exception as e:
                print(f"An error occurred while processing post {post_url}: {e}")
                traceback.print_exc()
                # Continue to the next post even if one fails
                continue

        print("\nNodeSeek commenting task completed.")

    except Exception as e:
        print(f"An error occurred during the overall commenting task: {e}")
        traceback.print_exc()

# --- Main Execution ---

if __name__ == "__main__":
    print("Starting NodeSeek automation script...")
    driver = None
    try:
        # 1. Setup browser and cookies
        driver = setup_driver_and_cookies()
        if not driver:
            print("Browser setup failed. Exiting.")
            exit(1)

        # 2. Perform sign-in
        print("\n--- Starting Sign-in Task ---")
        click_sign_icon(driver)
        print("--- Sign-in Task Attempted ---\n")

        # 3. Perform commenting and chicken leg task
        print("\n--- Starting Commenting Task ---")
        nodeseek_comment(driver)
        print("--- Commenting Task Completed ---\n")

    except Exception as main_error:
        print(f"An unhandled error occurred in the main script execution: {main_error}")
        traceback.print_exc()

    finally:
        # 4. Close the browser
        if driver:
            print("Closing browser...")
            driver.quit()
        print("Script execution finished.")
