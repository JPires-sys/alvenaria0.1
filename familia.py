"""Medidas da família de blocos usada pelo Alvenaria.py e pelo Quantitativo.py.

Todas as medidas em centímetros. Para mudar de família de blocos, altere SÓ este arquivo
(e tenha no template DXF os blocos com os nomes correspondentes).

Família atual: 19 x 39 (parede de 19 cm, bloco inteiro 19x19x39, meio-bloco 19x19x19).
A família original do programa era 14 x 29 (blocos B14, B29, B44) - ver pasta original_14x29.
"""

# --- Seção do bloco ------------------------------------------------------------
ESPESSURA = 19        # largura do bloco em planta = espessura da parede (era 14)
ALTURA_BLOCO = 19     # altura do bloco na elevação
JUNTA = 1             # junta de argamassa
ALTURA_FIADA = ALTURA_BLOCO + JUNTA   # 20 cm por fiada

# --- Comprimentos dos blocos ----------------------------------------------------
# Comprimento -> o programa procura em planta o bloco "B<comp>" e desenha na elevação
# "L<comp>" (vista lateral), "T<comp>" (vista da ponta), "BCL<comp>"/"BCT<comp>" (canaleta).
COMPRIMENTOS = [19, 39]   # era [14, 29, 44]
MEIO_BLOCO = 19           # bloco usado para arrematar portas e janelas (era 14)

# --- Furos e canaletas (quantitativo de graute) ---------------------------------
PAREDE_BLOCO = 2.5                                    # espessura das paredes do bloco
FURO_COMPRIMENTO = (39 - 3 * PAREDE_BLOCO) / 2        # 15.75 cm (era 10.75 no bloco 29)
FURO_LARGURA = ESPESSURA - 2 * PAREDE_BLOCO           # 14 cm (era 9)
FURO_AREA = FURO_COMPRIMENTO * FURO_LARGURA           # 220.5 cm² (era 96.75)
CANALETA_AREA = 255.0   # cm² de graute na seção da canaleta 19x19 (era 164 na canaleta 14x19)


def nomes(prefixo):
    """Ex.: nomes('L') -> ['L19', 'L39']"""
    return [f'{prefixo}{c}' for c in COMPRIMENTOS]


def comprimento(nome):
    """Ex.: comprimento('BCL39') -> 39"""
    return int(''.join(ch for ch in nome if ch.isdigit()))
