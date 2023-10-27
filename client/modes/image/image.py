import os
from flask import Blueprint, render_template, request, current_app, flash
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
from pylfsr import LFSR

image = Blueprint("image", __name__, static_folder="static", template_folder="templates")

@image.route("/encode")
def image_encode():
    return render_template("image-encode.html")

@image.route("/encode-result", methods=['POST', 'GET'])
def image_encode_result():
    if request.method == 'POST':
        text_encryption = True
        message = request.form['data']

        hennon_key_a = request.form['hennon-a']
        hennon_key_b = request.form['hennon-b']
        key = [float(hennon_key_a), float(hennon_key_b)]

        lfsr_polynomial = request.form['lfsr']
        lfsr_polynomial_list = [int(x) for x in str(lfsr_polynomial)]

        encode(os.path.join(
                current_app.config['UPLOAD_IMAGE_FOLDER'], "lena.png"), message, key, lfsr_polynomial_list)
        result = request.form
        
        return render_template("image-encode-result.html", result=result, text_encryption=text_encryption, message=message)

@image.route("/decode")
def image_decode():
    return render_template("image-decode.html")

@image.route("/decode-result", methods=['POST', 'GET'])
def image_decode_result():
    if request.method == 'POST':
        file = request.files['image']
        if file.filename == '':
            flash('No image selected')
        if file:
            filename = secure_filename(file.filename)
            hennon_key_a = request.form['hennon-a']
            hennon_key_b = request.form['hennon-b']
            key = [float(hennon_key_a), float(hennon_key_b)]

            lfsr_polynomial = request.form['lfsr']
            lfsr_polynomial_list = [int(x) for x in str(lfsr_polynomial)]

            file.save(os.path.join(
                current_app.config['UPLOAD_IMAGE_FOLDER'], filename))
            text_decryption = True
            message = decode(os.path.join(
                current_app.config['UPLOAD_IMAGE_FOLDER'], "lena.png"),
                os.path.join(
                current_app.config['UPLOAD_IMAGE_FOLDER'], filename), key, lfsr_polynomial_list)
        else:
            text_decryption = False
        result = request.form
        return render_template("image-decode-result.html", result=result, file=file, text_decryption=text_decryption, message=message)

# --------------------------------
# Helper Functions
# --------------------------------

def convertToBinary(data):
    if isinstance(data, str):
        return ''.join([ format(ord(i), "08b") for i in data ])
    elif isinstance(data, bytes) or isinstance(data, np.ndarray):
        return [ format(i, "08b") for i in data ]
    elif isinstance(data, int) or isinstance(data, np.uint8):
        return format(data, "08b")
    else:
        raise TypeError("Type not supported.")

def binaryToDecimal(binary):
    decimal = 0
    for bit in binary:
        decimal = decimal*2 + int(bit)
    return decimal

def HennonMapBinary(dimension, key):
    rows = dimension[0]
    cols = dimension[1]
    x = key[0]
    y = key[1]
    a = 1.4
    b = 0.3

    # Total Number of bitSequence produced
    sequenceSize = rows * cols
    bitSequenceSize = cols
    # Each bitSequence contains k bits
    bitSequence = []       
    # Each matrix contains m*n byteArray
    matrix = []

    for i in range(sequenceSize):
        x_next = y + 1 - (a * (x**2)) 
        y_next = b * x
        x = x_next
        y = y_next
        if x <= 0.4:
            bit = 0
        else:
            bit = 1

        bitSequence.append(bit) 

        # If Bit Sequence has k bits, convert it to decimal and add it to Byte Sequence.
        if i % bitSequenceSize == bitSequenceSize - 1:
            matrix.append(bitSequence)
            bitSequence = []

    return matrix

# --------------------------------
# Encoding
# --------------------------------

def encode(filename, secret_data, key, poly):

    # read the image.
    imagehandler = Image.open(filename) 
    image = imagehandler.load()
    image_size = imagehandler.size

    secret_data += "=!"

    # convert data to binary.
    binary_secret_data = convertToBinary(secret_data)
    data_len = len(binary_secret_data)

    # Build chaotic map and derive some available pixels.
    map = HennonMapBinary(image_size, key)

    # Select pixels by superimposing Chaotic Map on the image.
    availablePixels = []
    for i in range(image_size[0]):
        for j in range(0,image_size[1]):
            if map[i][j] == 1:
                availablePixels.append([i,j,0])

    # check if encoding is possible
    if data_len > len(availablePixels)*6:
        raise ValueError("[!] Insufficient space. Please change key or data.")

    # Build LFSR
    lfsr = LFSR(initstate = [1, 1, 1, 1, 1, 1, 1, 1], fpoly=poly, counter_start_zero=True)

    index = 0

    for i in range(0, data_len, 2):

        # Choose pixel using LFSR from Available pixels
        index = (index + binaryToDecimal(lfsr.state)) % len(availablePixels)
        lfsr.next()

        # If pixel is already used 3 times, keep choosing next pixel until unused pixel is found.
        while availablePixels[index][2] >= 2:
            index = (index + binaryToDecimal(lfsr.state)) % len(availablePixels)
            lfsr.next()

        # Extract row, column and usagestate values.
        row, col, usageState = availablePixels[index][0], availablePixels[index][1], availablePixels[index][2]
        
        # Update with Red Value
        if usageState == 0:
            red = list(convertToBinary(image[row,col][0]))
            red[-2] = str(int(red[-2]) ^ int(binary_secret_data[i]))
            red[-1] = str(int(red[-1]) ^ int(binary_secret_data[i+1]))
            red = "".join(red)
            red = binaryToDecimal(red)
            image[row,col] = (red, image[row,col][1], image[row,col][2])

        # Update with Blue Value
        elif usageState == 1:
            blue = list(convertToBinary(image[row,col][1]))
            blue[-2] = str(int(blue[-2]) ^ int(binary_secret_data[i]))
            blue[-1] = str(int(blue[-1]) ^ int(binary_secret_data[i+1]))
            blue = "".join(blue)
            blue = binaryToDecimal(blue)
            image[row,col] = (image[row,col][0], blue, image[row,col][2])
        
        # Update with Green Value
        elif usageState == 2:
            green = list(convertToBinary(image[row,col][2]))
            green[-2] = str(int(green[-2]) ^ int(binary_secret_data[i]))
            green[-1] = str(int(green[-1]) ^ int(binary_secret_data[i+1]))
            green = "".join(green)
            green = binaryToDecimal(green)
            image[row,col] = (image[row,col][0], image[row,col][1], green)
        
        availablePixels[index][2] += 1

    # Save the final image.
    imagehandler.save(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "encoded_image.png"), "PNG")

# --------------------------------
# Decoding
# --------------------------------

def decode(original_filename, encoded_filename, key, poly):

    # Read the Encoded Image
    imagehandler = Image.open(encoded_filename) 
    image = imagehandler.load()
    image_size = imagehandler.size

    # Read the Original Image
    imagehandler_or = Image.open(original_filename) 
    image_or = imagehandler_or.load()

    # Find Delimiter
    delimiter1 = convertToBinary("!")
    delimiter2 = convertToBinary("=")

    # Build chaotic map and derive some available pixels
    map = HennonMapBinary(image_size, key)

    availablePixels = []
    for i in range(image_size[0]):
        for j in range(0,image_size[1]):
            if map[i][j] == 1:
                availablePixels.append([i,j,0])

    # Build LFSR
    lfsr = LFSR(initstate = [1, 1, 1, 1, 1, 1, 1, 1], fpoly=poly, counter_start_zero=True)

    data = []
    current = ""
    index = 0

    i = 0

    while True:

        # Choose an unused pixel using LFSR from Chaotic Map

        index = (index + binaryToDecimal(lfsr.state)) % len(availablePixels)
        lfsr.next()

        while availablePixels[index][2] >= 2:
            index = (index + binaryToDecimal(lfsr.state)) % len(availablePixels)
            lfsr.next()

        row, col, usageState = availablePixels[index][0], availablePixels[index][1], availablePixels[index][2]
        
        # Extract from Red Value
        if usageState == 0:
            value = list(convertToBinary(image[row,col][0]))
            value_or = list(convertToBinary(image_or[row,col][0]))
            
            temp1 = str(int(value[-2]) ^ int(value_or[-2]))
            temp2 = str(int(value[-1]) ^ int(value_or[-1]))

        # Extract from Blue Value
        elif usageState == 1:
            value = list(convertToBinary(image[row,col][1]))
            value_or = list(convertToBinary(image_or[row,col][1]))
            
            temp1 = str(int(value[-2]) ^ int(value_or[-2]))
            temp2 = str(int(value[-1]) ^ int(value_or[-1]))
        
        # Extract from Green Value
        else:
            value = list(convertToBinary(image[row,col][2]))
            value_or = list(convertToBinary(image_or[row,col][2]))

            temp1 = str(int(value[-2]) ^ int(value_or[-2]))
            temp2 = str(int(value[-1]) ^ int(value_or[-1]))
        
        current = current + temp1 + temp2
        if len(current) == 8:
            if current == delimiter1:
                if len(data) >= 1 and data[-1] == delimiter2:
                    data.pop()
                    break
            data.append(current)
            current = ""
        availablePixels[index][2] += 1

        i += 2

    data_found = "".join(chr(int(c, 2)) for c in data)

    return data_found