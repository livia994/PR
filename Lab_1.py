import socket
from bs4 import BeautifulSoup
import re
from datetime import datetime
from functools import reduce

# Function to perform HTTP GET request using a TCP socket
def http_get(host, path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, 80))
        request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        s.sendall(request.encode())
        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
    response_str = response.decode()
    header, _, body = response_str.partition('\r\n\r\n')
    return body

# Define the URL of the product listing page
url = "http://floralsoul.md/catalog/?swoof=1&product_cat=plante"
host = "floralsoul.md"
path = "/catalog/?swoof=1&product_cat=plante"

# Fetch the HTML content using TCP socket
html_content = http_get(host, path)

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(html_content, "html.parser")

# Store all product details
all_product_details = []

# Find all product items by their container class
products = soup.find_all('div', class_='product-info')

# Loop through each product and extract details
for product in products:
    try:
        product_name_tag = product.find('h4', class_='product-item-name')
        product_name = product_name_tag.text.strip() if product_name_tag else None
        product_link_tag = product_name_tag.find('a', href=True)
        product_link = product_link_tag['href'] if product_link_tag else "Link not found"
        price_tag = product.find('span', class_='woocommerce-Price-amount')
        product_price = price_tag.text.strip() if price_tag else "Price not found"
    except Exception as e:
        print(f"Error extracting data: {e}")
        continue

    if not product_name or not product_price:
        print(f"Skipping product due to missing name or price: {product_name}, {product_price}")
        continue

    if not re.search(r'\d+', product_price):
        print(f"Skipping product due to invalid price: {product_price}")
        continue

    product_page_response = http_get(host, product_link)
    product_page_soup = BeautifulSoup(product_page_response, "html.parser")

    try:
        category_tag = product_page_soup.find('span', class_='posted_in')
        category = category_tag.text.strip() if category_tag else "Category not found"
        size_tag = product_page_soup.find('span', class_='tagged_as')
        plant_size = size_tag.text.strip() if size_tag else "Size not found"
    except Exception as e:
        print(f"Error extracting additional data: {e}")
        continue

    all_product_details.append({
        "Product Name": product_name,
        "Price": product_price,
        "Link": product_link,
        "Category": category,
        "Size": plant_size
    })

# Price conversion function
def convert_price(price_str):
    match = re.search(r'(\d+[\.,]?\d*)\s*([a-zA-Z]+)', price_str)
    if match:
        price_value = float(match.group(1).replace(',', '.'))
        currency = match.group(2).strip().upper()
        if currency == 'MDL':
            return price_value / 20
        elif currency == 'EUR':
            return price_value * 20
    return None

min_price = 10  # Minimum price in EUR
max_price = 50  # Maximum price in EUR

filtered_products = list(filter(lambda p: p['Price'] is not None, all_product_details))
for product in filtered_products:
    product['Converted Price'] = convert_price(product['Price'])

filtered_products = list(
    filter(lambda p: p['Converted Price'] is not None and min_price <= p['Converted Price'] <= max_price,
           filtered_products))

total_price = reduce(lambda acc, p: acc + (p['Converted Price'] if p['Converted Price'] is not None else 0),
                     filtered_products, 0)

timestamp = datetime.utcnow().isoformat() + 'Z'
result = {
    "Filtered Products": filtered_products,
    "Total Price": total_price,
    "Timestamp": timestamp
}

# Custom serialization logic
def custom_serialize(data):
    if isinstance(data, dict):
        items = [f'D:k:{custom_serialize(key)}:v:{custom_serialize(value)};' for key, value in data.items()]
        return f'{{{"".join(items)}}}'
    elif isinstance(data, list):
        items = [custom_serialize(item) for item in data]
        return f'L:[{"; ".join(items)}];'
    elif isinstance(data, str):
        return f'str({data})'
    elif isinstance(data, int) or isinstance(data, float):
        return f'int({data})'
    else:
        return f'unknown({data})'  # Fallback for unsupported data types

# Placeholder for deserialization logic (can be implemented later)
def custom_deserialize(serialized_str):
    pass

# Serialization to JSON format
def serialize_to_json(data):
    json_str = "{\n"
    json_str += f'  "Total Price": {data["Total Price"]},\n'
    json_str += f'  "Timestamp": "{data["Timestamp"]}",\n'
    json_str += '  "Filtered Products": [\n'

    for product in data["Filtered Products"]:
        json_str += '    {\n'
        json_str += f'      "Product Name": "{product["Product Name"]}",\n'
        json_str += f'      "Converted Price": {product["Converted Price"]},\n'
        json_str += f'      "Link": "{product["Link"]}",\n'
        json_str += f'      "Category": "{product["Category"]}",\n'
        json_str += f'      "Size": "{product["Size"]}"\n'
        json_str += '    },\n'

    json_str = json_str.rstrip(",\n") + "\n"  # Remove last comma
    json_str += '  ]\n'
    json_str += '}'

    return json_str

# Serialization to XML format
def serialize_to_xml(data):
    xml_str = "<ProductData>\n"
    xml_str += f'  <TotalPrice>{data["Total Price"]}</TotalPrice>\n'
    xml_str += f'  <Timestamp>{data["Timestamp"]}</Timestamp>\n'
    xml_str += "  <FilteredProducts>\n"

    for product in data["Filtered Products"]:
        xml_str += "    <Product>\n"
        xml_str += f'      <ProductName>{product["Product Name"]}</ProductName>\n'
        xml_str += f'      <ConvertedPrice>{product["Converted Price"]}</ConvertedPrice>\n'
        xml_str += f'      <Link>{product["Link"]}</Link>\n'
        xml_str += f'      <Category>{product["Category"]}</Category>\n'
        xml_str += f'      <Size>{product["Size"]}</Size>\n'
        xml_str += "    </Product>\n"

    xml_str += "  </FilteredProducts>\n"
    xml_str += "</ProductData>"

    return xml_str

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

# Serialize and print JSON
json_output = serialize_to_json(result)
print("\nJSON Output:")
print(json_output)

# Serialize and print XML
xml_output = serialize_to_xml(result)
print("\nXML Output:")
print(xml_output)

# Custom serialization test
serialized_custom_data = custom_serialize(result)
print("\nCustom Serialized Data:")
print(serialized_custom_data)
