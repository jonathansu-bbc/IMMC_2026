import json
import math
import os
import random
import requests
from datetime import datetime, timedelta
from PIL import Image, ImageDraw

# --- CONFIG ---
base_path = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(base_path, "enp_vege_map.png")
data_file = os.path.join(base_path, "fuel_data.json")
mock_file = os.path.join(base_path, "mock_weather_data.json")

# SET TO False TO FETCH REAL WEATHER FROM OPEN-METEO
MOCK_MODE = True

# --- VARIABLES ---
GFDI_THRESHOLD = 7.5
CLUSTER_THRESHOLD_PX = 25
SPACING_KM = 1.0 
BURN_DURATION_DAYS = 2 
PERSONNEL_PER_KM = 6  
MAX_STAFF_AVAILABLE = 145  # Total personnel available per day -> you can change
BURN_RATE = 0.5
WEATHER_FORECAST_RANGE = 60 #Amount of days the weather forecast will be generated for
HUM_RAND = 0.5
BURN_TIME = 2 #days to complete a burn
ANNUAL_TEMP = 31 #average annual temperature


wind_dir_speed_rose = {
    0:    ((2,5,10,20,30,40,50), (5.6/8760, 35.5/8760, 85.2/8760, 70.6/8760, 4.5/8760, 0, 0)), # N
    22.5: ((2,5,10,20,30,40,50), (8.5/8760, 39.4/8760, 122.8/8760, 165.6/8760, 15.9/8760, 0.5/8760, 0)), # NNE
    45:   ((2,5,10,20,30,40,50), (5.6/8760, 39.7/8760, 167.8/8760, 395.6/8760, 123.4/8760, 7.1/8760, 0)), # NE
    67.5: ((2,5,10,20,30,40,50), (7.7/8760, 45.4/8760, 216.4/8760, 777.3/8760, 362.5/8760, 45.8/8760, 0.3/8760)), #ENE
    90: ((2,5,10,20,30,40,50), (5.2/8760, 41/8760, 220.3/8760, 928.6/8760, 175.7/8760, 8.3/8760, 0.1/8760)), # E
    112.5:   ((2,5,10,20,30,40,50), (8.4/8760, 45.5/8760, 197.0/8760, 314.1/8760, 18.5/8760, 0.7/8760, 0)), # ESE
    135:((2,5,10,20,30,40,50), (5.2/8760, 38/8760, 152.4/8760, 173.1/8760, 10.7/8760, 0.5/8760, 0)), # SE
    157.5:  ((2,5,10,20,30,40,50), (8.4/8760, 37.2/8760, 143.3/8760, 228.4/8760, 17.5/8760, 0.5/8760, 0)), # SSE
    180:((2,5,10,20,30,40,50), (6.5/8760, 32.9/8760, 134.1/8760, 423.2/8760, 89.1/8760, 2.5/8760, 0)), # S
    202.5:  ((2,5,10,20,30, 40,50), (7.9/8760, 32/8760, 122.1/8760, 450.2/8760, 236/8760, 34.3/8760, 0.6/8760)), # SSW
    225:((2,5,10,20,30,40,50), (5.2/8760, 27.3/8760, 99.2/8760, 248.5/8760, 67.9/8760, 11.7/8760, 0.2/8760)), # SW
    247.5:  ((2,5,10,20,30,40,50), (7.6/8760, 27.9/8760, 91.7/8760, 145.7/8760, 18.8/8760, 0.9/8760, 0)), # WSW
    270:((2,5,10,20,30,40,50), (6/8760, 25.2/8760, 79.1/8760, 94.1/8760, 7.8/8760, 0.2/8760, 0)), # W
    292.5:  ((2,5,10,20,30,40,50), (7/8760, 29.3/8760, 70.5/8760, 58.9/8760, 3.6/8760, 0.1/8760, 0)), # WNW
    315:((2,5,10,20,30,40,50), (6.2/8760, 30.3/8760, 61.5/8760, 38.8/8760, 2.3/8760, 0.1/8760, 0)), # NW
    337.5:  ((2,5,10,20,30,40,50), (8.1/8760, 34.7/8760, 75.2/8760, 47/8760, 2.4/8760, 0, 0)), # NNW
}

MIN_HUM, MAX_HUM = 30, 70 
MIN_WIND, MAX_WIND = 5, 25 


# Map Bounds
LAT_TOP, LON_LEFT = -18.192796, 14.188624
LAT_BOTTOM, LON_RIGHT = -19.537984, 17.351988

fuel_growth_map = {
    (77, 189, 114): (2, 0.0025), #sparse mopane forest
    (150, 251, 122): (0.7, 0.00115), #shrubland
    (255, 195, 0): (0.2, 0.0009) #grassland
}

# --- DATA INITIALIZATION ---

def init_data(width, height, pixels):
    print("Initializing fuel database from image (exact RGB match)...")
    data = []
    lat_s = SPACING_KM / 111.32
    lon_s = SPACING_KM / (111.32 * math.cos(math.radians((LAT_TOP + LAT_BOTTOM) / 2)))

    curr_lat = LAT_TOP
    while curr_lat >= LAT_BOTTOM:
        curr_lon = LON_LEFT
        while curr_lon <= LON_RIGHT:
            px = int(((curr_lon - LON_LEFT) / (LON_RIGHT - LON_LEFT)) * (width - 1))
            py = int(((LAT_TOP - curr_lat) / (LAT_TOP - LAT_BOTTOM)) * (height - 1))
            if 0 <= px < width and 0 <= py < height:
                r, g, b = pixels[px, py][:3]
                match = fuel_growth_map.get((r, g, b))
                if match:
                    data.append({
                        "id": len(data), "lat": round(curr_lat, 6), "lon": round(curr_lon, 6),
                        "current_fuel_load": match[0], "max_capacity": match[0],
                        "growth_rate": match[1], "most_recent_burn_date": "Never",
                        "px": px, "py": py
                    })
            curr_lon += lon_s
        curr_lat -= lat_s
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)
    return data

# --- WEATHER SYSTEM ---

def sample_wind():
    directions = list(wind_dir_speed_rose.keys())
    weights_dir = [sum(wind_dir_speed_rose[d][1]) for d in directions]
    dir_chosen = random.choices(directions, weights=weights_dir, k=1)[0]

    # Get the bins and probabilities for the chosen direction
    speed_bins, probs = wind_dir_speed_rose[dir_chosen]

    # Choose a bin based on weights
    bin_idx = random.choices(range(len(speed_bins)), weights=probs, k=1)[0]

    # Determine the lower and upper bound of that bin
    if bin_idx == 0:
        lower = 0
    else:
        lower = speed_bins[bin_idx - 1]
    upper = speed_bins[bin_idx]

    # Pick a random speed within the bin
    speed_chosen = random.uniform(lower, upper)
    return dir_chosen, speed_chosen

# --- Mock data generation ---
def generate_mock_data(points, mock_file):
    print(f"Generating unique Mock profiles for {len(points)} points...")
    start_date = datetime.now()
    date_list = [(start_date + timedelta(days=x)).strftime("%Y-%m-%d") for x in range(WEATHER_FORECAST_RANGE)]
    
    mock_responses = []

    for p in points:
        t_off, h_off = random.uniform(-3, 3), random.uniform(-8, 8)
        daily_t, daily_w, daily_d, hourly_h_3pm = [], [], [], []

        for i in range(len(date_list)):
            # Temperature
            daily_t.append(round(ANNUAL_TEMP + t_off + random.uniform(-1, 1), 1))
            
            # Wind direction & speed (weighted)
            dir_chosen, speed_chosen = sample_wind()
            daily_d.append(round(dir_chosen))
            daily_w.append(round(speed_chosen))
            
            # 3 PM humidity
            if random.random() < HUM_RAND:
                h_raw = random.randint(MIN_HUM, MAX_HUM)
            else:
                if random.random() < 0.5:
                    h_raw = random.randint(0, MIN_HUM - 1)
                else:
                    h_raw = random.randint(MAX_HUM + 1, 100)
            h_raw = max(5, min(95, int(h_raw)))
            hourly_h_3pm.append(h_raw)

        # Store the mock data
        mock_responses.append({
            "latitude": p['lat'],
            "longitude": p['lon'],
            "daily": {
                "time": date_list,
                "temperature_2m_max": daily_t,
                "windspeed_10m_max": daily_w,
                "winddirection_10m_dominant": daily_d
            },
            "hourly_3pm": {
                "time": date_list,           # One entry per day
                "relative_humidity_2m": hourly_h_3pm
            }
        })

    # Save to JSON
    with open(mock_file, 'w') as f:
        json.dump(mock_responses, f, indent=4)

    print(f"Saved mock weather data to {mock_file}")

def get_weather_data(points, mock_file_path=mock_file):
    if MOCK_MODE:
        if not os.path.exists(mock_file_path): 
            generate_mock_data(points, mock_file_path)
        with open(mock_file_path, 'r') as f: 
            return json.load(f)
    else:
        all_results = []
        for p in points:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={p['lat']}&longitude={p['lon']}&daily=temperature_2m_max,windspeed_10m_max,winddirection_10m_dominant&hourly=relative_humidity_2m&timezone=auto"
            try:
                r = requests.get(url).json()
                all_results.append(r)
            except: 
                all_results.append(None)
        return all_results

# --- CALCULATIONS & DRAWING ---

def calculate_gfdi(fuel, temp, hum, wind):
    curf = math.e**(-0.009432*((100-85.7)**1.536))
    return (fuel**1.027)*(curf)*math.exp(-1.523 + 0.0276*temp - 0.2205*math.sqrt(hum) + 0.6422*math.sqrt(wind))

def simulate_growth(p, date_str):
    base_f = p.get('current_fuel_load', 0.0)
    if p.get('most_recent_burn_date') == "Never": return base_f
    days = (datetime.strptime(date_str, "%Y-%m-%d") - datetime.strptime(p['most_recent_burn_date'], "%Y-%m-%d")).days
    return min(p['max_capacity'], base_f + (max(0, days) * p.get('growth_rate', 0.001) * 1))

def draw_arrow(draw, cx, cy, angle_deg, length, color, width=3):
    rad = math.radians(angle_deg - 90)
    ex, ey = cx + length * math.cos(rad), cy + length * math.sin(rad)
    draw.line([cx, cy, ex, ey], fill=color, width=width)
    draw.polygon([(ex, ey), (ex-8*math.cos(rad-0.5), ey-8*math.sin(rad-0.5)), (ex-8*math.cos(rad+0.5), ey-8*math.sin(rad+0.5))], fill=color)

def pixel_to_latlon(px, py, width, height):
    lon = LON_LEFT + (px / (width - 1)) * (LON_RIGHT - LON_LEFT)
    lat = LAT_TOP - (py / (height - 1)) * (LAT_TOP - LAT_BOTTOM)
    return round(lat, 6), round(lon, 6)

# --- MAIN ANALYSIS ---

def run_fire_analysis():
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found."); return

    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    master_data = init_data(img.width, img.height, img.load()) if not os.path.exists(data_file) else json.load(open(data_file, 'r'))
    weather_database = get_weather_data(master_data)
    
    dates = [datetime.strptime(p['most_recent_burn_date'], "%Y-%m-%d") for p in master_data if p['most_recent_burn_date'] != "Never"]
    last_op_date = max(dates) if dates else datetime.now() - timedelta(days=1)

    print(f"\nSystem Online. Last Operation: {last_op_date.strftime('%Y-%m-%d')}")
    target_date_str = input("Enter Forecast Risk Date (YYYY-MM-DD): ")
    high_risk_points = []
    for idx, p in enumerate(master_data):
        if idx >= len(weather_database): continue
        w = weather_database[idx]
        sim_f = simulate_growth(p, target_date_str)
        try:
            f_idx = w["daily"]["time"].index(target_date_str)
            h_idx = w["hourly_3pm"]["time"].index(target_date_str)
            risk_gfdi = calculate_gfdi(
                sim_f,
                w["daily"]["temperature_2m_max"][f_idx],
                w["hourly_3pm"]["relative_humidity_2m"][h_idx],
                w["daily"]["windspeed_10m_max"][f_idx]
            )
            if risk_gfdi > GFDI_THRESHOLD:
                p.update({'risk_gfdi': risk_gfdi, 'weather': w, 'sim_fuel': sim_f})
                high_risk_points.append(p)
                draw.ellipse([p['px']-2, p['py']-2, p['px']+2, p['py']+2], fill=(255, 140, 0))
        except: continue

    clusters, visited = [], set()
    for i, p in enumerate(high_risk_points):
        if i in visited: continue
        curr, stack = [], [i]; visited.add(i)
        while stack:
            idx = stack.pop(); curr.append(high_risk_points[idx])
            for j, p2 in enumerate(high_risk_points):
                if j not in visited and math.sqrt((high_risk_points[idx]['px']-p2['px'])**2 + (high_risk_points[idx]['py']-p2['py'])**2) < CLUSTER_THRESHOLD_PX:
                    visited.add(j); stack.append(j)
        clusters.append(curr)

    cluster_ranks = sorted([{'pts': c, 'forecast_gfdi': sum(p['risk_gfdi'] for p in c)/len(c), 'avg_fuel': sum(p['sim_fuel'] for p in c)/len(c)} for c in clusters], key=lambda x: x['forecast_gfdi'], reverse=True)

    # --- STAFF-BASED SCHEDULING (DATE-CENTRIC, 2-DAY BLOCKS) ---
    all_forecast_dates = weather_database[0]["daily"]["time"]
    staff_usage_per_day = {d: 0 for d in all_forecast_dates}
    pending_burns = []
    scheduled_cluster_ids = set()
    schedule_no = 1  # start numbering from 1

    print("\n" + "="*175)
    print(f"{'No.':<3} | {'ID':<5} | {'Risk GFDI':<10} | {'Avg Fuel':<10} | {'Start Date':<12} | {'End Date':<12} | {'Wind':<6} | {'Hum%':<5} | {'Staff':<6} | {'Ignition Line Coordinates (LAT,LON)':<46} | {'Status'}")
    print("-" * 175)

    # LOOP 1: Forecast Days (Earliest first)
    for d_idx, d_str in enumerate(all_forecast_dates):
        if d_str <= last_op_date.strftime("%Y-%m-%d"): continue
        if d_idx + BURN_TIME >= len(all_forecast_dates): break 
        
        day_plus_1 = all_forecast_dates[d_idx + BURN_TIME] # changes the duration of burn

        # LOOP 2: Clusters (Priority by Risk)
        for i, data in enumerate(cluster_ranks):
            if i in scheduled_cluster_ids: continue
            
            pts = data['pts']
            w_sample = pts[0]['weather']
            
            try:
                h_idx1 = w_sample["hourly_3pm"]["time"].index(d_str)
                h_val1 = w_sample["hourly_3pm"]["relative_humidity_2m"][h_idx1]
                w_val1 = w_sample["daily"]["windspeed_10m_max"][d_idx]
                w_dir = w_sample["daily"]["winddirection_10m_dominant"][d_idx]

                h_idx2 = w_sample["hourly_3pm"]["time"].index(day_plus_1)
                h_val2 = w_sample["hourly_3pm"]["relative_humidity_2m"][h_idx2]
                w_val2 = w_sample["daily"]["windspeed_10m_max"][d_idx + 1]
                # Weather window check for both days
                if (MIN_HUM <= h_val1 <= MAX_HUM) and (MIN_WIND <= w_val1 <= MAX_WIND) and \
                   (MIN_HUM <= h_val2 <= MAX_HUM) and (MIN_WIND <= w_val2 <= MAX_WIND):
                    
                    cx, cy = sum(p['px'] for p in pts)/len(pts), sum(p['py'] for p in pts)/len(pts)
                    wind_rad = math.radians(w_dir - 90)
                    rel_y = []
                    for p in pts:
                        dx, dy = p['px'] - cx, p['py'] - cy
                        rel_y.append(-dx * math.sin(wind_rad) + dy * math.cos(wind_rad))
                    needed_staff = max(6, int(((max(rel_y) - min(rel_y) + 10) * PERSONNEL_PER_KM) / 50))

                    # 2-Day Staff occupancy check
                    if (staff_usage_per_day[d_str] + needed_staff <= MAX_STAFF_AVAILABLE) and \
                       (staff_usage_per_day[day_plus_1] + needed_staff <= MAX_STAFF_AVAILABLE):
                        
                        staff_usage_per_day[d_str] += needed_staff
                        staff_usage_per_day[day_plus_1] += needed_staff
                        scheduled_cluster_ids.add(i)

                        fuel_at_burn = simulate_growth(pts[0], d_str)
                        burn_id = f"B-{i+1}"
                        
                        # Drawing logic
                        rel_coords = []
                        for p in pts:
                            dx, dy = p['px'] - cx, p['py'] - cy
                            rel_coords.append((dx * math.cos(wind_rad) + dy * math.sin(wind_rad), -dx * math.sin(wind_rad) + dy * math.cos(wind_rad)))
                        min_xr, max_xr = min(c[0] for c in rel_coords) - 5, max(c[0] for c in rel_coords) + 5
                        min_yr, max_yr = min(c[1] for c in rel_coords) - 5, max(c[1] for c in rel_coords) + 5
                        corners = []
                        for xr, yr in [(min_xr, min_yr), (max_xr, min_yr), (max_xr, max_yr), (min_xr, max_yr)]:
                            corners.append((cx + xr * math.cos(wind_rad) - yr * math.sin(wind_rad), cy + xr * math.sin(wind_rad) + yr * math.cos(wind_rad)))
                        
                        draw.polygon(corners, outline="blue", width=2)
                        draw_arrow(draw, cx, cy, w_dir, 20, "yellow")
                        draw_arrow(draw, cx, cy, w_dir + 180, 20, "deeppink") 
                        draw.text((cx+5, cy+5), burn_id, fill="white")

                        # --- IGNITION LINE (UPWIND BOUNDARY) ---
                        # The line between (min_xr, min_yr) and (min_xr, max_yr) is the upwind edge
                        lx1 = cx + max_xr * math.cos(wind_rad) - max_yr * math.sin(wind_rad)
                        ly1 = cy + max_xr * math.sin(wind_rad) + max_yr * math.cos(wind_rad)
                        lx2 = cx + max_xr * math.cos(wind_rad) - min_yr * math.sin(wind_rad)
                        ly2 = cy + max_xr * math.sin(wind_rad) + min_yr * math.cos(wind_rad)
                        draw.line([lx1, ly1, lx2, ly2], fill="white", width=4)
                        # Convert ignition line endpoints to lat/lon
                        lat1, lon1 = pixel_to_latlon(lx1, ly1, img.width, img.height)
                        lat2, lon2 = pixel_to_latlon(lx2, ly2, img.width, img.height)
                        
                        print(f"{schedule_no:<3} | {burn_id:<5} | {data['forecast_gfdi']:<10.2f} | {data['avg_fuel']:<10.2f} | {d_str:<12} | {day_plus_1:<12} | {w_val1:<6.1f} | {h_val1:<5.1f} | {needed_staff:<6} | {lat1:<10},{lon1:<10} to {lat2:<10},{lon2:<10} | SCHEDULED")
                        pending_burns.append({'pts': pts, 'date': d_str, 'reduced_fuel': fuel_at_burn * BURN_RATE})
                        schedule_no +=1

            except: continue

    # Show unscheduled
    for i, data in enumerate(cluster_ranks):
        if i not in scheduled_cluster_ids:
            pts = data['pts']
            min_x, max_x = min(p['px'] for p in pts), max(p['px'] for p in pts)
            min_y, max_y = min(p['py'] for p in pts), max(p['py'] for p in pts)
            draw.rectangle([min_x-5, min_y-5, max_x+5, max_y+5], outline="red", width=2)
            print(f"B-{i+1:<3} | {data['forecast_gfdi']:<10.2f} | {data['avg_fuel']:<10.2f} | {'No Window':<12} | {'-':<12} | -      | -     | -      | UNSCHEDULED")

    # --- PERSONNEL REPORT ---
    print("\n" + "="*50)
    print(f"{'DATE':<15} | {'PERSONNEL USED':<15} | {'CAPACITY'}")
    print("-" * 50)
    for d_str in all_forecast_dates:
        usage = staff_usage_per_day[d_str]
        if usage > 0:
            pct = (usage / MAX_STAFF_AVAILABLE) * 100
            print(f"{d_str:<15} | {usage:<15} | {pct:.1f}%")
    print("="*50)

    img.show()
    if pending_burns and input("\nConfirm Schedule? (yes/no): ").lower() == 'yes':
        for burn in pending_burns:
            recovery_date = (datetime.strptime(burn['date'], "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")
            for p_ptr in burn['pts']:
                master_data[p_ptr['id']].update({'current_fuel_load': burn['reduced_fuel'], 'most_recent_burn_date': recovery_date})
        with open(data_file, 'w') as f:
            json.dump(master_data, f, indent=4)
        print("Confirmed.")

if __name__ == "__main__":
    run_fire_analysis()