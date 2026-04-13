from PIL import Image
import io

def crop_plant_image(original_image_bytes: bytes, box_2d: list):
    """
    Crops the image based on normalized bounding box [ymin, xmin, ymax, xmax].
    Returns the cropped image bytes.
    """
    img = Image.open(io.BytesIO(original_image_bytes))
    width, height = img.size
    
    ymin, xmin, ymax, xmax = box_2d
    
    # Denormalize coordinates (0-1000 to pixel values)
    left = xmin * width / 1000
    top = ymin * height / 1000
    right = xmax * width / 1000
    bottom = ymax * height / 1000
    
    cropped_img = img.crop((left, top, right, bottom))
    
    img_byte_arr = io.BytesIO()
    cropped_img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()
