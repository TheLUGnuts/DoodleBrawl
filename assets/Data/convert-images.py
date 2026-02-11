"""
This script grabs `characters.json`, and...
(1) Rips out all of the existing PNG images from their base64 strings
(2) Converts PNG to WEBP
(3) Compresses WEBP images with gzip

Author: Trevor Corcoran
NOTE: This can be deleted once we move to SQLite. My feelings won't be hurt -
it's mostly Claude generated code anyway since it's used once then never again.
"""

import json
import gzip
import base64
from io import BytesIO
from PIL import Image

FILE_NAME = "characters_test.json"

def convertImage(base64_string):
    """
    Convert headerless PNG base64 to WebP + gzip compressed base64
    Input: base64 string (no data URI prefix)
    Output: gzip compressed base64 string (no data URI prefix)
    """
    # Decode base64 to binary
    image_data = base64.b64decode(base64_string)
    
    # Open image with PIL
    image = Image.open(BytesIO(image_data))
    
    # Convert to WebP
    webp_buffer = BytesIO()
    image.save(webp_buffer, format='WEBP', quality=85)
    webp_buffer.seek(0)
    
    # Create base64 string from WebP data (no header)
    webp_base64 = base64.b64encode(webp_buffer.read()).decode('utf-8')
    
    # Gzip compress the base64 string
    compressed = gzip.compress(webp_base64.encode('utf-8'))
    
    # Return as base64 (no header)
    return base64.b64encode(compressed).decode('utf-8')


if __name__ == "__main__":
    # Open file
    data = {}
    with open(FILE_NAME, 'r') as file_obj:
        data = json.load(file_obj)

    # Iterate over objects
    for key in data.keys():
        # Prints
        print("CONVERTING ->")
        print(key)
        print(data[key]["name"])

        character = data[key]
        base64_string = character["image_file"]
        new_base64 = convertImage(base64_string)
        character["image_file"] = new_base64

        print('DONE.')
        print()


    # Write results
    with open(FILE_NAME + '.new', 'w') as file_obj:
        new_json = json.dumps(data, indent=2)
        file_obj.write(new_json)
