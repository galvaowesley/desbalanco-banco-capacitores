#%%
import json
from otimizador import OtimizadorBancoCapacitores
from pre_processamento import PreProcessamentoBancoCapacitores
# %%
# Caminhos para os arquivos de dados
DATA_PATH = 'data/'
MEASURES = DATA_PATH + 'MEDIDA_CAPACITANCIA_FASE_A.txt'
SERIES_AND_POSITION = DATA_PATH + 'ramo_serie_posicao_fase_A.csv'
# %%
# Carrega o arquivo de configuração
with open('data/config.json', 'r') as file:
    config = json.load(file)
# %%
# Cria uma instância da classe
preprocessador = PreProcessamentoBancoCapacitores(
    measures_path=MEASURES,
    series_and_position_path=SERIES_AND_POSITION,
    config=config
)
# %%
# Carrega os dados brutos
preprocessador.load_data()

# %%
# Processa os dados
preprocessador.process_data()
# %%
# Acessa o DataFrame pré-processado
df_preprocessado = preprocessador.df
# %%
df_preprocessado.info()

# %%
df_preprocessado.sample(3)
# %%
# Otimização do banco de capacitores
otimizador = OtimizadorBancoCapacitores(df_preprocessado, config, rack_to_optimize='R1', max_permutacoes=10)
resultados = otimizador.get_results()

# Acessando os resultados
print("Sistema balanceado:", resultados['is_balanced'])
print("Corrente de desbalanceamento após otimização:", resultados['unbalanced_current'])
print("Permutações realizadas:", resultados['permutations'])

# Print other system parameters
print("\nCapacitâncias dos ramos (μF):")
for ramo, cap in resultados['capacitancias_ramos'].items():
    print(f"Ramo {ramo}: {cap}")

print("\nCapacitâncias das pernas (μF):")
for perna, cap in resultados['capacitancias_pernas'].items():
    print(f"Perna {perna}: {cap}")

print("\nCapacitâncias dos racks (μF):")
for rack, cap in resultados['capacitancias_racks'].items():
    print(f"Rack {rack}: {cap}")

print("\nCapacitância da fase (μF):", resultados['capacitancia_fase'])

print("\nReatâncias dos ramos (Ohms):")
for ramo, reatancia in resultados['reatancias_ramos'].items():
    print(f"Ramo {ramo}: {reatancia}")

print("\nReatâncias das pernas (Ohms):")
for perna, reatancia in resultados['reatancias_pernas'].items():
    print(f"Perna {perna}: {reatancia}")

print("\nReatâncias dos racks (Ohms):")
for rack, reatancia in resultados['reatancias_racks'].items():
    print(f"Rack {rack}: {reatancia}")

print("\nReatância da fase (Ohms):", resultados['reatancia_fase'])

print("\nTensão de fase (V):", resultados['V_fase'])
print("Corrente de fase (A):", resultados['I_fase'])

print("\nTensões dos racks (V):")
for rack, tensao in resultados['V_racks'].items():
    print(f"Rack {rack}: {tensao}")

print("\nCorrentes das pernas (A):")
for perna, corrente in resultados['I_pernas'].items():
    print(f"Perna {perna}: {corrente}")

# %%
