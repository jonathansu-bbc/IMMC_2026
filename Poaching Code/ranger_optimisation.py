import cv2
import numpy as np

# 1. Load the image in grayscale
# put heatmap you just made
img = cv2.imread('kyleshen.png', 0)
h, w = img.shape

# #ENP:
n_rows = 126
n_cols = 302

#INP:
# n_rows = 236
# n_cols = 306

# #UKNP:
# n_rows = 28
# n_cols = 52

grid_h = h // n_rows
grid_w = w // n_cols

grid_data = []

# 4. Iterate through the image and calculate average color for each grid
for i in range(n_rows):
    for j in range(n_cols):
        # Define the boundaries of the current grid cell
        y_start, y_end = i * grid_h, (i + 1) * grid_h
        x_start, x_end = j * grid_w, (j + 1) * grid_w
        
        # Crop the cell
        cell = img[y_start:y_end, x_start:x_end]
        
        # Calculate the average grayscale value (0=Black, 255=White)
        avg_color = np.mean(cell)
        
        # Store (average_color, row_index, col_index, pixel_coords)
        grid_data.append({
            'avg': avg_color,
            'pos': (i, j),
            'coords': (x_start, y_start)
        })

# 5. Sort by average color (lowest value = most black/highest risk)
# We take the top 150
top_risky = sorted(grid_data, key=lambda x: x['avg'])[:150] # no of rangers

# Create a colored version of the original to draw on
output_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

# Draw the 150 most 'black' grids in red/blue
for cell in top_risky:
    x, y = cell['coords']
    # Draw rectangle (top-left to bottom-right)
    cv2.rectangle(output_img, (x, y), (x + grid_w, y + grid_h), (0, 0, 255), 2) # (0, 0, 255) r, (255, 0, 0) b

# Save or show the result
cv2.imwrite('kyleshen1.png', output_img)
# NAME IT RESULT FILE