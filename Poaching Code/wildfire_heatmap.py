import cv2
import numpy as np
import requests
from datetime import datetime
import math

# Map bounding box
lat_top, lon_left = -18.192796, 14.188624
lat_bottom, lon_right = -19.537984, 17.351988

# Fuel loads (kg/m²)
fuel_dict = {
    (77, 189, 114): 2.0,    # dark green = trees
    (150, 251, 122): 0.7,   # light green = shrubs
    (255, 195, 0): 0.2      # yellow = dry grasslands
}

def generate_stepped_heatmap(original_image_path, output_path, date_str, step, radius):
    # 1. Get original dimensions
    img = cv2.imread(original_image_path)
    if img is None:
        print("Image not found")
        return
    
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, _ = img_rgb.shape

    # 2. Calculate the size of the "Small Grid"
    # If image is 1000x1000 and step is 50, grid is 20x20
    grid_h = h // step
    grid_w = w // step

    print(f"Sampling {grid_h * grid_w} points...")

    date = datetime.strptime(date_str, "%Y-%m-%d").date()

    def f(x, y):

        lon = lon_left + (x / (w - 1)) * (lon_right - lon_left)
        lat = lat_top - (y / (h - 1)) * (lat_top - lat_bottom)

        fuel_load = fuel_dict.get(tuple(img_rgb[y, x]), 0)

        # def fetch_daily_forecast(lat, lon):
        #     url = (
        #         f"https://api.open-meteo.com/v1/forecast?"
        #         f"latitude={lat}&longitude={lon}"
        #         f"&start_date={date}&end_date={date}"
        #         "&daily=temperature_2m_max,windspeed_10m_max"
        #         "&hourly=relativehumidity_2m"
        #         "&timezone=auto"
        #     )
        #     response = requests.get(url, timeout=10)
        #     data = response.json()
            
        #     # Assuming 'data' is your response.json()
        #     daily = data.get('daily', {})
        #     hourly = data.get('hourly', {})

        #     # Daily values (index 0 for the single day requested)
        #     temp_max = daily.get('temperature_2m_max', [None])[0]
        #     wind_max = daily.get('windspeed_10m_max', [None])[0]

        #     # Hourly value for 3:00 PM (Index 15)
        #     # Using .get() with a fallback empty list to prevent index errors
        #     humidity_3pm = hourly.get('relative_humidity_2m', [None] * 24)[15]
        #     return temp_max, wind_max, humidity_3pm
        def fetch_daily_forecast(lat, lon):
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                "&daily=temperature_2m_max,windspeed_10m_max"
                "&hourly=relativehumidity_2m"
                "&timezone=auto"
            )
            response = requests.get(url, timeout=10)
            data = response.json()
            
            daily_dates = data["daily"]["time"]
            temp_max = data["daily"]["temperature_2m_max"]
            wind_max = data["daily"]["windspeed_10m_max"]
            hourly_times = data["hourly"]["time"]
            hourly_humidity = data["hourly"]["relativehumidity_2m"]

            humidity_3pm = []
            for date_str in daily_dates:
                target_time = f"{date_str}T15:00"
                if target_time in hourly_times:
                    index = hourly_times.index(target_time)
                    humidity_3pm.append(hourly_humidity[index])
                else:
                    humidity_3pm.append(None)
            return daily_dates, temp_max, wind_max, humidity_3pm
        
        def grassland_fire_density_index(fuel_load, temp_max, hum, wind_max):
            if hum is None:
                hum = 50
            # gfdi_scaled = min(100, math.log1p(raw_gfdi) * 10)
            return (fuel_load ** 1.027) * math.exp(-0.009432 * ((100 - 85.7) ** 1.536) -1.523 + (0.0276*temp_max) - (0.2205*(hum ** 0.5)) + (0.6422*(wind_max ** 0.5)))
        
        dates, temp_max_list, wind_max_list, humidity_3pm_list = fetch_daily_forecast(lat, lon)

        # Find index for target date
        try:
            idx = dates.index(date_str)
        except ValueError:
            print("Target date not available in forecast.")
            exit()

        hum = humidity_3pm_list[idx]

        gfdi = grassland_fire_density_index(fuel_load, temp_max_list[idx], hum, wind_max_list[idx])

        return gfdi

    # 3. Fill the small grid by calling f(x, y)
    for row in range(1, grid_h + 1):
        for col in range(1, grid_w + 1):
            # Calculate the actual coordinate in the original image
            pixel_x = col * step
            pixel_y = row * step
            
            # Call your slow function
            # small_data[row, col] = f(pixel_x, pixel_y)
            val = f(pixel_x, pixel_y)
            ratio = val / 10

            red = int(255 - (ratio * (255 - 0)))
            green = int(255 - (ratio * (255 - 0)))
            blue = int(255 - (ratio * (255 - 0)))

            cv2.circle(img, (pixel_x, pixel_y), radius, (blue, green, red), -1)
            cv2.circle(img, (pixel_x, pixel_y), radius, (0, 0, 0), 1)

            # 5. Draw the Label (Number)
            label = f"{val:.1f}" # Format to 1 decimal place
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.4
            thickness = 1
            
            # Calculate text position (slightly above the dot)
            # Subtracting from y moves the text UP in image coordinates
            text_pos = (pixel_x - 10, pixel_y - (radius + 5))

            # Draw a black shadow/outline first for better readability
            cv2.putText(img, label, (text_pos[0]+1, text_pos[1]+1), font, 
                        font_scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
            
            # Draw the actual text in white
            cv2.putText(img, label, text_pos, font, 
                        font_scale, (255, 255, 255), thickness, cv2.LINE_AA)


    # # 4. Upscale the grid to full resolution (Interpolation)
    # # cv2.INTER_CUBIC creates smooth transitions between the points
    # smooth_data = cv2.resize(small_data, (w, h), interpolation=cv2.INTER_CUBIC)
    
    # # Ensure values stay between 0-100 after interpolation
    # smooth_data = np.clip(smooth_data, 0, 100) / 100.0

    # # 5. Map to RGB (White to Dark Red logic)
    # # 0.0 -> White (255, 255, 255) | 1.0 -> Dark Red (0, 0, 139)
    # heatmap_rgb = np.zeros((h, w, 3), dtype=np.uint8)
    
    # # Red channel: scales from 255 down to 139
    # heatmap_rgb[:,:,2] = (255 - (smooth_data * (255 - 0))).astype(np.uint8)
    # # Green and Blue: scale from 255 down to 0
    # heatmap_rgb[:,:,1] = (255 - (smooth_data * (255 - 0))).astype(np.uint8)
    # heatmap_rgb[:,:,0] = (255 - (smooth_data * (255 - 0))).astype(np.uint8)

    # # 6. Optional: Overlay on the original image (50% transparency)
    # overlay = cv2.addWeighted(img, 0.5, heatmap_rgb, 0.5, 0)

    # cv2.imwrite("smooth_web_heatmap.png", heatmap_rgb)
    # cv2.imwrite("overlay_result.png", overlay)
    # print("Heatmap generated and saved.")

    cv2.imwrite(output_path, img)
    print(f"Labeled heatmap saved to {output_path}")

# Run it
generate_stepped_heatmap("ENP Copy.png", "4.png", "2026-03-02", 200, 6)