import csv
import math
import random
from datetime import datetime, timedelta
from collections import defaultdict

# parametros
DISTANCIA_MINIMA = 500 
RAIO_COMUNICACAO = 10       
REPETICOES = 100
LIMIAR_BATERIA = 30
ARQUIVO_TRACE = "dataset_final_29.06.25.txt"
CHANCE_PRIORIDADE = 0.8
MAX_SALTOS = 10    

DEBUG = False       


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.asin(math.sqrt(a))

def carregar_trace(arquivo):
    timeline = defaultdict(list)
    print(f"⏳ Carregando arquivo de trace: {arquivo}...")
    with open(arquivo, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for linha in reader:
            try:
                node_id = int(linha[0])
                datahora = datetime.strptime(f"{linha[1]} {linha[2]}", "%d/%m/%Y %H:%M:%S")
                lat, lon = map(float, linha[3].split(','))
                bateria = int(linha[4])
                timeline[datahora].append({
                    'id': node_id,
                    'lat': lat,
                    'lon': lon,
                    'bateria': bateria
                })
            except (ValueError, IndexError):
                pass
    print("✅ Trace carregado com sucesso!")
    return timeline

def distancia_valida(timeline, id1, id2, tempos):
    for t in tempos:
        nos_no_tempo_t = timeline[t]
        n1 = next((n for n in nos_no_tempo_t if n['id'] == id1), None)
        n2 = next((n for n in nos_no_tempo_t if n['id'] == id2), None)
        if n1 and n2 and haversine(n1['lat'], n1['lon'], n2['lat'], n2['lon']) >= DISTANCIA_MINIMA:
            return True
    return False

def construir_contatos(nos_ativos):
    contatos = defaultdict(set)
    for i in range(len(nos_ativos)):
        for j in range(i + 1, len(nos_ativos)):
            ni, nj = nos_ativos[i], nos_ativos[j]
            if haversine(ni['lat'], ni['lon'], nj['lat'], nj['lon']) <= RAIO_COMUNICACAO:
                contatos[ni['id']].add(nj['id'])
                contatos[nj['id']].add(ni['id'])
    return contatos

def mensagem_prioritaria():
    return random.random() < CHANCE_PRIORIDADE

def simular_caso(timeline, caso, todos_ids):
    tempos = sorted(timeline.keys())
    resultados = {
        'entregues': 0,
        'saltos_total': 0,
        'latencia_total': 0,
        'transmissoes_iniciadas': 0
    }

    tentativas_de_par = 0
    while resultados['transmissoes_iniciadas'] < REPETICOES:
        tentativas_de_par += 1
        if tentativas_de_par > REPETICOES * 200:
            print("\n[AVISO] Dificuldade em encontrar pares válidos. Interrompendo.")
            break

        start_index = random.randint(0, len(tempos) - 2)
        tempo_envio = tempos[start_index]
        nos_iniciais_ativos = timeline[tempo_envio]

        if not nos_iniciais_ativos:
            continue

        origem_node = random.choice(nos_iniciais_ativos)
        origem_id = origem_node['id']

        possiveis_destinos = [nid for nid in todos_ids if nid != origem_id]

        if not possiveis_destinos:
            continue

        destino_id = random.choice(possiveis_destinos)

        if not distancia_valida(timeline, origem_id, destino_id, tempos):
            continue

        resultados['transmissoes_iniciadas'] += 1
        buffer_msg = {origem_id}
        hop_count = {origem_id: 0}
        entrega_bem_sucedida = False

        if DEBUG:
            print(f"[DEBUG] Transmissão #{resultados['transmissoes_iniciadas']} Origem: {origem_id} Destino: {destino_id}")

        for timestamp in tempos[start_index:]:

            nos_ativos = timeline[timestamp]
            contatos = construir_contatos(nos_ativos)
            novos_buffers = set()

            for remetente in list(buffer_msg):
                if hop_count[remetente] >= MAX_SALTOS:
                    continue

                for vizinho_id in contatos.get(remetente, set()):
                    if vizinho_id in buffer_msg:
                        continue

                    vizinho_node = next((n for n in nos_ativos if n['id'] == vizinho_id), None)
                    if not vizinho_node:
                        continue

                    is_egoista = vizinho_node['bateria'] < LIMIAR_BATERIA
                    deve_retransmitir = False

                    if caso == 1:
                        deve_retransmitir = True
                    elif caso == 2:
                        deve_retransmitir = not is_egoista
                    elif caso == 3:
                        deve_retransmitir = not is_egoista or mensagem_prioritaria()

                    if deve_retransmitir:
                        novos_buffers.add(vizinho_id)
                        hop_count[vizinho_id] = hop_count[remetente] + 1

            buffer_msg.update(novos_buffers)

            if destino_id in buffer_msg:
                resultados['entregues'] += 1
                resultados['saltos_total'] += hop_count.get(destino_id, 0)
                latencia = (timestamp - tempo_envio).total_seconds()
                resultados['latencia_total'] += latencia
                entrega_bem_sucedida = True

                if DEBUG:
                    print(f"[DEBUG] Mensagem entregue no tempo {timestamp} com latência {timedelta(seconds=int(latencia))} e saltos {hop_count.get(destino_id,0)}")

                break

    return resultados

def executar_simulacoes():
    timeline = carregar_trace(ARQUIVO_TRACE)
    if not timeline:
        print("[ERRO] Nenhum dado carregado. Verifique o arquivo de trace.")
        return

    todos_os_ids = list({node['id'] for t in timeline.values() for node in t})

    casos = {
        1: "Roteamento Epidêmico (sem egoísmo)",
        2: "Nós egoístas por bateria (sem prioridade)",
        3: "Nós egoístas por bateria (com mensagens prioritárias)"
    }

    for caso_num, descricao in casos.items():
        print(f"\n🧪 Simulando CASO {caso_num}: {descricao}...")
        res = simular_caso(timeline, caso_num, todos_os_ids)

        entregues = res['entregues']
        total = res['transmissoes_iniciadas']

        taxa = (entregues / total) * 100 if total > 0 else 0
        latencia_media = res['latencia_total'] / entregues if entregues > 0 else 0
        saltos_medios = res['saltos_total'] / entregues if entregues > 0 else 0

        latencia_tempo = timedelta(seconds=int(latencia_media))

        print(f"  → Taxa de entrega: {taxa:.2f}% ({entregues} de {total} mensagens)")
        print(f"  → Latência média: {latencia_tempo}")
        print(f"  → Saltos médios: {saltos_medios:.2f}")

if __name__ == "__main__":
    executar_simulacoes()
