# Alvenaria 0.1 - Alvenaria Estrutural família 19x39

Gera as elevações de paredes de alvenaria estrutural (blocos, vãos, vergas, contravergas, cinta,
graute, armaduras, corte e quantitativos) a partir da planta das fiadas desenhada no AutoCAD (DXF).

Baseado no programa de Mauro Fernandes Viana (FURG, 2022) - https://github.com/maurex23/AlvenariaEstrutural -
adaptado da família 14x29 para **19x39** (parede de 19 cm, blocos 19x19x39 e meio-bloco 19x19x19).

## Arquivos
| Arquivo | O que é |
|---|---|
| `dist/Alvenaria.exe` | Programa principal (pede a altura da parede e gera `OUTFILE.dxf`) |
| `dist/Quantitativo.exe` | Refaz as tabelas a partir do `OUTFILE.dxf` e gera `Quantitativo.dxf` |
| `Arquivos/Template_19x39.dxf` | Blocos para desenhar a planta: B19, B39, portas, janela, graute, ferros, corte |
| `Arquivos/Exemplo19x39/` | Exemplo: `INFILE.dxf` (planta), `OUTFILE.dxf` (resultado) e imagens do teste |
| `familia.py` | **Todas as medidas dos blocos** (espessura, comprimentos, furo, canaleta) |
| `Alvenaria.py`, `Quantitativo.py` | Código-fonte |
| `gerar_template_19x39.py` | Regera o template e o exemplo a partir de `familia.py` |
| `original_14x29/` | Código original (família 14x29) |
| `Arquivos/README.pdf` | Manual de uso (do trabalho original; vale igual, trocando B14/B29 por B19/B39) |

## Como usar
1. Desenhe as fiadas com os blocos `B19`/`B39` do template: fiadas ímpares no layer `fiada1`, pares no `fiada2`.
2. Portas no layer `porta`, graute no layer `graute`, ferros no layer `ferro` (ver manual).
3. Salve como `INFILE.dxf` na pasta do `Alvenaria.exe` e execute; informe a altura em cm.
4. O resultado sai em `OUTFILE.dxf`. Sem janela: `Alvenaria.exe --altura 280`.

## Medidas (familia.py)
Espessura 19 cm · blocos 19 e 39 cm · fiada 20 cm (19 + 1 de junta) · furo 15,75 x 14 cm ·
canaleta 255 cm² de graute (estimativa - conferir com o catálogo do fabricante).

## Gerar os executáveis
```
pip install ezdxf numpy FreeSimpleGUI pyinstaller
python -m PyInstaller --noconfirm Alvenaria.spec
python -m PyInstaller --noconfirm Quantitativo.spec
```
