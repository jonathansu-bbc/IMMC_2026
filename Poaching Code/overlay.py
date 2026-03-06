import cv2
import numpy as np

def overlay_images(background_path, overlay_path, output_path, opacity=0.9, position=(0, 0)):
    # Load images
    background = cv2.imread(background_path, cv2.IMREAD_COLOR)
    overlay = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
    
    print(f"Background: {background.shape}")
    print(f"Overlay: {overlay.shape}")
    
    # Position overlay
    y, x = position
    h, w = overlay.shape[:2]
    
    roi = background[y:y+h, x:x+w]
    overlay_rgb = overlay[:, :, :3]
    
    # Create uniform opacity mask (2D -> 3D)
    alpha = np.ones((h, w, 3), dtype=np.float32) * opacity
    
    # Blend
    blended = (roi.astype(float) * (1 - alpha) + overlay_rgb.astype(float) * alpha)
    blended = np.clip(blended, 0, 255).astype(np.uint8)
    
    # Paste back
    background[y:y+h, x:x+w] = blended
    
    cv2.imwrite(output_path, background)
    cv2.imshow('Overlay Result', background)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print(f"Overlay placed at ({x},{y})")

# Usage
overlay_images('1.1.png', 'real3.1.png', 'result.png', opacity=0.6, position=(0, 0))