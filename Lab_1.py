import requests
from bs4 import BeautifulSoup
import re

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

# Display all collected product details
print("\nFinal Extracted Product Data:")
for product in all_product_details:
    print(f"Product Name: {product['Product Name']}")
    print(f"Price: {product['Price']}")
    print(f"Link: {product['Link']}")
    print(f"Category: {product['Category']}")
    print(f"Size: {product['Size']}")
    print("-" * 50)  # Separator between products
