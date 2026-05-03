from PIL import Image, ImageFilter
import io

def crop_plant_image(original_image_bytes: bytes, box_2d: list):
    """
    Creates a portrait-style effect:
    1. Keeps the original image size.
    2. Blurs the entire image.
    3. Pastes the clear, sharp plant cutout over the blurred background based on the bounding box.
    Returns the processed image bytes.
    """
    img = Image.open(io.BytesIO(original_image_bytes)).convert("RGB")
    width, height = img.size
    
    ymin, xmin, ymax, xmax = box_2d
    
    # Add 10% padding to give more context/clarity to the plant cutout
    padding = 50 # 5% of 1000
    ymin = max(0, ymin - padding)
    xmin = max(0, xmin - padding)
    ymax = min(1000, ymax + padding)
    xmax = min(1000, xmax + padding)

    # Denormalize coordinates (0-1000 to pixel values)
    left = xmin * width / 1000
    top = ymin * height / 1000
    right = xmax * width / 1000
    bottom = ymax * height / 1000
    
    # 1. Create a sharp crop of the plant with extra padding
    sharp_cutout = img.crop((left, top, right, bottom))
    
    # 2. Create a blurred version of the entire original image
    blurred_bg = img.filter(ImageFilter.GaussianBlur(radius=15))
    
    # 3. Paste the sharp plant back onto the blurred background
    blurred_bg.paste(sharp_cutout, (int(left), int(top)))
    
    img_byte_arr = io.BytesIO()
    blurred_bg.save(img_byte_arr, format='JPEG', quality=90)
    return img_byte_arr.getvalue()
