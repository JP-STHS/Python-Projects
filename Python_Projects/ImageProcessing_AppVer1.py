# Date:  November 16, 2023

#Starting point of code inspired from Image Processing Examples
from PIL import Image
from PIL import ImageEnhance


#display image
funnyImage = Image.open("BIG galaxy.png")
funnyImage.show()

#mainline
#simple menu
print("\nHow would you like to change the image?")
answer = int(input("Crop image (1)\nFlip image horizontally (2)\nFlip image vertically (3)\nRotate image (4)\n"
                   "Change image to B&W (5)\nEnhance the image (6)\nChoice: "))
#allow user to crop image
if answer == 1:
    left = int(input("Enter a value for the amount to crop the left side of the image "))
    right = int(input("Enter a value for the amount to crop the right side of the image (must be bigger than left )"))
    top = int(input("Enter a value for the amount to crop the top of the image "))
    bottom = int(input("Enter a value for the amount to crop the bottom of the image (must be bigger than top value )"))
    crop_image = funnyImage.crop((left,top,right,bottom))
    crop_image.show()
#allow user to flip image
if answer ==2:
    horizontalFlip = funnyImage.transpose(Image.FLIP_LEFT_RIGHT)
    horizontalFlip.show()
if answer ==3:
    verticalFlip = funnyImage.transpose(Image.FLIP_TOP_BOTTOM)
    verticalFlip.show()
#rotate image
if answer ==4:
    rotatedImage = funnyImage.rotate(int(input("Enter rotation angle: ")))
    rotatedImage.show()
#change image to black and white
if answer==5:
    convertedImage = funnyImage.convert('L')
    convertedImage.show()
#enhance the image
if answer ==6:
    #enhance color
    imageClr = ImageEnhance.Color(funnyImage).enhance(float(input("Enhance the color: ")))
    imageClr.show()
    #enhance contrast
    imageContrast = ImageEnhance.Contrast(funnyImage).enhance(float(input("Enhance the contrast: ")))
    imageContrast.show()
    #enhance brightness
    imageBrightness = ImageEnhance.Brightness(funnyImage).enhance(float(input("Enhance the brightness: ")))
    imageBrightness.show()
    #enhance sharpness
    imageSharpness = ImageEnhance.Sharpness(funnyImage).enhance(float(input("Enhance the sharpness: ")))
    imageSharpness.show()

