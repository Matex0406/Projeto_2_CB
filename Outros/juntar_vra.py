"""
Junta os arquivos mensais do VRA (Voo Regular Ativo - ANAC) de 2025 em uma única base.

- Não altera nem apaga os arquivos originais.
- Mantém o formato da ANAC: mesmas colunas, separador ';', UTF-8 e quebras de linha CRLF.
- Cada linha de dados é copiada exatamente como está no arquivo de origem;
  o cabeçalho é escrito uma única vez.

Uso:
    python juntar_vra.py <pasta_com_os_csv> <arquivo_saida>
    python juntar_vra.py dados/brutos dados/VRA_2025.csv
"""
import hashlib
import re
import sys
from pathlib import Path

PADRAO = re.compile(r"VRA_2025_(\d{2})\.csv")


def juntar(pasta, saida):
    pasta, saida = Path(pasta), Path(saida)
    arquivos = sorted(f for f in pasta.iterdir() if PADRAO.fullmatch(f.name))
    if not arquivos:
        sys.exit(f"ERRO: nenhum arquivo VRA_2025_MM.csv em {pasta}")

    meses = {int(PADRAO.fullmatch(f.name).group(1)) for f in arquivos}
    faltando = sorted(set(range(1, 13)) - meses)
    if faltando:
        print(f"ATENÇÃO: meses ausentes: {faltando}\n")

    # Dois arquivos com conteúdo idêntico indicam o mesmo mês baixado duas vezes
    vistos = {}
    for f in arquivos:
        h = hashlib.md5(f.read_bytes()).hexdigest()
        if h in vistos:
            sys.exit(f"ERRO: {f.name} é idêntico a {vistos[h]}")
        vistos[h] = f.name

    cabecalho, total = None, 0
    with open(saida, "wb") as out:
        for f in arquivos:
            linhas = f.read_bytes().split(b"\r\n")
            if linhas[-1] == b"":  # quebra de linha final do arquivo
                linhas.pop()
            if any(b"\n" in l for l in linhas):
                sys.exit(f"ERRO: {f.name} tem quebras de linha fora do padrão CRLF")

            if cabecalho is None:
                cabecalho = linhas[0]
                out.write(cabecalho + b"\r\n")
            elif linhas[0] != cabecalho:
                sys.exit(f"ERRO: as colunas de {f.name} diferem das do primeiro arquivo")

            dados = linhas[1:]
            out.write(b"".join(l + b"\r\n" for l in dados))
            total += len(dados)
            print(f"{f.name}: {len(dados):>9,} linhas")

    print(f"\nTotal: {total:,} linhas de dados em {saida}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    juntar(sys.argv[1], sys.argv[2])
