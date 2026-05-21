from PIL import Image, ImageFilter
import io

def crop_plant_image(original_image_bytes: bytes, box_2d: list):
    """
    Crops the original photo around the detected plant using a 3:4 portrait ratio.
    Returns the processed image bytes.
    """
    img = Image.open(io.BytesIO(original_image_bytes)).convert("RGB")
    width, height = img.size
    
    ymin, xmin, ymax, xmax = box_2d

    # Denormalize coordinates (0-1000 to pixel values)
    left = xmin * width / 1000
    top = ymin * height / 1000
    right = xmax * width / 1000
    bottom = ymax * height / 1000
    
    box_w = right - left
    box_h = bottom - top
    
    # Add 20% padding
    target_w = box_w * 1.2
    target_h = box_h * 1.2
    
    # Ensure 3:4 ratio (width:height = 0.75)
    if target_w / max(1, target_h) > 0.75:
        target_h = target_w / 0.75
    else:
        target_w = target_h * 0.75
        
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    
    crop_left = cx - target_w / 2
    crop_right = cx + target_w / 2
    crop_top = cy - target_h / 2
    crop_bottom = cy + target_h / 2
    
    # Shift if out of bounds
    if crop_left < 0:
        crop_right -= crop_left
        crop_left = 0
    if crop_right > width:
        crop_left -= (crop_right - width)
        crop_right = width
        
    if crop_top < 0:
        crop_bottom -= crop_top
        crop_top = 0
    if crop_bottom > height:
        crop_top -= (crop_bottom - height)
        crop_bottom = height
        
    # Clamp to image size
    crop_left = max(0, crop_left)
    crop_top = max(0, crop_top)
    crop_right = min(width, crop_right)
    crop_bottom = min(height, crop_bottom)
    
    final_crop = img.crop((crop_left, crop_top, crop_right, crop_bottom))
    
    img_byte_arr = io.BytesIO()
    final_crop.save(img_byte_arr, format='JPEG', quality=90)
    return img_byte_arr.getvalue()
