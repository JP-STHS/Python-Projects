# Date:  November 28, 2023

import math
#Start of code borrowed from Sample Code Convolution
#Start of code inspired from Sample Code Filters
from PIL import Image

#image limitations
MAX_COLOR_VALUE = 256
MAX_BIT_VALUE = 8

#show the default image
comparisonimage = Image.open(".png")
comparisonimage.show()
image_to_hide = comparisonimage

def bigconv():
    #Convolution filter
    def convolve (list1,list2):
        answer = 0
        for x in range(3):
            for y in range(3):
                answer = answer + list1[x][y]*list2[x][y]
        answer = int(answer)
        if answer < 0:
            answer = 0
        #answer = abs(answer)
        if answer > 255:
            answer = 255
        return answer

    # define convolution
    trans = [[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]]

    # user pick channels
    print('Channel Options are: R, G, B, RG, GB, RB, RGB')
    channels = input('Enter the channel(s)')
    c_test = [False,False,False]
    c_test[0] = (channels == 'R') or (channels == 'RG') or (channels == 'RB') or (channels == 'RGB')
    c_test[1] = (channels == 'G') or (channels == 'RG') or (channels == 'GB') or (channels == 'RGB')
    c_test[2] = (channels == 'B') or (channels == 'RB') or (channels == 'GB') or (channels == 'RGB')
    bw_test = (channels == 'BW')
    print(channels)

    # read in image
    path = "BIG galaxy.png"  # location of image
    file = Image.open(path)  # file to be opened
    width, height = file.size
    m = file.load()  # file loaded into memory
    data = []  # data structure to store image information
    for y in range(height):
        for x in range(width):
            pixel = m[x, y]
            data.append((pixel[0], pixel[1], pixel[2]))
    print(data[0:20])

    # perform convolution
    new_data = []
    for y in range(height):
        for x in range(width):
            border_test = (x == 0) or (y == 0) or (y == height - 1) or (x == width - 1)
            pixel = m[x, y]
            r_intensity = 0
            g_intensity = 0
            b_intensity = 0
            # convolve the r channel
            if border_test==False:
                pixela = m[x-1,y-1]
                pixelb = m[x,y-1]
                pixelc = m[x+1,y-1]
                pixeld = m[x-1,y]
                pixele = m[x,y]
                pixelf = m[x+1,y]
                pixelg = m[x-1,y+1]
                pixelh = m[x,y+1]
                pixeli = m[x+1,y+1]
            for q in range(3):
                if (border_test == False) and c_test[q]:
                    a = pixela[q]
                    b = pixelb[q]
                    c = pixelc[q]
                    d = pixeld[q]
                    e = pixele[q]
                    f = pixelf[q]
                    g = pixelg[q]
                    h = pixelh[q]
                    i = pixelh[q]
                    patch = [[a,b,c], [d, e, f], [g, h, i]]
                    if q == 0:
                        r_intensity = convolve(trans,patch)
                    if q == 1:
                        g_intensity = convolve(trans,patch)
                    if q == 2:
                        b_intensity = convolve(trans,patch)
            new_data.append((r_intensity, g_intensity, b_intensity))
    resolution = (width,height)
    image_filter = Image.new("RGB", resolution)
    image_filter.putdata(new_data)
    image_filter.show()

def make_image(data, resolution):
    image = Image.new("RGB", resolution)
    image.putdata(data)
    return image

def warmer(image_to_hide):
    width, height = image_to_hide.size
    hide_image = image_to_hide.load()
    data = []
    for y in range(height):
        for x in range(width):
            rgb_hide = hide_image[x, y]
            r_hide = rgb_hide[0]
            g_hide = rgb_hide[1]
            b_hide = 0
            data.append((r_hide,g_hide,b_hide))
    return make_image(data, image_to_hide.size)

#Output from ChatGPT
#create swirl filter
def swirl_effect(image_to_swirl):
    width, height = image_to_swirl.size
    swirl_image = image_to_swirl.load()
    data = []

    #swirl parameters
    swirl_intensity = 125
    swirl_center_x = width // 2
    swirl_center_y = height // 2

    for y in range(height):
        for x in range(width):
            dx = x - swirl_center_x
            dy = y - swirl_center_y

            #Calculate polar coordinates
            radius = math.sqrt(dx * dx + dy * dy)
            angle = math.atan2(dy, dx)

            # Apply swirl effect to the red channel based on the polar coordinates
            new_x = int(swirl_center_x + math.cos(angle + radius / swirl_intensity) * radius)
            new_y = int(swirl_center_y + math.sin(angle + radius / swirl_intensity) * radius)

            # Ensure the new coordinates are within bounds
            if 0 <= new_x < width and 0 <= new_y < height:
                # Get the pixel color from the original location
                pixel_color = swirl_image[new_x, new_y]
                r_swirl = pixel_color[0]  # Red channel value from the original location

                # Manipulate the red channel based on the swirl effect
                data.append((r_swirl, pixel_color[1], pixel_color[2]))
            else:
                # If the new coordinates are out of bounds, use black color
                data.append((0, 0, 0))  # Set the pixel to black

    return make_image(data, image_to_swirl.size)
#mainline
#filters menu
userchoice=input("Please choose a filter:\nImage Convolution (1)\nWarm Image (2)\nSwirl Image (3)\nChoose: ")
if userchoice == "1":
    #perfom convolution
    bigconv()
if userchoice =="2":
    #make the image warmer
    warmer(image_to_hide).show()
if userchoice =="3":
    #create a swirl filter
    swirl_effect(image_to_hide).show()
