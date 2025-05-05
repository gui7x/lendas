import itertools
import numpy as np

def gerar_tabela_sinais(k):
    fatores = ['A', 'B', 'C', 'D', 'E'][:k]
    base = list(itertools.product([-1, 1], repeat=k))
    base = sorted(base, key=lambda x: x[::-1])

    tabela = []
    nomes_colunas = []

    for linha in base:
        sinais = list(linha)
        efeitos = []
        nomes = []

        for i in range(k):
            efeitos.append(sinais[i])
            nomes.append(fatores[i])

        for i in range(1, 2 ** k):
            indices = [j for j in range(k) if (i >> j) & 1]
            if len(indices) > 1:
                valor = 1
                nome = ''
                for idx in indices:
                    valor *= sinais[idx]
                    nome += fatores[idx]
                efeitos.append(valor)
                nomes.append(nome)

        tabela.append(efeitos)
        if not nomes_colunas:
            nomes_colunas = nomes

    return np.array(tabela), nomes_colunas, base

def entrada_respostas(n, r, base):
    print("\nInsira os valores de y para cada combinação de sinais:\n")
    y = []
    for i in range(n):
        sinais_str = "\t".join(str(val) for val in base[i])
        print(f"Experimento {i+1} - Sinais: {sinais_str}")
        valores = []
        for j in range(r):
            v = float(input(f"  Repetição {j+1}: "))
            valores.append(v)
        y.append(valores)
    return np.array(y)

def calcular_efeitos(tabela, y_medias):
    n = len(y_medias)
    efeitos = [np.mean(y_medias)]
    for j in range(tabela.shape[1]):
        efeitos.append(np.dot(tabela[:, j], y_medias) / n)
    return np.array(efeitos)

def calcular_y_est(tabela, efeitos):
    y_est = np.full(tabela.shape[0], efeitos[0])
    for j in range(tabela.shape[1]):
        y_est += tabela[:, j] * efeitos[j + 1]
    return y_est

def calcular_soma_quadrados_total(y, y_global):
    return np.sum((y.flatten() - y_global) ** 2)

def calcular_soma_quadrados_erro(y, y_est):
    return np.sum((y - y_est[:, np.newaxis]) ** 2)

def main():
    print("Projeto Fatorial 2^k r")
    k = int(input("Digite o número de fatores (2 a 5): "))
    r = int(input("Digite o número de replicações (1 a 3): "))

    tabela, nomes_colunas, base = gerar_tabela_sinais(k)
    y = entrada_respostas(len(tabela), r, base)
    y_medias = np.mean(y, axis=1)
    y_global = np.mean(y)

    efeitos = calcular_efeitos(tabela, y_medias)

    print("\nTabela de Sinais\n")
    cabecalho = ['I'] + nomes_colunas + ['y']
    print("\t".join(cabecalho))

    soma_colunas = np.zeros(len(nomes_colunas))
    soma_y = 0

    for i in range(len(tabela)):
        linha = [1] + list(tabela[i]) + [y_medias[i]]
        soma_y += y_medias[i]
        for j in range(len(nomes_colunas)):
            soma_colunas[j] += tabela[i][j] * y_medias[i]
        print("\t".join(str(val) for val in linha))

    print(f"{soma_y}\t" + "\t".join(str(val) for val in soma_colunas) + "\tTotal")
    print(f"{efeitos[0]}\t" + "\t".join(str(efeitos[j+1]) for j in range(len(nomes_colunas))) + f"\tTotal/{2**k}")

    if r == 1:
        SST = 2 ** k * sum(efeitos[1:] ** 2)
        SSE = 0
    else:
        y_est = calcular_y_est(tabela, efeitos)
        SST = calcular_soma_quadrados_total(y, y_global)
        SSE = calcular_soma_quadrados_erro(y, y_est)

    print("\nAnálise da Variação Explicada:\n")
    somas_parciais = []
    nomes_expandidos = []

    for j, nome in enumerate(nomes_colunas):
        if r == 1:
            SS = (2 ** k) * efeitos[j + 1] ** 2
        else:
            SS = (2 ** k) * r * efeitos[j + 1] ** 2
        somas_parciais.append(SS)
        nomes_expandidos.append(nome)

    total_SST = SST
    total_SS_exp = sum(somas_parciais)
    SSE = total_SST - total_SS_exp

    for nome, ss in zip(nomes_expandidos, somas_parciais):
        print(f"Fator {nome} explica {ss}/{total_SST} = {(ss / total_SST) * 100:.2f}%")

    print(f"\nSST = " + " + ".join([f"SS{nome}" for nome in nomes_expandidos]) + f" + SSE = {total_SST}")
    print(f"{(SSE / total_SST) * 100:.2f}% é atribuído aos erros")

    if r > 1:
        print("\nErros experimentais:")
        y_est = calcular_y_est(tabela, efeitos)
        for i in range(len(y)):
            for j in range(r):
                erro = y[i][j] - y_est[i]
                print(f"Experimento {i+1}, Repetição {j+1}: Erro = {erro:.2f}")

if __name__ == "__main__":
    main()
