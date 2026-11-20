"""Gera o template de blocos da família definida em familia.py (19x39) e uma planta de exemplo.

Saídas:
  Arquivos/Template_19x39.dxf          blocos B19, B39 (planta), L/T/BCL/BCT (elevação), Bcorte, graute, lajes
                                       + portas, janela, ferros e corte copiados do exemplo original
  Arquivos/Exemplo19x39/INFILE.dxf     parede de 4 m com porta 80x220, janela 80x120/100, cantos,
                                       graute, ferros e corte A
"""
import os

import ezdxf
from ezdxf.addons import Importer

import familia as fam
from familia import ESPESSURA as E, ALTURA_BLOCO as H, PAREDE_BLOCO as P

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGINAL = os.path.join(AQUI, 'Arquivos', 'Exemplo', 'INFILE.dxf')
COPIAR = ['P60', 'P70', 'P80', 'P90', 'Janela', 'ferro', 'ferroHorizontal', 'corte']


def ret(blk, x0, y0, w, h, **kw):
    blk.add_lwpolyline([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)], close=True, dxfattribs=kw)


def hach(blk, x0, y0, w, h, cor=8):
    hatch = blk.add_hatch(color=cor)
    hatch.set_pattern_fill('AR-SAND', scale=0.05)
    hatch.paths.add_polyline_path([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)], is_closed=True)


def furos(comp):
    """Posições x dos furos de um bloco de comprimento comp (1 furo no meio-bloco, 2 no inteiro)."""
    if comp <= fam.MEIO_BLOCO:
        return [(P, comp - 2 * P)]
    return [(P, fam.FURO_COMPRIMENTO), (2 * P + fam.FURO_COMPRIMENTO, fam.FURO_COMPRIMENTO)]


def criar_blocos(doc):
    for c in fam.COMPRIMENTOS:
        b = doc.blocks.new(f'B{c}')                    # planta: c x 19
        ret(b, 0, 0, c, E)
        for x, w in furos(c):
            ret(b, x, P, w, E - 2 * P)
        b = doc.blocks.new(f'L{c}')                    # elevação lateral: c x 19
        ret(b, 0, 0, c, H)
        b.add_text(str(c), dxfattribs={'height': 4, 'insert': (1, 1)})
        b = doc.blocks.new(f'T{c}')                    # elevação da ponta: 19 x 19
        ret(b, 0, 0, E, H)
        b.add_line((0, 0), (E, H)); b.add_line((0, H), (E, 0))
        b.add_text(f'T{c}', dxfattribs={'height': 3, 'insert': (1, 1)})
        b = doc.blocks.new(f'BCL{c}')                  # canaleta lateral c x 19, com graute
        ret(b, 0, 0, c, H)
        hach(b, 0.5, P, c - 1, H - P - 0.5)
        b.add_text(f'BC{c}', dxfattribs={'height': 3, 'insert': (1, 1)})
        b = doc.blocks.new(f'BCT{c}')                  # canaleta vista em corte: U de 19 x 19
        ret(b, 0, 0, E, H)
        hach(b, P, P, E - 2 * P, H - P)
        b.add_text(f'BC{c}', dxfattribs={'height': 3, 'insert': (1, 1)})
    b = doc.blocks.new('Bcorte')                       # bloco cortado: paredes de 2,5 + furo
    ret(b, 0, 0, E, H)
    b.add_line((P, 0), (P, H)); b.add_line((E - P, 0), (E - P, H))
    b = doc.blocks.new('graute')                       # marcador em planta no furo
    ret(b, 0, 0, fam.FURO_COMPRIMENTO, fam.FURO_LARGURA)
    hach(b, 0, 0, fam.FURO_COMPRIMENTO, fam.FURO_LARGURA, cor=1)
    b.add_attdef('QUANTITATIVO', (0, -3), 's', dxfattribs={'height': 2})
    for nome, x0, w in (('Laje', -30, 30 + E + 30), ('LajeDir', 0, E + 30), ('LajeEsq', -30, 30 + E)):
        b = doc.blocks.new(nome)                       # laje de 10 cm apoiada na parede
        ret(b, x0, 0, w, 10)
        hach(b, x0, 0, w, 10)
    imp = Importer(ezdxf.readfile(ORIGINAL), doc)
    imp.import_blocks(COPIAR)
    imp.finalize()


def criar_layers(doc):
    for nome, cor in (('fiada1', 3), ('fiada2', 5), ('porta', 6), ('graute', 1), ('ferro', 2), ('corte', 4),
                      ('parede', 4), ('cinta', 4), ('verga', 4), ('laje', 8), ('ferroNcontado', 2), ('janela', 30)):
        if nome not in doc.layers:
            doc.layers.add(nome, color=cor)


def ins(msp, nome, x, y, layer, rot=0, attrs=None):
    r = msp.add_blockref(nome, (x, y), dxfattribs={'layer': layer, 'rotation': rot})
    if attrs:
        r.add_auto_attribs(attrs)
    return r


def exemplo(doc):
    msp = doc.modelspace()
    # Fiada 1 (y=0): canto esquerdo com bloco da parede perpendicular, 9 blocos de 39, canto direito
    ins(msp, 'B39', E, -20, 'fiada1', 90)              # ocupa x 0..19, y -20..19
    for x in range(20, 380, 40):
        ins(msp, 'B39', x, 0, 'fiada1')
    ins(msp, 'B39', 380, E, 'fiada1', 270)             # ocupa x 380..399, y -20..19
    # Fiada 2 (y=-150): passa por cima dos cantos; usa meio-blocos B19
    y2 = -150
    for x in range(0, 320, 40):
        ins(msp, 'B39', x, y2, 'fiada2')
    ins(msp, 'B19', 320, y2, 'fiada2')
    ins(msp, 'B39', 340, y2, 'fiada2')
    ins(msp, 'B19', 380, y2, 'fiada2')
    ins(msp, 'B39', E, y2 - 40, 'fiada2', 90)          # paredes perpendiculares (não aparecem na vista)
    ins(msp, 'B39', 380, y2 - 1, 'fiada2', 270)
    # Vãos
    ins(msp, 'P80', 100, 0, 'porta', attrs={'LARGURA': '80', 'ALTURA': '220'})
    ins(msp, 'Janela', 260, 0, 'janela', attrs={'LARGURA': '80', 'ALTURA': '120', 'PEITORIL': '100'})
    # Graute + ferros nos cantos, ferro horizontal, corte
    for x in (P, 380 + P):
        ins(msp, 'graute', x, P, 'graute', attrs={'QUANTITATIVO': 's'})
        ins(msp, 'ferro', x + fam.FURO_COMPRIMENTO / 2, E / 2, 'ferro',
            attrs={'BITOLA': '10', 'BARRA': '1', 'COMPRIMENTO': '280', 'QUANTITATIVO': 's'})
    ins(msp, 'ferroHorizontal', 0, -10, 'ferro',
        attrs={'BITOLA': '8', 'BARRAS': '2', 'COMPRIMENTO': '400', 'ALTURA': '120', 'QUANTITATIVO': 's'})
    ins(msp, 'corte', 60, 0, 'corte', attrs={'CORTE': 'A', 'LAJE': '2'})


def main():
    for destino, com_exemplo in ((os.path.join(AQUI, 'Arquivos', 'Template_19x39.dxf'), False),
                                 (os.path.join(AQUI, 'Arquivos', 'Exemplo19x39', 'INFILE.dxf'), True)):
        doc = ezdxf.new('R2018', units=4)
        criar_layers(doc)
        criar_blocos(doc)
        if com_exemplo:
            exemplo(doc)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        doc.saveas(destino)
        print('gerado', destino)


if __name__ == '__main__':
    main()
