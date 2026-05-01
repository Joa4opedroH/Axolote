import cv2
import numpy as np
import os
import glob 
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import math

pasta_imagens = '/home/julia/Pictures/Screenshots/*.png'  
imagens = glob.glob(pasta_imagens)

#hsv das bases
basemenorazul = np.array([110,70,40])
basemaiorazul = np.array([128,255,255])

basemenorlaranja = np.array ([0,100,60])   
basemaiorlaranja = np.array ([10,255,255])

def dms_para_decimal(dms, ref):
    d = float(dms[0])
    m = float(dms[1])
    s = float(dms[2])
    decimal = d + (m / 60.0) + (s / 3600.0)
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def obter_gps_foto(caminho):
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

    alt_val = gps_info.get('GPSAltitude', 0)
    if isinstance(alt_val, tuple): # Caso o valor venha como (numerador, denominador)
        altitude = float(alt_val[0]) / float(alt_val[1])
    else:
        altitude = float(alt_val)
        
    return lat, lon, altitude

def projetar_coordenadas(lat_drone, lon_drone, cx, cy, img_w, img_h, gsd, heading=0):
    
    dx = cx - (img_w / 2)
    dy = cy - (img_h / 2)
    
    #pixels pra metros
    dist_x = dx * gsd
    dist_y = -dy * gsd  

    
    rad = math.radians(heading)
    rel_x = dist_x * math.cos(rad) - dist_y * math.sin(rad)
    rel_y = dist_x * math.sin(rad) + dist_y * math.cos(rad)
    
    
    lat_final = lat_drone + (rel_y / 111111)
    lon_final = lon_drone + (rel_x / (111111 * math.cos(math.radians(lat_drone))))
    return lat_final, lon_final

def encontrar_bases(arquivo_imagem):

    #onde voce passa as imagens
    imagem = cv2.imread(arquivo_imagem)
    hsv = cv2.cvtColor(imagem,cv2.COLOR_BGR2HSV)


    for imagem in imagens:
        gps = obter_gps_foto(imagem)
        if not gps:
            print(f"Sem GPS em: {imagem}")
            continue

    gsd = obter_gps_foto(arquivo_imagem)[2]*(0.00537)/0.0036*imagem.shape[1]


    #cria as mascaras com o hsv de cada base e cria os contornos para cada mascara
    maskazul = cv2.inRange(hsv, basemenorazul, basemaiorazul)
    contornosazul, _ = cv2.findContours(maskazul, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) #none é mais preciso

    masklaranja = cv2.inRange(hsv, basemenorlaranja, basemaiorlaranja)
    contornoslaranja, _ = cv2.findContours(masklaranja, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    found_laranja = False
    found_azul = False

    for c in contornosazul:
        if cv2.contourArea(c) > 500:
            M = cv2.moments(c)

            if M["m00"] != 0:
                found_azul = True
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
        
                #cv2.circle(imagem, (cx, cy), 4, (255, 255, 255), -1)

                
                # print(f"Centro azul detectado em: X={cx}, Y={cy}")
                # vertices = cv2.approxPolyDP(c, 0.01*cv2.arcLength(c, True), True)
                # print(f"Vertices do contorno azul: {len(vertices)}")

                lat, lon = projetar_coordenadas(gps[0], gps[1], cx, cy, imagem.shape[1], imagem.shape[0], gsd)
                print(f"Base encontrada em: {lat:.6f}, {lon:.6f}")

            cv2.drawContours(imagem, [c], -1, (0, 255, 0), 3)
    

    for c in contornoslaranja:
        if cv2.contourArea(c) > 500:
            M = cv2.moments(c)

            if M["m00"] != 0:
                found_laranja = Truegsd = obter_gps_foto(arquivo_imagem)[2]*(0.00537)/0.0036*imagem.shape[1]
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
        
                #cv2.circle(imagem, (cx, cy), 4, (255, 255, 255), -1)
                
                # print(f"Centro laranja detectado em: X={cx}, Y={cy}")
                # vertices = cv2.approxPolyDP(c, 0.01*cv2.arcLength(c, True), True)
                # print(f"Vertices do contorno laranja: {len(vertices)}")


                lat, lon = projetar_coordenadas(gps[0], gps[1], cx, cy, imagem.shape[1], imagem.shape[0], gsd)
                print(f"Base encontrada em: {lat:.6f}, {lon:.6f}")

            cv2.drawContours(imagem, [c], -1, (0, 255, 0), 3)

    if not found_azul:
        print("Nenhuma base azul encontrada.")

    if not found_laranja:
        print("Nenhuma base laranja encontrada.")

    #cv2.imshow('Mascara', masklaranja)
    cv2.imshow('Resultado Final', imagem)

    while True:
        if cv2.waitKey(1000) or 0xFF == ord('q'):
            break

for imagem in imagens:
    encontrar_bases(imagem)
        


cv2.destroyAllWindows()


       


