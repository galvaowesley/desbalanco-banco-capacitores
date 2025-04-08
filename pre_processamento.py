import pandas as pd
import numpy as np

class PreProcessamentoBancoCapacitores:
    def __init__(self, measures_path, series_and_position_path, config):
        """
        Inicializa a classe com os caminhos para os dados brutos e o dicionário de configuração.

        Args:
            measures_path (str): Caminho para o arquivo de medidas de campo.
            series_and_position_path (str): Caminho para o arquivo de série e posição.
            config (dict): Dicionário contendo as constantes e restrições do sistema.
        """
        self.measures_path = measures_path
        self.series_and_position_path = series_and_position_path
        self.config = config
        self.df = None  # DataFrame pré-processado

    def load_data(self):
        """
        Carrega os dados brutos dos arquivos especificados.
        """
        self.raw_data = pd.read_csv(self.measures_path, delimiter='\t', decimal=',')
        self.serie_position = pd.read_csv(self.series_and_position_path, delimiter=',')

    def process_data(self):
        """
        Realiza o pré-processamento dos dados brutos para gerar o dataset de entrada.
        """
        # Mapeamento das pernas baseado nos ramos
        pernas = {
            'A1': 'P1',
            'A2': 'P1',
            'B1': 'P2',
            'B2': 'P2',
            'A3': 'P3',
            'A4': 'P3',
            'B3': 'P4',
            'B4': 'P4'
        }
        self.serie_position['perna'] = self.serie_position['ramo'].map(pernas)

        # Cálculo da capacitância média das três medições
        self.raw_data['capacitancia_campo_uF'] = self.raw_data[['(uF)', '(uF).1', '(uF).2']].mean(axis=1)

        # Criação do DataFrame com as medições de campo
        field_measurements = self.raw_data[['Serial', 'Date Time', '(C)', 'capacitancia_campo_uF']].copy()

        # Renomeando as colunas
        field_measurements.rename(columns={
            'Serial': 'serial',
            'Date Time': 'date_time',
            '(C)': 'temperatura_capacitor_C'
        }, inplace=True)

        # Ajuste do índice do serial
        field_measurements['serial'] = field_measurements.index + 1

        # Junção dos DataFrames
        self.field_measurements_merged = pd.merge(
            field_measurements,
            self.serie_position,
            left_on='serial',
            right_on='posicao',
            how='inner'
        )

        # Cálculo dos deltas de capacitância em relação ao valor de referência
        capacit_nom_capacitor_uF = self.config['constants']['capacit_nom_capacitor_uF']
        self.field_measurements_merged['delta_capacitancia_fabrica_%'] = 100 * (
            self.field_measurements_merged['capacitancia_fabrica_uF'] - capacit_nom_capacitor_uF
        ) / capacit_nom_capacitor_uF

        self.field_measurements_merged['delta_capacitancia_campo_%'] = 100 * (
            self.field_measurements_merged['capacitancia_campo_uF'] - capacit_nom_capacitor_uF
        ) / capacit_nom_capacitor_uF

        # Ajuste da capacitância de campo devido à temperatura
        alpha = -0.0004  # Coeficiente de temperatura
        temp_ref_C = self.config['constants']['temp_ref_C']
        self.field_measurements_merged['capacitancia_campo_ajustada_uF'] = (
            self.field_measurements_merged['capacitancia_campo_uF'] /
            (1 + alpha * (self.field_measurements_merged['temperatura_capacitor_C'] - temp_ref_C))
        )

        # Verificação de conformidade
        val_admit_capacit_capacitor_uF = self.config['constraints']['val_admit_capacit_capacitor_uF']
        self.field_measurements_merged['conformidade'] = np.where(
            (self.field_measurements_merged['capacitancia_campo_ajustada_uF'] >= val_admit_capacit_capacitor_uF[0]) &
            (self.field_measurements_merged['capacitancia_campo_ajustada_uF'] <= val_admit_capacit_capacitor_uF[1]),
            "C",
            "NC"
        )

        # Reordenamento das colunas
        self.df = self.field_measurements_merged[
            [
                'date_time',
                'rack',
                'ramo',
                'perna',
                'posicao',
                'num_serie',
                'capacitancia_fabrica_uF',
                'delta_capacitancia_fabrica_%',
                'capacitancia_campo_uF',
                'delta_capacitancia_campo_%',
                'temperatura_capacitor_C',
                'capacitancia_campo_ajustada_uF',
                'conformidade'
            ]
        ].copy()

    def save_preprocessed_data(self, output_path):
        """
        Salva o DataFrame pré-processado no caminho especificado.

        Args:
            output_path (str): Caminho para salvar o dataset pré-processado.
        """
        self.df.to_csv(output_path, index=False)
