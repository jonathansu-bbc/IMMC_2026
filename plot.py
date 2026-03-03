import cv2

# 1. Load your PNG image
# Replace 'your_image.png' with your actual file path
image_path = 'Rhino distribution.png' 
img = cv2.imread(image_path)

if img is None:
    print("Error: Image not found.")
else:
    # 2. Define the coordinates (x, y) 
    # These are some of the scaled coordinates we found earlier
    points = [
        (2107.34, 322.99), (2124.07, 322.99), (2139.61, 321.80),
        (2155.63, 331.13), (362.18, 474.92), (1985.41, 474.92),
        (2157.94, 502.04), (345.96, 513.88), (2126.46, 520.38),
        (355.25, 523.49), (404.02, 523.28), (421.95, 525.16)
    ]

    # 3. Plot the dots
    for pt in points:
        # Convert to integers for pixel coordinates
        center = (int(pt[0]), int(pt[1]))
        
        # Draw the circle: (image, center, radius, color_bgr, thickness)
        # (0, 0, 255) is Red in BGR
        cv2.circle(img, center, radius=5, color=(255, 255, 0), thickness=-1)

    # 4. Save or display the result
    cv2.imwrite('plotted_distribution.png', img)
    
    # Optional: Display the image (comment out if running in a headless environment)
    # cv2.imshow('Plotted Dots', img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    print("Successfully plotted dots and saved as 'plotted_distribution.png'")