import cv2
import numpy as np
import math

# Mapping colors (RGB) to Region Names

enp = {
    (77, 189, 114): "Tree savanna", 
    (150, 251, 122): "Shrub savanna", 
    (255, 195, 0): "Grass savanna",
    (142, 185, 219): "Salt pan", 
    (0, 34, 255): "Waterhole", 
    (255, 225, 0): "Road",
    (255, 0, 0): "Camp", 
    (0, 0, 0): "Fence",
    (255, 255, 255): "Outside"
}

inp = {
    (114, 137, 67): "Optimal wetland",
    (232, 231, 185): "Riparian marshland",
    (244, 201, 123): "Grazed wetland",
    (42, 55, 127): "Human barrier",
    (160, 209, 216): "Waters",
    (255, 225, 0): "Road",
    (255, 0, 0): "Camp",
    (255, 255, 255): "Outside"
}

uknp = {
    (0, 110, 59): "Mountainous rainforests",
    (254, 200, 132): "Low plateaus",
    (137, 163, 212): "Mangroves and swamp",
    (66, 185, 126): "Cropland",
    (108, 170, 221): "Rivers",
    (5, 86, 167): "Ocean",
    (255, 225, 0): "Road",
    (255, 0, 0): "Camp",
    (255, 255, 255): "Outside"
}

def analyze_point(image_path, map, x, y):
    # Load image and convert BGR (OpenCV default) to RGB
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        return "Image not found."
    
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    height, width, _ = img_rgb.shape

    # 1. Identify the region at the current coordinate
    # Note: Images are indexed as [row, column] which is [y, x]
    pixel_color = tuple(img_rgb[y, x])
    region = map.get(pixel_color, "Unknown")

    # Features to measure distance to
    d = {}

    d[region] = 0.0

    # 2-6. Calculate distances using Distance Transform
    for color, name in map.items():
        # Create a binary mask: 0 where the color matches, 255 everywhere else
        # (Distance transform calculates distance from non-zero to zero pixels)
        mask = np.all(img_rgb == color, axis=-1)
        
        if not np.any(mask):
            d[name] = 400
            continue

        # Convert mask to uint8: 0 for target pixels, 1 for everything else
        binary_mask = np.where(mask, 0, 1).astype(np.uint8)
        
        # Calculate distance transform
        dist_map = cv2.distanceTransform(binary_mask, cv2.DIST_L2, 5)
        
        # Get distance at the specific (x, y) point
        d[name] = round(float(dist_map[y, x]), 2)

    return d

# --- Example Usage ---
# Provide the path to your 'Etosha map.jpg' and the (x, y) coordinates
result = analyze_point('UKNP.png', uknp, x=700, y=500)
print(result)
# for key, value in result.items():
#     print(f"{key}: {value}")