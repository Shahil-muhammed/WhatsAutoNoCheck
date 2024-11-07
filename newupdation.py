import os
import json
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Save cookies to a file
def save_cookies(driver, filepath):
    with open(filepath, 'w') as file:
        json.dump(driver.get_cookies(), file)

# Load cookies from a file
def load_cookies(driver, filepath):
    with open(filepath, 'r') as file:
        cookies = json.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)

# Check if a WhatsApp number is valid
def is_valid_whatsapp_number(driver, phone_number):
    # Navigate to the chat page for the given phone number
    driver.get(f"https://web.whatsapp.com/send?phone={phone_number}")
    
    # Check for the invalid number message
    try:
        invalid_msg = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Phone number shared via url is invalid')]"))
        )
        if invalid_msg:
            print(f"The number {phone_number} is **not valid**.")
            return "invalid"
    except TimeoutException:
        # If the message doesn't appear, assume the number is valid
        print(f"The number {phone_number} is **valid**.")
        return "valid"

# Main function to process numbers from CSV and output results
def process_numbers_from_csv(input_file, output_file):
    # Set up Chrome driver with options
    chrome_options = Options()
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--user-data-dir=C:/Users/SHA/Desktop/whatAuto/ChromeData")  # Persistent session

    chrome_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    cookies_path = "whatsapp_cookies.json"
    
    try:
        # Open WhatsApp Web and load cookies if available
        driver.get("https://web.whatsapp.com")

        # Check if cookies exist
        if os.path.exists(cookies_path):
            load_cookies(driver, cookies_path)
            driver.refresh()
            print("Loaded cookies, refreshing page...")
            
            try:
                # Wait for main UI to confirm successful login
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "side"))
                )
                print("Successfully reused session from saved cookies.")
            except TimeoutException:
                print("Session expired or cookies invalid, re-login required.")
                os.remove(cookies_path)  # Remove old cookies

        # Prompt for QR scan if no valid session
        if not os.path.exists(cookies_path):
            try:
                qr_code_element = WebDriverWait(driver, 120).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "canvas[aria-label*='Scan']"))
                )
                print("QR code loaded. Please scan it to log in.")
                input("Press Enter after scanning the QR code to continue...")
                save_cookies(driver, cookies_path)
            except TimeoutException:
                print("Error: QR code did not load in time.")
                driver.quit()
                return

        # Read phone numbers from input CSV and store results
        results = []
        with open(input_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                phone_number = row['Number']
                status = is_valid_whatsapp_number(driver, phone_number)
                results.append({'Number': phone_number, 'Status': status})

        # Write results to output CSV
        with open(output_file, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['Number', 'Status'])
            writer.writeheader()
            writer.writerows(results)

        print(f"Results saved to {output_file}")

    finally:
        driver.quit()

# Execute the function with your input and output files
process_numbers_from_csv("input.csv", "output.csv")
