"""Alvenaria Estrutural - gera as elevações das paredes a partir da planta de fiadas (INFILE.dxf).

Versão família 19 x 39. As medidas dos blocos ficam em familia.py.
Uso:  python Alvenaria.py              (abre a janela e pede a altura)
      python Alvenaria.py --altura 280 (sem janela, útil para testes)
"""
import math
import sys

import ezdxf as ez
import numpy as np

import familia as fam
from familia import ESPESSURA as E, ALTURA_FIADA, ALTURA_BLOCO, MEIO_BLOCO, COMPRIMENTOS

MAIOR = max(COMPRIMENTOS)
BLOCO_MEIO = f'L{MEIO_BLOCO}'


def trunc(n, c):
    a = 10 ** c
    return int(n * a) / float(a)


def pedir_altura():
    """Janela que pede a altura da parede (pé-direito) em cm."""
    try:
        import PySimpleGUI as sg
    except ImportError:  # PySimpleGUI saiu do PyPI; FreeSimpleGUI é o fork compatível
        import FreeSimpleGUI as sg
    sg.theme('DarkBrown5')
    layout = [[sg.Text('Software de Alvenaria Estrutural')],
              [sg.Text(f'Família de blocos: {E}x{MAIOR}  (blocos de {", ".join(map(str, COMPRIMENTOS))} cm)')],
              [sg.Text('Altura da Parede em cm: '), sg.Input()],
              [sg.Button('Ok', bind_return_key=True), sg.Button('Cancel')],
              [sg.ProgressBar(100)]]
    window = sg.Window('Alvenaria', layout, icon='./images/tijolo.ico', location=(50, 50))
    altura = ''
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancel'):
            break
        if event == 'Ok':
            try:
                altura = float(values[0].replace(',', '.'))
                if altura <= 0:
                    raise ValueError
                break
            except ValueError:
                sg.popup('Por favor insira um valor!', title='Aviso', keep_on_top=True)
    window.close()
    return altura


def bloco(model, nome, x, y, layer='parede'):
    model.add_blockref(nome, (x, y), dxfattribs={'layer': layer, 'color': 4, 'rotation': 0})


def eixos_da_fiada(model, layer):
    """Eixos (baixo, meio, cima) da fiada, tirados de um bloco com rotação 0 do layer."""
    for b in model.query(f'INSERT[layer=="{layer}"]'):
        if b.dxf.name in fam.nomes('B') and round(b.dxf.rotation) % 360 == 0:
            y = b.dxf.insert[1]
            return round(y, 3), round(y + E / 2, 3), round(y + E, 3)
    return None


def vista_do_bloco(entity, eixos):
    """Converte um bloco de planta em (nome do bloco da elevação, x) ou None se não pertence à fiada."""
    comp = fam.comprimento(entity.dxf.name)
    rot = round(entity.dxf.rotation) % 360
    ix, iy = entity.dxf.insert[0], entity.dxf.insert[1]
    baixo, meio, cima = eixos
    if rot == 0:
        return f'L{comp}', ix
    if rot == 180:
        return f'L{comp}', ix - comp
    if rot == 270:  # bloco "descendo" a partir do ponto de inserção
        topo, centro, base, x = iy, iy - comp / 2, iy - comp, ix
    elif rot == 90:  # bloco "subindo" a partir do ponto de inserção
        topo, centro, base, x = iy + comp, iy + comp / 2, iy, ix - E
    else:
        print('O bloco esta desalinhado!', entity.dxf.rotation)
        return None
    if round(topo, 3) == cima or round(centro, 3) == meio or round(base, 3) == baixo:
        return f'T{comp}', x
    return None  # bloco da parede perpendicular que não aparece nesta fiada


def recortar_vao(model, x_ini, x_fim, y_ini, y_fim):
    """Apaga os blocos da elevação dentro do vão e arremata as bordas com meio-bloco."""
    folga = MEIO_BLOCO + 1
    m1, n1 = int((x_ini - folga) * 1000), int(x_fim * 1000)
    m2, n2 = int(y_ini * 1000), int(y_fim * 1000)
    for b in model.query('INSERT[layer=="parede"]'):
        px, py = trunc(b.dxf.insert[0], 2), trunc(b.dxf.insert[1], 2)
        if int(px * 1000) in range(m1, n1) and int(py * 1000) in range(m2, n2):
            comp = fam.comprimento(b.dxf.name)
            model.delete_entity(b)
            if int(px * 1000) in range(m1, m1 + folga * 1000):           # sobra à esquerda do vão
                bloco(model, BLOCO_MEIO, px, py)
            if px + comp > x_fim + 0.5 and int(px * 1000) in range(n1 - folga * 1000, n1):  # sobra à direita
                bloco(model, BLOCO_MEIO, px + folga, py)


def trocar_por_canaleta(model, x1, x2, y1, y2, layer):
    """Troca blocos L<c> da faixa por canaletas BCL<c> (vergas e contravergas)."""
    for b in model.query('INSERT[layer=="parede"]'):
        x, y = int(b.dxf.insert[0] * 1000), int(b.dxf.insert[1] * 1000)
        if x in range(x1, x2) and y in range(y1, y2) and b.dxf.name.startswith('L'):
            nome = 'BC' + b.dxf.name
            model.delete_entity(b)
            bloco(model, nome, x / 1000, y / 1000, layer)


def gerar(pedireito, entrada='INFILE.dxf', saida='OUTFILE.dxf'):
    fiadas = math.ceil(pedireito / ALTURA_FIADA)
    dwg = ez.readfile(entrada)
    model = dwg.modelspace()

    # ------------------------------------------------------------ FIADAS -------------------
    eixos1 = eixos_da_fiada(model, 'fiada1')
    eixos2 = eixos_da_fiada(model, 'fiada2') or eixos1
    if eixos1 is None:
        raise SystemExit('Fiada ímpar (layer fiada1) nao encontrada.')
    pontozero = eixos1[0] + 200  # a elevação é desenhada 200 cm acima da 1ª fiada em planta
    nomes_planta = fam.nomes('B')
    for k in range(fiadas):
        layer, eixos = ('fiada1', eixos1) if k % 2 == 0 else ('fiada2', eixos2)
        y = pontozero + ALTURA_FIADA * k
        for ent in model.query(f'INSERT[layer=="{layer}"]'):
            if ent.dxf.name not in nomes_planta:
                continue
            vista = vista_do_bloco(ent, eixos)
            if vista:
                bloco(model, vista[0], vista[1], y)

    # ------------------------------------------------------------ PORTAS e JANELAS ---------
    portas = list(model.query('INSERT[layer=="porta"]'))
    janelas = list(model.query('INSERT[name=="Janela"]'))
    for p in portas:
        larg, alt = float(p.get_attrib_text('LARGURA')), float(p.get_attrib_text('ALTURA'))
        x = trunc(p.dxf.insert[0], 2)
        recortar_vao(model, x, x + larg, trunc(pontozero, 2), trunc(pontozero, 2) + alt)
    for j in janelas:
        larg, alt = float(j.get_attrib_text('LARGURA')), float(j.get_attrib_text('ALTURA'))
        peit = float(j.get_attrib_text('PEITORIL'))
        x = trunc(j.dxf.insert[0], 2)
        recortar_vao(model, x, x + larg, trunc(pontozero, 2) + peit, trunc(pontozero, 2) + peit + alt)

    # ------------------------------------------------------------ CINTA (última fiada) -----
    hparede = trunc(pontozero + (fiadas - 1) * ALTURA_FIADA - 1, 2)
    for b in model.query('INSERT[layer=="parede"]'):
        if trunc(b.dxf.insert[1], 2) > hparede:
            nome, pt = b.dxf.name, (b.dxf.insert[0], b.dxf.insert[1])
            model.delete_entity(b)
            bloco(model, 'BC' + nome, pt[0], pt[1], 'cinta')

    # ------------------------------------------------------------ VERGAS / CONTRAVERGAS ----
    def faixa(x_ins, larg, y_base):
        return (int(trunc(x_ins - (MAIOR + 1), 2) * 1000), int(trunc(x_ins + larg + MEIO_BLOCO + 1, 2) * 1000),
                int(trunc(y_base, 2) * 1000), int(trunc(y_base + ALTURA_BLOCO, 2) * 1000))
    for p in portas:
        larg, alt = float(p.get_attrib_text('LARGURA')), float(p.get_attrib_text('ALTURA'))
        trocar_por_canaleta(model, *faixa(p.dxf.insert[0], larg, pontozero + alt), 'verga')
    for j in janelas:
        larg, alt = float(j.get_attrib_text('LARGURA')), float(j.get_attrib_text('ALTURA'))
        peit = float(j.get_attrib_text('PEITORIL'))
        trocar_por_canaleta(model, *faixa(j.dxf.insert[0], larg, pontozero + alt + peit), 'verga')
        trocar_por_canaleta(model, *faixa(j.dxf.insert[0], larg, pontozero + peit - ALTURA_FIADA), 'verga')

    # ------------------------------------------------------------ GRAUTE -------------------
    graute = list(model.query('INSERT[name=="graute"]').query('INSERT[layer=="graute"]'))
    for g in graute:
        x = g.dxf.insert[0]
        pts = ((x + fam.FURO_COMPRIMENTO, pontozero), (x, pontozero), (x, pontozero + pedireito),
               (x + fam.FURO_COMPRIMENTO, pontozero + pedireito))
        hatch = model.add_hatch(color=1, dxfattribs={'layer': 'graute'})
        hatch.paths.add_polyline_path(pts, is_closed=True)

    # ------------------------------------------------------------ FERROS ------------------
    ferros_v = list(model.query('INSERT[name=="ferro"]'))
    for i, fe in enumerate(ferros_v):
        x, y = fe.dxf.insert[0], pontozero
        barra, bitola = int(fe.get_attrib_text('BARRA')), float(fe.get_attrib_text('BITOLA'))
        comp = float(fe.get_attrib_text('COMPRIMENTO'))
        model.add_line((x, y), (x, y + comp), dxfattribs={'layer': 'ferro'})
        topo = y + pedireito + 49
        model.add_line((x, topo), (x, topo + comp), dxfattribs={'layer': 'ferroNcontado', 'color': 2})
        model.add_text(f'N{i + 1} {barra} Φ{bitola} - C={comp}',
                       dxfattribs={'layer': 'ferro', 'rotation': 90, 'height': 5,
                                   'insert': (x - 1, (topo + topo + pedireito) / 2)})
    ferros_h = list(model.query('INSERT[name=="ferroHorizontal"]'))
    for i, fe in enumerate(ferros_h):
        alturaF = float(fe.get_attrib_text('ALTURA'))
        barra, bitola = int(fe.get_attrib_text('BARRAS')), float(fe.get_attrib_text('BITOLA'))
        comp = float(fe.get_attrib_text('COMPRIMENTO'))
        x, y = fe.dxf.insert[0], pontozero + alturaF
        model.add_line((x, y), (x + comp, y), dxfattribs={'layer': 'ferro'})
        yb = pontozero - (i + 1) * 10
        model.add_line((x, yb), (x + comp, yb), dxfattribs={'layer': 'ferroNcontado', 'color': 2})
        model.add_text(f'N{len(ferros_v) + i + 1} {barra} Φ{bitola} - C={comp}',
                       dxfattribs={'layer': 'ferro', 'height': 5, 'insert': (x, yb)})

    # ------------------------------------------------------------ CORTE -------------------
    for c in model.query('INSERT[name=="corte"]'):
        xc = round(c.dxf.insert[0], 2)
        x1, x2 = int((xc - (MAIOR + 1)) * 1000), int(xc * 1000)
        for layer in ('parede', 'cinta', 'verga'):
            for b in model.query(f'INSERT[layer=="{layer}"]'):
                if int(b.dxf.insert[0] * 1000) not in range(x1, x2):
                    continue
                nome = b.dxf.name
                if nome.startswith('L'):
                    novo = 'Bcorte'
                elif nome.startswith('BCL'):
                    novo = 'BCT' + nome[3:]
                else:
                    continue
                model.add_blockref(novo, (xc, b.dxf.insert[1] + pedireito + 50),
                                   dxfattribs={'layer': 'corte', 'color': 4})
        topo = pedireito + pontozero + 49
        laje = {'d': 'LajeDir', 'e': 'LajeEsq', '2': 'Laje'}.get(c.get_attrib_text('LAJE'))
        if laje:
            model.add_blockref(laje, (xc, topo + pedireito), dxfattribs={'layer': 'laje'})
        for a, b2 in (((xc, topo), (xc, topo + pedireito)), ((xc + E, topo), (xc + E, topo + pedireito)),
                      ((xc, topo), (xc + E, topo))):
            model.add_line(a, b2, dxfattribs={'layer': 'corte', 'color': 2})
        model.add_text(c.get_attrib_text('CORTE'), dxfattribs={'color': 3, 'height': 10,
                                                               'insert': (xc, topo + 21 + pedireito)})

    tabelas(model, pedireito, graute)
    dwg.saveas(saida)
    return fiadas


# ---------------------------------------------------------------- TABELAS ------------------
PESO_M = {5: 0.154, 6.3: 0.245, 8: 0.395, 10: 0.617, 12.5: 0.963, 16: 1.578, 20: 2.466, 25: 3.853}


def tabelas(model, pedireito, graute, x=0):
    """Tabelas de aço, blocos e graute desenhadas abaixo da fiada par."""
    yref = model.query('INSERT[layer=="fiada2"]')[0].dxf.insert[1]
    txt = lambda t, p, h=4: model.add_text(t, dxfattribs={'color': 3, 'insert': p, 'height': h})
    linha = lambda a, b: model.add_line(a, b, dxfattribs={'color': 3})
    ret = lambda x0, y0, w, h: model.add_lwpolyline([(x0, y0), (x0 + w, y0), (x0 + w, y0 - h), (x0, y0 - h)],
                                                    close=True, dxfattribs={'color': 3})
    # Aço
    total = {b: 0.0 for b in PESO_M}
    for nome, attr_barras in (('ferro', 'BARRA'), ('ferroHorizontal', 'BARRAS')):
        for fe in model.query(f'INSERT[name=="{nome}"]'):
            if fe.get_attrib_text('QUANTITATIVO') == 's':
                bit = float(fe.get_attrib_text('BITOLA'))
                if bit in total:
                    total[bit] += int(fe.get_attrib_text(attr_barras)) * float(fe.get_attrib_text('COMPRIMENTO'))
    y = yref - 300
    ret(x, y, 100, 110)
    linha((x, y - 20), (x + 100, y - 20))
    for k in range(1, 9):
        linha((x, y - 20 - 10 * k), (x + 100, y - 20 - 10 * k))
    linha((x + 20, y - 20), (x + 20, y - 110)); linha((x + 70, y - 20), (x + 70, y - 110))
    txt('TABELA DE FERROS', (x + 2, y - 15), 7)
    txt('Bitola', (x + 2, y - 27)); txt('Comprimento (m)', (x + 22, y - 27)); txt('Peso (kg)', (x + 72, y - 27))
    for k, bit in enumerate(PESO_M, start=1):
        c = round(total[bit] / 100, 2)  # atributo COMPRIMENTO está em cm; tabela em metros
        txt(f'Φ {bit}', (x + 2, y - 27 - 10 * k)); txt(f' {c}', (x + 38, y - 27 - 10 * k))
        txt(f'{round(c * PESO_M[bit], 2)}', (x + 72, y - 27 - 10 * k))
    # Blocos
    lista = fam.nomes('L') + fam.nomes('BCL')
    y = yref - 450
    h = 30 + 30 * len(lista)
    ret(x, y, 120, h)
    linha((x, y - 15), (x + 120, y - 15)); linha((x, y - 30), (x + 120, y - 30))
    for k in range(1, len(lista)):
        linha((x, y - 30 - 30 * k), (x + 120, y - 30 - 30 * k))
    linha((x + 60, y - 15), (x + 60, y - h))
    txt('TABELA DE BLOCOS', (x + 15, y - 11), 7); txt('Blocos', (x + 5, y - 25), 5); txt('Quantidade', (x + 65, y - 25), 5)
    for k, nome in enumerate(lista):
        yy = y - 60 - 30 * k
        model.add_blockref(nome, (x + 5, yy + 5), dxfattribs={'color': 3})
        qtd = len(model.query(f'INSERT[name=="{nome}" & color==4]'))
        txt(f'{qtd}', (x + 80, yy + 10), 5)
    # Graute
    y = yref - 450 - h - 40
    ret(x, y, 120, 60)
    linha((x, y - 15), (x + 120, y - 15)); linha((x, y - 30), (x + 120, y - 30)); linha((x + 60, y - 15), (x + 60, y - 60))
    txt('TABELA DE GRAUTE', (x + 5, y - 11), 7); txt('Descrição', (x + 10, y - 25), 5); txt('Volume(m³)', (x + 70, y - 25), 5)
    n = sum(1 for g in graute if g.get_attrib_text('QUANTITATIVO') == 's')
    gv = round(fam.FURO_AREA * pedireito * n / 1e6, 2)
    gh = round(sum(len(model.query(f'INSERT[name=="BCL{c}" & color==4]')) * fam.CANALETA_AREA * c
                   for c in COMPRIMENTOS) / 1e6, 2)
    for k, (rot, v) in enumerate((('Vertical', gv), ('Horizontal', gh), ('Total', round(gv + gh, 2)))):
        txt(rot, (x + 20, y - 37 - 10 * k)); txt(f'{v}', (x + 80, y - 37 - 10 * k))


if __name__ == '__main__':
    if '--altura' in sys.argv:
        altura = float(sys.argv[sys.argv.index('--altura') + 1])
    else:
        altura = pedir_altura()
    if altura == '':
        print('Por favor insira uma valor para funcionar adequadamente!')
    else:
        n = gerar(altura)
        print(f'OUTFILE.dxf gerado: {n} fiadas, família {E}x{MAIOR}')
