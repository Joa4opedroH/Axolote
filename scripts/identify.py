import cv2
import numpy as np
import os
import glob 
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import math


pasta_imagens = '/home/julia/Pictures/Screenshots/*.jpg'  
imagens = glob.glob(pasta_imagens)

# HSV - Lembre-se: Use o script de calibração se não detectar nada
basemenorazul = np.array([100, 30, 100])
basemaiorazul = np.array([140, 255, 255])

basemenorlaranja = np.array([154, 30, 0])   
basemaiorlaranja = np.array([179, 255, 255])


def obter_gps_foto(caminho):
    try:
        img = Image.open(caminho)
        exif = img._getexif()
        if not exif: return None
        
        gps_info = {}
        for key, val in exif.items():
            if TAGS.get(key) == 'GPSInfo':
                for t in val:
                    gps_info[GPSTAGS.get(t)] = val[t]
        
        if 'GPSLatitude' not in gps_info: return None
        
        lat = dms_para_decimal(gps_info['GPSLatitude'], gps_info['GPSLatitudeRef'])
        lon = dms_para_decimal(gps_info['GPSLongitude'], gps_info['GPSLongitudeRef'])
        alt = float(gps_info.get('GPSAltitude', 0))
        return lat, lon, alt
    except:
        return None

def dms_para_decimal(dms, ref):
    d, m, s = float(dms[0]), float(dms[1]), float(dms[2])
    decimal = d + (m / 60.0) + (s / 3600.0)
    return -decimal if ref in ['S', 'W'] else decimal

def projetar_coordenadas(lat_drone, lon_drone, cx, cy, img_w, img_h, gsd):
    
    dx = cx - (img_w / 2)
    dy = -(cy - (img_h / 2)) 
    
    dist_x = dx * gsd
    dist_y = dy * gsd  
    
    
    lat_final = lat_drone + (dist_y / 111111)
    lon_final = lon_drone + (dist_x / (111111 * math.cos(math.radians(lat_drone))))
    return lat_final, lon_final

def encontrar_bases(caminho_imagem):
    imagem = cv2.imread(caminho_imagem)
    if imagem is None: return

    gps = obter_gps_foto(caminho_imagem)
    if not gps:
        print(f"Sem GPS em: {caminho_imagem}")
        return

    
    # GSD = (Altitude * SensorWidth) / (FocalLength * ImageWidth)
    altitude = gps[2]
    gsd = (altitude * 0.00537) / (0.0036 * imagem.shape[1])

    hsv = cv2.cvtColor(imagem, cv2.COLOR_BGR2HSV)
    
    #processamento de cores
    for cor, mask_lower, mask_upper, nome in [("azul", basemenorazul, basemaiorazul, "Azul"), 
                                             ("laranja", basemenorlaranja, basemaiorlaranja, "Laranja")]:
        
        mask = cv2.inRange(hsv, mask_lower, mask_upper)
        contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contornos:
            if cv2.contourArea(c) > 500:
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    lat, lon = projetar_coordenadas(gps[0], gps[1], cx, cy, imagem.shape[1], imagem.shape[0], gsd)
                    print(f"Base {nome} encontrada em: {lat:.6f}, {lon:.6f}")
                    cv2.drawContours(imagem, [c], -1, (0, 255, 0), 3)

    cv2.imshow('Resultado', imagem)
    cv2.waitKey(1000)

# Loop Principal
for img_path in imagens:
    encontrar_bases(img_path)

cv2.destroyAllWindows()