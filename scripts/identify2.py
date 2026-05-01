import cv2
import numpy as np
import rasterio

# --- 1. CONFIGURAÇÕES ---
# IMPORTANTE: Troque este caminho para o local onde você baixou a Ortofoto (.tif) do WebODM
caminho_imagem = '/home/julia/caminho_para_a_sua_ortofoto.tif'

# Carrega a imagem com OpenCV (para processamento visual)
imagem = cv2.imread(caminho_imagem)

if imagem is None:
    print(f"ERRO: Não foi possível carregar a imagem. Verifique o caminho: {caminho_imagem}")
    exit()

# Abre o dataset geográfico com Rasterio (para traduzir pixel em GPS)
try:
    dataset_geo = rasterio.open(caminho_imagem)
except Exception as e:
    print(f"Erro ao abrir metadados geográficos: {e}")
    print("O script continuará rodando, mas sem extrair as coordenadas GPS.")
    dataset_geo = None

hsv = cv2.cvtColor(imagem, cv2.COLOR_BGR2HSV)

# --- 2. DEFINIÇÃO DE CORES (HSV) ---
basemenorazul = np.array([110, 70, 40])
basemaiorazul = np.array([128, 255, 255])

basemenorlaranja = np.array([0, 100, 60])   
basemaiorlaranja = np.array([10, 255, 255])

# --- 3. PROCESSAMENTO DE MÁSCARAS ---
maskazul = cv2.inRange(hsv, basemenorazul, basemaiorazul)
# Usando CHAIN_APPROX_SIMPLE para otimizar memória em imagens gigantes
contornosazul, _ = cv2.findContours(maskazul, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 

masklaranja = cv2.inRange(hsv, basemenorlaranja, basemaiorlaranja)
contornoslaranja, _ = cv2.findContours(masklaranja, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

found_laranja = False
found_azul = False

# --- 4. FUNÇÃO DE ANÁLISE ---
def analisar_contornos(contornos, cor_nome, cor_bgr_desenho):
    global found_azul, found_laranja
    
    for c in contornos:
        if cv2.contourArea(c) > 500:
            M = cv2.moments(c)

            if M["m00"] != 0:
                # Calcula o centroide em pixels
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                if cor_nome == "azul": found_azul = True
                if cor_nome == "laranja": found_laranja = True
                
                # Desenha o centroide e o contorno da base na imagem original
                cv2.circle(imagem, (cx, cy), 15, (255, 255, 255), -1)
                cv2.drawContours(imagem, [c], -1, cor_bgr_desenho, 5)
                
                # Conta os vértices
                vertices = cv2.approxPolyDP(c, 0.01 * cv2.arcLength(c, True), True)
                
                print(f"\n--- Base {cor_nome.upper()} Detectada! ---")
                print(f"Vértices encontrados: {len(vertices)}")
                print(f"Posição do Pixel: X={cx}, Y={cy}")
                
                # TRADUZ PIXEL PARA GPS
                if dataset_geo is not None:
                    # A função dataset.xy exige (linha, coluna), que é (cy, cx)
                    lon, lat = dataset_geo.xy(cy, cx)
                    print(f"COORDENADA GPS -> Latitude: {lat} | Longitude: {lon}")


# Roda a função para as duas cores (Passando a cor que será desenhada em BGR)
analisar_contornos(contornosazul, "azul", (255, 0, 0))       # Desenha contorno Azul
analisar_contornos(contornoslaranja, "laranja", (0, 165, 255)) # Desenha contorno Laranja

if not found_azul:
    print("\nNenhuma base azul encontrada.")
if not found_laranja:
    print("Nenhuma base laranja encontrada.")

# Fecha o arquivo geográfico para liberar memória
if dataset_geo is not None:
    dataset_geo.close()

# --- 5. EXIBIÇÃO DA IMAGEM ---
# Redimensiona a imagem apenas para visualização na tela do seu computador
altura_original, largura_original = imagem.shape[:2]

# Define a altura da janela para 800 pixels e ajusta a largura proporcionalmente
nova_altura = 800
proporcao = nova_altura / float(altura_original)
nova_largura = int(largura_original * proporcao)

imagem_exibicao = cv2.resize(imagem, (nova_largura, nova_altura))

cv2.imshow('Mapa Processado - Pressione Q para fechar', imagem_exibicao)

while True:
    # Sai do loop se a tecla 'q' for pressionada
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()