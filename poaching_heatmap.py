import cv2
import numpy as np

# DO THIS TSTSTT5S

# #ENP:
d_h_i = 0.05  # Weighting on H at day (0.05)
d_q_i = 0.15  # Weighting on Q at day (0.15)
n_h_i = 0.05  # Weighting on H at night (0.05)
n_q_i = 0.30  # Weighting on Q at night (0.36)

# #INP:
# d_h_i = 0.05
# d_q_i = 0.05
# n_h_i = 0.1
# n_q_i = 0.1

#UKNP:
# d_h_i = 0.05
# d_q_i = 0.0
# n_h_i = 0.1
# n_q_i = 0.0

def f1_v(x): return -0.15 * np.log(x + np.exp(-4)) + 0.4
def f2_v(x): return 0.15 * np.log(x + np.exp(-4)) + 0.6

#1: -, attraction
#2: +, repulsion

# if drop a lanmark make i and j 0 (weighting)
enp = {# (RGB, (animal region, poacher region, max_dist, animal a/r, poacher a/r, animal day, poacher day, animal night, poacher night))
    "t": ((77, 189, 114), (0.75, 1.0, 300, 1, 1, 0, 0, 0, 0)), # last 4: 0.1, 0.05, 0.3, 0.02
    "s": ((150, 251, 122), (1.0, 0.75, 350, 1, 1, 0, 0, 0, 0)), # last 4: 0.05, 0.03, 0.1, 0.01
    "g": ((255, 195, 0), (0.5, 0.75, 570, 1, 1, 0, 0, 0, 0)), # last 4: 0.05, 0.02, 0.05, 0.01
    "p": ((142, 185, 219), (1.0, 0.25, 700, 1, 2, 0, 0, 0, 0)), # last 4: 0.35, 0.03, 0.05, 0.03
    "w": ((0, 34, 255), (1.0, 0.25, 480, 1, 1, 0.25, 0.02, 0.5, 0.1)), #Pnight was 0.02
    "r": ((255, 225, 0), (0.25, 1.0, 400, 2, 1, 0.05, 0.3, 0, 0.15)), #Pnight was 0.2
    "c": ((255, 0, 0), (0.25, 0.25, 570, 2, 2, 0.1, 0.2, 0.05, 0.18)), #Pday was 0.25, Pnight was 0.2
    "f": ((0, 0, 0), (0.25, 1.0, 380, 1, 1, 0, 0.2, 0, 0.2))  #Pday was 0.15, Pnight was 0.15
}

inp = {
    "o": ((114, 137, 67), (1.0, 0.5, 385, 1, 1, 0.2, 0.05, 0.3, 0.05)),
    "m": ((232, 231, 185), (1.0, 0.5, 260, 1, 1, 0.18, 0.05, 0.1, 0.05)),
    "g": ((244, 201, 123), (0.5, 0.25, 190, 1, 1, 0.18, 0.05, 0.1, 0.05)),
    "b": ((42, 55, 127), (0.25, 1.0, 450, 2, 1, 0.16, 0.1, 0.1, 0.05)),
    "w": ((160, 209, 216), (0.25, 0.25, 150, 1, 2, 0.08, 0.1, 0.2, 0.05)),
    "r": ((255, 225, 0), (0.25, 1.0, 160, 2, 1, 0.15, 0.5, 0.05, 0.6)),
    "c": ((255, 0, 0), (0.25, 0.5, 570, 2, 2, 0.1, 0.1, 0.05, 0.05))
}

uknp = {
    "m": ((0, 110, 59), (0.75, 0.5, 404, 2, 1, 0.21, 0.05, 0.1, 0.05)),
    "l": ((254, 200, 132), (1.0, 0.5, 266, 1, 1, 0.15, 0.05, 0.1, 0.05)),
    "s": ((137, 163, 212), (0.25, 0.25, 690, 1, 2, 0.11, 0.1, 0.05, 0.1)),
    "p": ((66, 185, 126), (0.25, 1.0, 1086, 2, 1, 0.14, 0.05, 0.05, 0.05)),
    "w": ((108, 170, 221), (1.0, 0.25, 150, 1, 2, 0.06, 0.05, 0.4, 0.05)),
    "o": ((5, 86, 167), (0.25, 0.25, 310, 1, 2, 0.11, 0.1, 0.1, 0.05)),
    "r": ((255, 225, 0), (0.25, 1.0, 200, 2, 1, 0.11, 0.5, 0.05, 0.6)),
    "c": ((255, 0, 0), (0.25, 0.25, 304, 2, 2, 0.16, 0.1, 0.05, 0.05))
}

def generate_risk_heatmap(map, image_path, output_path, time):

    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        print("Error: Image not found.")
        return
    
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    h, w, _ = img_rgb.shape

    d_maps = {}

    d = {}
    d_h = np.full((h, w), 0.25)
    d_q = np.full((h, w), 0.25)
    
    for name, (colour, info) in map.items():
        mask = np.all(img_rgb == colour, axis=-1)
        d[name] = np.all(img_rgb == colour, axis=-1)

        d_h[d[name]] = info[0]
        d_q[d[name]] = info[1]
        
        if not np.any(mask):
            d_maps[name] = np.full((h, w), 400.0 / info[2])
        else:
            binary_mask = np.where(mask, 0, 1).astype(np.uint8)
            dist = cv2.distanceTransform(binary_mask, cv2.DIST_L2, 5)
            d_maps[name] = dist / info[2]

    time = int(time)

    if (time > 6 and time < 20): # 5, 21

        p_r = d_h_i * d_h
        p_p = d_q_i * d_q

        for name, info in map.items():
            if (info[1][3] == 1):
                p_r = p_r + info[1][5] * f1_v(d_maps[name])
            else:
                p_r = p_r + info[1][5] * f2_v(d_maps[name])

        for name, info in map.items():
            if (info[1][4] == 1):
                p_p = p_p + info[1][6] * f1_v(d_maps[name])
            else:
                p_p = p_p + info[1][6] * f2_v(d_maps[name])

    else:

        p_r = n_h_i * d_h
        p_p = n_q_i * d_q

        for name, info in map.items():
            if (info[1][3] == 1):
                p_r = p_r + info[1][7] * f1_v(d_maps[name])
            else:
                p_r = p_r + info[1][7] * f2_v(d_maps[name])

        for name, info in map.items():
            if (info[1][4] == 1):
                p_p = p_p + info[1][8] * f1_v(d_maps[name])
            else:
                p_p = p_p + info[1][8] * f2_v(d_maps[name])

    risk_map = 0.8 * p_r + 0.2 * p_p
    risk_map = np.clip(risk_map, 0, 1)

    heatmap = np.zeros((h, w, 3), dtype=np.uint8)

    heatmap[:,:,2] = (255 - (risk_map * (255 - 0))).astype(np.uint8)
    heatmap[:,:,1] = (255 - (risk_map * (255 - 0))).astype(np.uint8)
    heatmap[:,:,0] = (255 - (risk_map * (255 - 0))).astype(np.uint8)
    
    cv2.imwrite(output_path, heatmap)
    print(f"Risk heatmap generated successfully at: {output_path}")

# Usage
t = input("Time: ")
generate_risk_heatmap(enp, "ENP.png", "real1.png", t) #TSTSTTS