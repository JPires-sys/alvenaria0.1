"""Refaz as tabelas de quantitativo (aço, blocos e graute) a partir do OUTFILE.dxf.

Gera Quantitativo.dxf. Usa as mesmas medidas de familia.py e a mesma rotina de tabelas do Alvenaria.py.
Uso:  python Quantitativo.py              (pergunta a altura)
      python Quantitativo.py --altura 280
"""
import sys

import ezdxf as ez

from Alvenaria import tabelas

if '--altura' in sys.argv:
    pedireito = float(sys.argv[sys.argv.index('--altura') + 1])
else:
    pedireito = float(input('Altura da Parede em cm: ').replace(',', '.'))

dwg = ez.readfile('OUTFILE.dxf')
model = dwg.modelspace()
graute = list(model.query('INSERT[name=="graute"]').query('INSERT[layer=="graute"]'))
tabelas(model, pedireito, graute, x=200)  # x=200: ao lado das tabelas originais
dwg.saveas('Quantitativo.dxf')
print('Quantitativo.dxf gerado.')
