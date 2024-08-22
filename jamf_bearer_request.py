import base64
import json
import os
import requests
from getpass import getpass
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET

# Get Bearer token with username and password
JAMF_URL = "https://jss.example.com/"
BEARER_URL = JAMF_URL + "api/v1/auth/token"
output_dir = "/tmp/Restricted_Software_XMLs"

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

while True:
    username = input("What's your username?\n")
    password = getpass(prompt="\nPassword: ")
    usernamepassword = (username + ":" + password).replace(" ", "")
    encoded = base64.b64encode(bytes(usernamepassword, "UTF-8"))

    # Check if the username and password are valid
    payload = {}
    headers = {
        "Authorization": f"Basic {encoded.decode()}",
    }

    token_response = requests.request(
        "POST", BEARER_URL, headers=headers, data=payload)

    if token_response.status_code == 200:
        break
    else:
        print("Invalid username or password. Please try again.")

# End Bearer token request

token = json.loads(token_response.text)["token"]

try:
    response = requests.get(
        f"{JAMF_URL}/JSSResource/restrictedsoftware",
        headers={"accept": "application/xml", "Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    responseXML = response.text
    print(responseXML)
except requests.exceptions.RequestException as e:
    print(f"Error fetching restricted software list: {e}")
    exit(1)

# Locate the ID numbers
try:
    root = ET.fromstring(responseXML)
    # Print the structure of the XML
    for elem in root.iter():
        print(elem.tag, elem.attrib)

    # Adjust the XPath based on the actual structure
    restrictionList = root.findall(".//restricted_software_title/id")
    if restrictionList:
        print("Found IDs:")
        for id_elem in restrictionList:
            print(id_elem.text)
    else:
        print("No <id> elements found.")
except ET.ParseError as e:
    print(f"Error parsing XML: {e}")
    exit(1)

# Extract and sort the results
sortedRestrictionList = sorted([id_elem.text for id_elem in restrictionList])
print("Sorted Restriction List:")
print(sortedRestrictionList)

# Iterate through the list of IDs and pull the details, then write them to output_dir
for i in sortedRestrictionList:
    try:
        rs_response = requests.get(
            f"{JAMF_URL}/JSSResource/restrictedsoftware/id/{i}",
            headers={"accept": "application/xml", "Authorization": f"Bearer {token}"}
        )
        print(f"Requesting ID {i}, Status Code: {rs_response.status_code}")
        rs_response.raise_for_status()
        rsDetails = rs_response.text

        # Print each line of the response
        for line in rsDetails.splitlines():
            print(line)

        # Write the response to a file named with the ID
        file_path = os.path.join(output_dir, f"restricted_software_{i}.xml")
        with open(file_path, 'w') as f:
            f.write(rsDetails)
        print(f"Written to {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching details for ID {i}: {e}")
    except Exception as e:
        print(f"Unexpected error for ID {i}: {e}")