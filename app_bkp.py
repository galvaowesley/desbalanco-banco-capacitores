import streamlit as st
import pandas as pd
import numpy as np
import json
from otimizador import OtimizadorBancoCapacitores
from pre_processamento import PreProcessamentoBancoCapacitores

st.title('Otimização de Banco de Capacitores')

st.sidebar.header('Configurações')

# Upload dos arquivos
measures_file = st.sidebar.file_uploader('Carregar arquivo de medidas de capacitância', type=['txt'])
series_position_file = st.sidebar.file_uploader('Carregar arquivo de série e posição', type=['csv'])

# Seleção do rack e número máximo de permutações
rack_to_optimize = st.sidebar.selectbox('Rack para otimizar', options=['R1', 'R2'])
max_permutacoes = st.sidebar.number_input('Número máximo de permutações', min_value=1, value=10)

config_default = 'data/config.json'
config_file = st.sidebar.file_uploader('Carregar arquivo de configuração (config.json)', type=['json'])

if config_file is not None:
    config = json.load(config_file)
else:
    with open(config_default, 'r') as file:
        config = json.load(file)

if measures_file is not None and series_position_file is not None:
    # Carregar os dados usando os arquivos enviados pelo usuário
    preprocessador = PreProcessamentoBancoCapacitores(
        measures_path=measures_file,
        series_and_position_path=series_position_file,
        config=config
    )
    
    preprocessador.load_data()
    preprocessador.process_data()
    df_preprocessado = preprocessador.df
    
    st.subheader('Dados Pré-processados')
    st.write(df_preprocessado.head())
    
    # Permitir baixar o DataFrame pré-processado antes da otimização
    csv_preprocessado = df_preprocessado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Baixar Dados Pré-processados",
        data=csv_preprocessado,
        file_name='dataframe_preprocessado.csv',
        mime='text/csv',
    )
    
    # Exibir o status atual do sistema antes da otimização
    st.subheader('Status do Sistema Antes da Otimização')
    otimizador_inicial = OtimizadorBancoCapacitores(
        df_preprocessado, config, rack_to_optimize, max_permutacoes, run_optimization=False
    )
    resultados_iniciais = otimizador_inicial.get_results()
    st.write(f"**Corrente de desbalanceamento antes da otimização (A):** {resultados_iniciais['unbalanced_current']:.6f}")
    st.write(f"**Sistema balanceado:** {resultados_iniciais['is_balanced']}")
    
    def exibir_capacitancias(resultados, titulo):
        st.write(f"**{titulo}**")
        
        # Preparar os dados para a tabela
        fase_cap = resultados['capacitancia_fase']
        rows = []
        
        fase_included = False
        
        rack_legs = {'R1': ['P1', 'P2'], 'R2': ['P3', 'P4']}
        perna_ramos = {
            'P1': ['A1', 'A2'],
            'P2': ['B1', 'B2'],
            'P3': ['A3', 'A4'],
            'P4': ['B3', 'B4']
        }
        
        for rack in ['R1', 'R2']:
            rack_cap = resultados['capacitancias_racks'][rack]
            rack_included = False
        
            for perna in rack_legs[rack]:
                perna_cap = resultados['capacitancias_pernas'][perna]
                perna_included = False
        
                for ramo in perna_ramos[perna]:
                    ramo_cap = resultados['capacitancias_ramos'][ramo]
        
                    row = {}
        
                    if not fase_included:
                        row['Fase (μF)'] = f"{fase_cap:.3f}"
                        fase_included = True
                    else:
                        row['Fase (μF)'] = ''
        
                    if not rack_included:
                        row['Rack'] = rack
                        row['Cap. Rack (μF)'] = f"{rack_cap:.3f}"
                        rack_included = True
                    else:
                        row['Rack'] = ''
                        row['Cap. Rack (μF)'] = ''
        
                    if not perna_included:
                        row['Perna'] = perna
                        row['Cap. Perna (μF)'] = f"{perna_cap:.3f}"
                        perna_included = True
                    else:
                        row['Perna'] = ''
                        row['Cap. Perna (μF)'] = ''
        
                    row['Ramo'] = ramo
                    row['Cap. Ramo (μF)'] = f"{ramo_cap:.6f}"
        
                    rows.append(row)
        
        df_tabela = pd.DataFrame(rows, columns=[
            'Fase (μF)', 'Rack', 'Cap. Rack (μF)', 'Perna', 'Cap. Perna (μF)', 'Ramo', 'Cap. Ramo (μF)'
        ])
        
        st.table(df_tabela)

    def exibir_reatancias(resultados, titulo):
        st.write(f"**{titulo}**")
        
        # Preparar os dados para a tabela
        fase_reat = resultados['reatancia_fase']
        rows = []
        
        fase_included = False
        
        rack_legs = {'R1': ['P1', 'P2'], 'R2': ['P3', 'P4']}
        perna_ramos = {
            'P1': ['A1', 'A2'],
            'P2': ['B1', 'B2'],
            'P3': ['A3', 'A4'],
            'P4': ['B3', 'B4']
        }
        
        for rack in ['R1', 'R2']:
            rack_reat = resultados['reatancias_racks'][rack]
            rack_included = False
        
            for perna in rack_legs[rack]:
                perna_reat = resultados['reatancias_pernas'][perna]
                perna_included = False
        
                for ramo in perna_ramos[perna]:
                    ramo_reat = resultados['reatancias_ramos'][ramo]
        
                    row = {}
        
                    if not fase_included:
                        row['Fase (Ohms)'] = f"{fase_reat:.3f}"
                        fase_included = True
                    else:
                        row['Fase (Ohms)'] = ''
        
                    if not rack_included:
                        row['Rack'] = rack
                        row['Reat. Rack (Ohms)'] = f"{rack_reat:.3f}"
                        rack_included = True
                    else:
                        row['Rack'] = ''
                        row['Reat. Rack (Ohms)'] = ''
        
                    if not perna_included:
                        row['Perna'] = perna
                        row['Reat. Perna (Ohms)'] = f"{perna_reat:.3f}"
                        perna_included = True
                    else:
                        row['Perna'] = ''
                        row['Reat. Perna (Ohms)'] = ''
        
                    row['Ramo'] = ramo
                    row['Reat. Ramo (Ohms)'] = f"{ramo_reat:.6f}"
        
                    rows.append(row)
        
        df_tabela = pd.DataFrame(rows, columns=[
            'Fase (Ohms)', 'Rack', 'Reat. Rack (Ohms)', 'Perna', 'Reat. Perna (Ohms)', 'Ramo', 'Reat. Ramo (Ohms)'
        ])
        
        st.table(df_tabela)

    def exibir_correntes_tensoes(resultados, titulo):
        st.write(f"**{titulo}**")
        
        # Tabela para Tensão e Corrente de Fase
        st.write("**Tensão e Corrente de Fase**")
        df_fase = pd.DataFrame({
            'Tensão de Fase (V)': [f"{resultados['V_fase']:.3f}"],
            'Corrente de Fase (A)': [f"{resultados['I_fase']:.3f}"],
            'Corrente de Desbalanceamento (A)': [f"{resultados['unbalanced_current']:.6f}"]
        })
        st.table(df_fase)
        
        # Tabela para Tensões dos Racks
        st.write("**Tensões dos Racks**")
        df_racks = pd.DataFrame([
            {'Rack': rack, 'Tensão (V)': f"{tensao:.3f}"} for rack, tensao in resultados['V_racks'].items()
        ])
        st.table(df_racks)
        
        # Tabela para Correntes das Pernas
        st.write("**Correntes das Pernas**")
        df_pernas = pd.DataFrame([
            {'Perna': perna, 'Corrente (A)': f"{corrente:.3f}"} for perna, corrente in resultados['I_pernas'].items()
        ])
        st.table(df_pernas)
        
    
    # Exibir os parâmetros antes da otimização
    exibir_capacitancias(resultados_iniciais, 'Capacitâncias')
    exibir_reatancias(resultados_iniciais, 'Reatâncias')
    exibir_correntes_tensoes(resultados_iniciais, 'Tensões e Correntes')
    
    # Botão para executar a otimização
    if st.button('Executar Otimização'):
        # Otimização
        otimizador = OtimizadorBancoCapacitores(
            df_preprocessado, config, rack_to_optimize, max_permutacoes, run_optimization=True
        )
        resultados = otimizador.get_results()
        
        # Exibir os resultados após a otimização
        st.subheader('Resultados da Otimização')
        # st.write(f"**Sistema balanceado:** {resultados['is_balanced']}")
        st.write(f"**Corrente de desbalanceamento após otimização (A):** {resultados['unbalanced_current']:.6f}")
        st.write(f"**Permutações realizadas:** {len(resultados['permutations'])}")
        
        if resultados['permutations']:
            st.write('**Detalhes das Permutações:**')
            st.table(pd.DataFrame(resultados['permutations']))
        
        # Exibir parâmetros após a otimização
        exibir_capacitancias(resultados, 'Capacitâncias Após a Otimização')
        exibir_reatancias(resultados, 'Reatâncias Após a Otimização')
        exibir_correntes_tensoes(resultados, 'Tensões e Correntes Após a Otimização')
        
        # Permitir ao usuário baixar o DataFrame atualizado

        df_atualizado = resultados['updated_dataframe']
        csv_otimizado = df_atualizado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Baixar CSV com dados otimizados",
            data=csv_otimizado,
            file_name='dataframe_atualizado.csv',
            mime='text/csv',
        )
