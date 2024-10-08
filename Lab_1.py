import requests
from bs4 import BeautifulSoup

url = "https://999.md/ro/list/animals-and-plants/other-animals"

try:
    # Send a GET request
    response = requests.get(url)

    # Check the status code
    if response.status_code == 200:
        print("GET request successful!")

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all product items (you may need to adjust this selector based on the page structure)
        products = soup.find_all('div', class_='ads-list-photo-item')  # Adjust the class name accordingly

        # Loop through each product item and extract details
        for product in products:
            # Extract product name
            product_name = product.find('div', class_='ads-list-photo-item-title').find('a').text.strip()

            # Extract product price
            price_div = product.find('div', class_='ads-list-photo-item-price')
            if price_div:
                product_price = price_div.find('span', class_='ads-list-photo-item-price-wrapper').text.strip()
            else:
                product_price = "Negociabil"  # or handle it as needed

            # Extract product link
            product_link = product.find('a')['href']

            # Print the extracted data
            print(f"Product Name: {product_name}, Price: {product_price}, Link: {product_link}")
    else:
        print(f"GET request failed with status code: {response.status_code}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

except Exception as e:
    print(f"An unexpected error occurred: {e}")
