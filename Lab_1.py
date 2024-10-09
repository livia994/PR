from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re  # Regular expression library for validating the price

# Initialize the Chrome options and driver setup
chrome_options = Options()
chrome_options.add_argument("--start-maximized")  # Open Chrome maximized
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Open the main product listing page
url = "https://999.md/ro/list/animals-and-plants/other-animals"
driver.get(url)

# Wait for the page to load (adjust sleep time if needed)
time.sleep(5)

# Find all product items by their container class
products = driver.find_elements(By.CLASS_NAME, 'ads-list-photo-item')

# Store all product details
all_product_details = []

# Loop through each product and extract details
for index, product in enumerate(products):
    try:
        # Extract product name
        product_name = product.find_element(By.CLASS_NAME, 'ads-list-photo-item-title').text
    except Exception:
        product_name = None  # Set to None to indicate missing value

    try:
        # Extract product price
        price_div = product.find_element(By.CLASS_NAME, 'ads-list-photo-item-price')
        product_price = price_div.text if price_div else "Negociabil"
    except Exception:
        product_price = None  # Set to None to indicate missing value

    try:
        # Extract product link
        product_link = product.find_element(By.TAG_NAME, 'a').get_attribute('href')
    except Exception:
        product_link = "Link not found"
        print(f"Error finding product link")

    # Skip products that are ads (identified by their link structure)
    if product_link.startswith("https://999.md/booster/link?token="):
        continue  # Skip this iteration if it's an ad

    # Open the product link in a new tab to scrape the other attribute
    driver.execute_script("window.open(arguments[0]);", product_link)
    driver.switch_to.window(driver.window_handles[1])  # Switch to the new tab

    # Wait for the product page to load
    time.sleep(3)

    try:
        # Locate the attribute using itemprop attributes in XPath
        label_xpath = "//span[@itemprop='name' and contains(text(), 'Sex')]"
        value_xpath = "//span[@itemprop='value']"

        # Find the label and its corresponding value element
        label_element = driver.find_element(By.XPATH, label_xpath)
        if label_element:
            # If "Sex" label found, retrieve the next sibling element containing its value
            animal_type = driver.find_element(By.XPATH, value_xpath).text
        else:
            animal_type = "Category not found"
    except Exception as e:
        animal_type = "Category not found"
        print(f"Error finding animal type")

    # Validation 1: Check if the product name and price are not None
    if product_name is None or product_price is None:
        print(f"Skipping product due to missing name or price: {product_name}, {product_price}")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        continue

    # Validation 2: Check if the price is numeric (e.g., "300 lei" should have a number in it)
    if not re.search(r'\d+', product_price):  # Regular expression checks for digits in the price
        print(f"Skipping product due to invalid price format: {product_price}")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        continue

    # Print the extracted data for this product
    print(f"Product Name: {product_name}, Price: {product_price}, Link: {product_link}, Category: {animal_type}")

    # Close the new tab and switch back to the main product listing tab
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    # Append the product details to our list after validation
    all_product_details.append({
        "Product Name": product_name,
        "Price": product_price,
        "Link": product_link,
        "Category": animal_type
    })

# Close the browser
driver.quit()

# Display all collected product details
print("\nFinal Extracted Product Data:")
for product in all_product_details:
    print(product)
