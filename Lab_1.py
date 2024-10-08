import requests
from bs4 import BeautifulSoup
url = "https://999.md/ro/list/animals-and-plants/other-animals"

try:
    # Send a GET request
    response = requests.get(url)

    # Check the status code
    if response.status_code == 200:
        print("GET request successful!")

        print(response.text[:1000])
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Example: Extract product details (Assuming products are listed within a div with class 'product-item')
        products = soup.find_all('div', class_='product-item')

        for product in products:
            # Extract product name
            product_name = product.find('a').text.strip()

            # Extract product price
            product_price = product.find('span', class_='price').text.strip()

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
