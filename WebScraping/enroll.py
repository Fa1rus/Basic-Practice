import time
import re
import sys
import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

import os

# --- CONFIGURATION ---
COURSES_FILE = "courses.txt"

def load_courses():
    courses = []
    if os.path.exists(COURSES_FILE):
        with open(COURSES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    courses.append(line)
    
    if not courses:
        print(f"[WARNING] No courses found in '{COURSES_FILE}'. Creating a default file.")
        courses = ["123-456 Example Course", "987-654 Another Course"]
        with open(COURSES_FILE, "w", encoding="utf-8") as f:
            f.write("# Add your courses here, one per line.\n")
            f.write("# Format: XXX-XXX <course_name>\n")
            f.write("123-456 Example Course\n")
            f.write("987-654 Another Course\n")
    return courses

COURSES = load_courses()

USER_DATA_DIR = "./browser_profile"       # Folder to save your session
RETRY_DELAY =  10                        # Seconds to wait before retrying on site crash

def handle_enrollment():
    with sync_playwright() as p:
        print("Launching Firefox (Persistent Context)...")
        browser = p.firefox.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,  
            viewport={'width': 1280, 'height': 800}
        )
        
        page = browser.pages[0]

        while True:
            try:
                # -------------------------------------------------------------
                # STEP 1: Login and Home Page
                # -------------------------------------------------------------
                print("\n[INFO] Navigating to https://sis.psu.ac.th/...")
                page.goto("https://sis.psu.ac.th/", wait_until="domcontentloaded", timeout=30000)
                
                # Check if we need to click the PSU Passport Login button
                if page.locator("#loginButton").is_visible():
                    print("[INFO] Clicking 'PSU Passport' login button...")
                    page.wait_for_selector("#loginButton", timeout=10000)
                    
                    # Ensure the click actually triggers navigation
                    for attempt in range(5):
                        if "login.microsoftonline.com" in page.url.lower() or "sis.psu.ac.th/home" in page.url.lower():
                            break
                        try:
                            page.click("#loginButton")
                            page.wait_for_url(re.compile(r"login\.microsoftonline\.com|sis\.psu\.ac\.th/home", re.IGNORECASE), timeout=5000)
                            break
                        except PlaywrightTimeoutError:
                            print(f"[WARNING] Did not navigate after click, retrying (Attempt {attempt+1})...")

                if "login.microsoftonline.com" in page.url.lower() or "login" in page.url.lower():
                    print("[ACTION REQUIRED] Please complete login and MFA visually.")
                    # Wait until we are redirected back to the SIS portal dashboard
                    page.wait_for_url(re.compile(r"sis\.psu\.ac\.th/home", re.IGNORECASE), timeout=0) 
                
                print("[INFO] Successfully reached the home page!")
                time.sleep(2) # brief pause to let UI render

                print("Closing the browser...")

                # -------------------------------------------------------------
                # STEP 2: Navigate to Enrollment Check
                # -------------------------------------------------------------
                print("[INFO] Clicking 'Enrollment'...")
                page.wait_for_selector(".registDynamicButton", timeout=10000)
                page.click(".registDynamicButton")
                
                print("[INFO] Waiting for 'services/enroll' page...")
                page.wait_for_url(re.compile(r"services/enroll", re.IGNORECASE), timeout=10000)
                time.sleep(2)
                
                # -------------------------------------------------------------
                # STEP 3: Click Next and Check Eligibility
                # -------------------------------------------------------------
                print("[INFO] Clicking Next button to check if enrollment is open...")
                
                # We try a few common selectors for a 'Next' button if we don't know the exact ID
                # UPDATE THIS if the button has a specific class or ID (e.g., button#btn-next)
                next_button_selectors = ["button:has-text('Next')", "button:has-text('ถัดไป')", ".next-btn"]
                clicked = False
                for sel in next_button_selectors:
                    if page.locator(sel).is_visible():
                        page.click(sel)
                        clicked = True
                        break
                
                if not clicked:
                    print("[WARNING] Could not automatically find the 'Next' button! You might need to add the exact CSS selector in the code.")
                
                time.sleep(3) # Wait for page to load or error popup to appear
                
                # Retrieve the text of the entire body to check for error messages
                page_text = page.locator("body").inner_text()
                
                error_keywords = [
                    "The student profile is not specified or invalid",
                    "Unable to register or confirm registration",
                    "(REGIST_CALENDAR)",
                    "out of time"
                ]
                
                found_error = False
                for keyword in error_keywords:
                    if keyword.lower() in page_text.lower():
                        print(f"\n[FAILED] Cannot enroll right now.")
                        print(f"Feedback from system: '{keyword}'")
                        print("Ending the script.")
                        browser.close()
                        sys.exit(0) # Exits script based on the workflow
                        
                # -------------------------------------------------------------
                # STEP 4: Searching and Enrolling Courses
                # -------------------------------------------------------------
                print("\n[SUCCESS] Eligible to enroll. Proceeding to search courses...")
                
                for course in COURSES:
                    print(f"\n--- Processing {course} ---")
                    
                    try:
                        # Find the search bar
                        # UPDATE THIS if the search input box has a specific ID (e.g. input#course-search)
                        print(f"  > Typing course '{course}' into search bar...")
                        page.wait_for_selector("input[type='text'], input[placeholder*='Search']", timeout=5000)
                        
                        # Fill the first text input we find with the course name
                        page.fill("input[type='text'], input[placeholder*='Search']", course) 
                        page.keyboard.press("Enter") # Simulate pressing Enter to search
                        time.sleep(3) # Wait for results
                        
                        # Wait for the course card/text to appear
                        # We use the course ID prefix (e.g. "123-456") to locate it
                        course_id = course.split(' ')[0]
                        course_element = page.locator(f"text='{course_id}'")
                        
                        if not course_element.is_visible():
                            print(f"  [ERROR] Course '{course}' did not appear in search results.")
                            # Create error file logging the issue
                            with open("enrollment_error_log.txt", "a", encoding="utf-8") as f:
                                stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                f.write(f"[{stamp}] Searching for '{course}' failed. Course did not appear.\n")
                            continue # Process next course
                        
                        print(f"  > Course '{course_id}' found! Clicking it...")
                        # Grab the first matching element just in case there are copies
                        course_element.first.click()
                        time.sleep(2)
                        
                        # -------------------------------------------------------------
                        # STEP 5: Choose section pop-up
                        # -------------------------------------------------------------
                        print(f"  > Pop-up appeared. Choosing section...")
                        # ------------------------------------------------------------------
                        # ACTION REQUIRED: You MUST add the logic here to click the section!
                        # Example: page.click("text='Section 01'")
                        # ------------------------------------------------------------------
                        
                        print(f"  > Submitting course...")
                        # ACTION REQUIRED: Click the submit button inside the popup!
                        # Example: page.click("button:has-text('Submit')")
                        
                        time.sleep(3) # Wait for submission to complete
                        
                        print(f"  > Result: Returning back to search next course...")
                        # ACTION REQUIRED: Navigate back or clear search to ready next loop!
                        # Example: page.keyboard.press("Escape") to close a success popup
                        # Example: page.fill("input[type='text']", "") to clear search bar
                        
                    except Exception as e:
                        print(f"  [ERROR] Failed during '{course}' process: {e}")
                        with open("enrollment_error_log.txt", "a", encoding="utf-8") as f:
                                stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                f.write(f"[{stamp}] Exception error on '{course}': {str(e)}\n")
                        
                print("\n[INFO] Finished attempting all courses!")
                break # Exit the `while True` loop, we are done!

            except (PlaywrightTimeoutError, PlaywrightError) as e:
                # Handle website crashes, timeout failures, connection aborts
                print(f"[ERROR] Website is down, slow, or connection reset: {e}")
                print(f"Retrying the entire process in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)

        # Finished
        browser.close()
        print("[INFO] Automation exited cleanly.")

if __name__ == "__main__":
    try:
        handle_enrollment()
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting...")
        sys.exit(0)
