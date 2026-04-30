import cv2
import numpy as np

imagem = cv2.imread('/home/julia/Pictures/Screenshots/Screenshot 2026-04-30 032411.png')
hsv = cv2.cvtColor(imagem,cv2.COLOR_BGR2HSV)


basemenorazul = np.array([110,70,40])
basemaiorazul = np.array([128,255,255])

basemenorlaranja = np.array ([0,100,60])   
basemaiorlaranja = np.array ([10,255,255])

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
            
    
            cv2.circle(imagem, (cx, cy), 4, (255, 255, 255), -1)
            
            print(f"Centro azul detectado em: X={cx}, Y={cy}")
            vertices = cv2.approxPolyDP(c, 0.01*cv2.arcLength(c, True), True)
            print(f"Vertices do contorno azul: {len(vertices)}")

        cv2.drawContours(imagem, [c], -1, (0, 255, 0), 3)
  

for c in contornoslaranja:
    if cv2.contourArea(c) > 500:
        M = cv2.moments(c)

        if M["m00"] != 0:
            found_laranja = True
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
    
            cv2.circle(imagem, (cx, cy), 4, (255, 255, 255), -1)
            
            print(f"Centro laranja detectado em: X={cx}, Y={cy}")
            vertices = cv2.approxPolyDP(c, 0.01*cv2.arcLength(c, True), True)
            print(f"Vertices do contorno laranja: {len(vertices)}")
        cv2.drawContours(imagem, [c], -1, (0, 255, 0), 3)

if not found_azul:
    print("Nenhuma base azul encontrada.")

if not found_laranja:
    print("Nenhuma base laranja encontrada.")

#cv2.imshow('Mascara', masklaranja)
cv2.imshow('Resultado Final', imagem)

while True:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()


       


