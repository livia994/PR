import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from functools import reduce

# Define the URL of the product listing page
url = "https://floralsoul.md/catalog/?swoof=1&product_cat=plante"

# Make an HTTP GET request to fetch the page content
response = requests.get(url)
if response.status_code != 200:
    print(f"Failed to fetch page. Status code: {response.status_code}")
    exit()

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# Store all product details
all_product_details = []

# Find all product items by their container class
products = soup.find_all('div', class_='product-info')

# Loop through each product and extract details
for product in products:
    try:
        # Extract product name
        product_name_tag = product.find('h4', class_='product-item-name')
        product_name = product_name_tag.text.strip() if product_name_tag else None

        # Extract product link
        product_link_tag = product_name_tag.find('a', href=True)
        product_link = product_link_tag['href'] if product_link_tag else "Link not found"

        # Extract product price
        price_tag = product.find('span', class_='woocommerce-Price-amount')
        product_price = price_tag.text.strip() if price_tag else "Price not found"
    except Exception as e:
        print(f"Error extracting data: {e}")
        continue

    # Validation 1: Ensure name and price are not None or empty
    if not product_name or not product_price:
        print(f"Skipping product due to missing name or price: {product_name}, {product_price}")
        continue

    # Validation 2: Ensure price contains a valid number
    if not re.search(r'\d+', product_price):
        print(f"Skipping product due to invalid price: {product_price}")
        continue

    # Open the product link and scrape an additional attribute
    product_page_response = requests.get(product_link)
    if product_page_response.status_code != 200:
        print(f"Failed to fetch product page. Status code: {product_page_response.status_code}")
        continue

    # Parse the product page HTML
    product_page_soup = BeautifulSoup(product_page_response.content, "html.parser")

    try:
        # Extract the category
        category_tag = product_page_soup.find('span', class_='posted_in')
        category = category_tag.text.strip() if category_tag else "Category not found"

        # Extract plant size
        size_tag = product_page_soup.find('span', class_='tagged_as')
        plant_size = size_tag.text.strip() if size_tag else "Size not found"
    except Exception as e:
        print(f"Error extracting additional data: {e}")
        continue

    # Store validated product data
    all_product_details.append({
        "Product Name": product_name,
        "Price": product_price,
        "Link": product_link,
        "Category": category,
        "Size": plant_size
    })

# Function to convert prices
def convert_price(price_str):
    # Extract the numeric value and the currency
    match = re.search(r'(\d+[\.,]?\d*)\s*([a-zA-Z]+)', price_str)
    if match:
        price_value = float(match.group(1).replace(',', '.'))
        currency = match.group(2).strip().upper()
        # Convert MDL to EUR (example conversion rate: 1 EUR = 20 MDL)
        if currency == 'MDL':
            return price_value / 20  # Convert to EUR
        elif currency == 'EUR':
            return price_value * 20  # Convert to MDL
    return None

# Filter products by price range and convert prices
min_price = 10  # Set your minimum price in EUR
max_price = 50  # Set your maximum price in EUR

filtered_products = list(filter(lambda p: p['Price'] is not None, all_product_details))
for product in filtered_products:
    product['Converted Price'] = convert_price(product['Price'])

filtered_products = list(filter(lambda p: p['Converted Price'] is not None and min_price <= p['Converted Price'] <= max_price, filtered_products))

# Use reduce to sum up the prices of filtered products
total_price = reduce(lambda acc, p: acc + (p['Converted Price'] if p['Converted Price'] is not None else 0), filtered_products, 0)

# Attach UTC timestamp and total price to the new data structure
timestamp = datetime.utcnow().isoformat() + 'Z'
result = {
    "Filtered Products": filtered_products,
    "Total Price": total_price,
    "Timestamp": timestamp
}

# Display final results
print("\nFinal Extracted Product Data:")
print(f"Total Price (EUR): {result['Total Price']}")
print(f"Timestamp: {result['Timestamp']}")
for product in result["Filtered Products"]:
    print(f"Product Name: {product['Product Name']}")
    print(f"Converted Price (EUR): {product['Converted Price']}")
    print(f"Link: {product['Link']}")
    print(f"Category: {product['Category']}")
    print(f"Size: {product['Size']}")
    print("-" * 50)  # Separator between products
