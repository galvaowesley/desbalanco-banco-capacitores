import pandas as pd
import numpy as np

class OtimizadorBancoCapacitores:
    def __init__(self, df: pd.DataFrame, config: dict, rack_to_optimize: str, max_permutacoes: int, run_optimization=True):
        self.df = df.copy()
        self.config = config
        self.rack_to_optimize = rack_to_optimize
        self.max_permutacoes = max_permutacoes
        self.permutacoes_feitas = []
        self.swapped_capacitors = set()
        self.unbalanced_current = None  # Será calculada
        self.is_balanced = None
        self.result_df = self.df.copy()
        self.constants = config['constants']
        self.constraints = config['constraints']
        
        # Cálculos iniciais
        self.calcular_parametros()
        self.verificar_balanceamento_inicial()
        
        # Se desbalanceado e se for para otimizar, realizar otimização
        if not self.is_balanced and run_optimization:
            self.otimizar()
    
    def calcular_parametros(self):
        # Calcular capacitâncias
        self.capacitancias_ramos = self.get_capacitancia_ramo()
        self.capacitancias_pernas = self.get_capacitancia_perna()
        self.capacitancias_racks = self.get_capacitancia_racks()
        self.capacitancia_fase = self.get_capacitancia_fase()
        
        # Calcular reatâncias
        self.reatancias_ramos = self.get_reatancia_capacitiva_ramos()
        self.reatancias_pernas = self.get_reatancia_capacitiva_pernas()
        self.reatancias_racks = self.get_reatancia_capacitiva_racks()
        self.reatancia_fase = self.get_reatancia_capacitiva_fase()
        
        # Calcular correntes e tensões
        self.V_fase = self.constants['tensao_nom_kV'] * 1000 / np.sqrt(3)
        self.I_fase = self.get_corrente_fase()
        self.V_racks = self.get_tensao_racks()
        self.I_pernas = self.get_corrente_pernas()
        self.unbalanced_current = self.get_corrente_desbalanceamento()
    
    def verificar_balanceamento_inicial(self):
        tolerancia_diferenca = self.constraints['tolerancia_diferenca']
        corrente_desbalanco_alarme = self.constraints['corrente_desbalanco_alarme_A']
        
        if self.unbalanced_current < corrente_desbalanco_alarme:
            self.is_balanced = True
            print("O sistema já está balanceado.")
        else:
            self.is_balanced = False
            print("O sistema não está balanceado e requer otimização.")
    
    def get_capacitancia_ramo(self):
        branches = self.df['ramo'].unique()
        branches = np.sort(branches)
        
        capacitancias_ramos = {}
        
        for ramo in branches:
            ramo_data = self.result_df[self.result_df['ramo'] == ramo]
            soma_inversos = np.sum(1 / ramo_data['capacitancia_campo_ajustada_uF'].values)
            capacitancias_ramos[ramo] = 1 / soma_inversos
        
        return capacitancias_ramos
    
    def get_capacitancia_perna(self):
        capacitancias_pernas = {
            'P1': self.capacitancias_ramos['A1'] + self.capacitancias_ramos['A2'],
            'P2': self.capacitancias_ramos['B1'] + self.capacitancias_ramos['B2'],
            'P3': self.capacitancias_ramos['A3'] + self.capacitancias_ramos['B4'],
            'P4': self.capacitancias_ramos['B3'] + self.capacitancias_ramos['B4']
        }
        return capacitancias_pernas
    
    def get_capacitancia_racks(self):
        capacitancias_racks = {
            'R1': self.capacitancias_pernas['P1'] + self.capacitancias_pernas['P2'],
            'R2': self.capacitancias_pernas['P3'] + self.capacitancias_pernas['P4']
        }
        return capacitancias_racks
    
    def get_capacitancia_fase(self):
        C_R1 = self.capacitancias_racks['R1']
        C_R2 = self.capacitancias_racks['R2']
        capacitancia_fase = (C_R1 * C_R2) / (C_R1 + C_R2)
        return capacitancia_fase
    
    def get_reatancia_capacitiva_ramos(self):
        frequencia = self.constants['frequencia_Hz']
        phi = 1e-6
        reatancias_ramos = {}
        for ramo, capacitancia in self.capacitancias_ramos.items():
            capacitancia_farad = capacitancia * phi
            reatancia = 1 / (2 * np.pi * frequencia * capacitancia_farad)
            reatancias_ramos[ramo] = reatancia
        return reatancias_ramos
    
    def get_reatancia_capacitiva_pernas(self):
        reatancias_pernas = {}
        for perna in self.capacitancias_pernas:
            if perna == 'P1':
                ramo1, ramo2 = 'A1', 'A2'
            elif perna == 'P2':
                ramo1, ramo2 = 'B1', 'B2'
            elif perna == 'P3':
                ramo1, ramo2 = 'A3', 'A4'
            elif perna == 'P4':
                ramo1, ramo2 = 'B3', 'B4'
            else:
                continue
            Xc_ramo1 = self.reatancias_ramos[ramo1]
            Xc_ramo2 = self.reatancias_ramos[ramo2]
            Xc_perna = (Xc_ramo1 * Xc_ramo2) / (Xc_ramo1 + Xc_ramo2)
            reatancias_pernas[perna] = Xc_perna
        return reatancias_pernas
    
    def get_reatancia_capacitiva_racks(self):
        reatancias_racks = {}
        Xc_P1 = self.reatancias_pernas['P1']
        Xc_P2 = self.reatancias_pernas['P2']
        Xc_R1 = (Xc_P1 * Xc_P2) / (Xc_P1 + Xc_P2)
        reatancias_racks['R1'] = Xc_R1
        Xc_P3 = self.reatancias_pernas['P3']
        Xc_P4 = self.reatancias_pernas['P4']
        Xc_R2 = (Xc_P3 * Xc_P4) / (Xc_P3 + Xc_P4)
        reatancias_racks['R2'] = Xc_R2
        return reatancias_racks
    
    def get_reatancia_capacitiva_fase(self):
        Xc_R1 = self.reatancias_racks['R1']
        Xc_R2 = self.reatancias_racks['R2']
        Xc_fase = Xc_R1 + Xc_R2
        return Xc_fase
    
    def get_corrente_fase(self):
        I_fase = self.V_fase / self.reatancia_fase
        return I_fase
    
    def get_tensao_racks(self):
        V_racks = {}
        V_racks['R1'] = self.I_fase * self.reatancias_racks['R1']
        V_racks['R2'] = self.I_fase * self.reatancias_racks['R2']
        return V_racks
    
    def get_corrente_pernas(self):
        I_pernas = {}
        V_R1 = self.V_racks['R1']
        Xc_P1 = self.reatancias_pernas['P1']
        Xc_P2 = self.reatancias_pernas['P2']
        I_P1 = V_R1 / Xc_P1
        I_P2 = V_R1 / Xc_P2
        V_R2 = self.V_racks['R2']
        Xc_P3 = self.reatancias_pernas['P3']
        Xc_P4 = self.reatancias_pernas['P4']
        I_P3 = V_R2 / Xc_P3
        I_P4 = V_R2 / Xc_P4
        I_pernas['P1'] = I_P1
        I_pernas['P2'] = I_P2
        I_pernas['P3'] = I_P3
        I_pernas['P4'] = I_P4
        return I_pernas
    
    def get_corrente_desbalanceamento(self):
        I_P1 = self.I_pernas['P1']
        I_P2 = self.I_pernas['P2']
        I_P3 = self.I_pernas['P3']
        I_P4 = self.I_pernas['P4']
        I_desb_R1 = np.abs(I_P4 - I_P2)
        I_desb_R2 = np.abs(I_P3 - I_P1)
        I_desbalanceamento = max(I_desb_R1, I_desb_R2)
        return I_desbalanceamento
    
    def otimizar(self):
        num_permutations = 0
        max_permutacoes = self.max_permutacoes
        tolerancia_diferenca = self.constraints['tolerancia_diferenca']
        corrente_desbalanco_alarme = self.constraints['corrente_desbalanco_alarme_A']
        rack = self.rack_to_optimize
        if rack == 'R1':
            legs = ['P1', 'P2']
        elif rack == 'R2':
            legs = ['P3', 'P4']
        else:
            print("Rack inválido.")
            return
        
        leg_branches = {
            'P1': ['A1', 'A2'],
            'P2': ['B1', 'B2'],
            'P3': ['A3', 'A4'],
            'P4': ['B3', 'B4']
        }
        
        leg1_branches = leg_branches[legs[0]]
        leg2_branches = leg_branches[legs[1]]
        
        while self.unbalanced_current > tolerancia_diferenca and num_permutations < max_permutacoes:
            swap_made = False
            for branch1 in leg1_branches:
                capacitors_branch1 = self.result_df[
                    (self.result_df['ramo'] == branch1) &
                    (~self.result_df['posicao'].isin(self.swapped_capacitors))
                ]
                if capacitors_branch1.empty:
                    continue
                cap1 = capacitors_branch1.loc[capacitors_branch1['capacitancia_campo_ajustada_uF'].idxmin()]
                for branch2 in leg2_branches:
                    capacitors_branch2 = self.result_df[
                        (self.result_df['ramo'] == branch2) &
                        (~self.result_df['posicao'].isin(self.swapped_capacitors))
                    ]
                    if capacitors_branch2.empty:
                        continue
                    cap2 = capacitors_branch2.loc[capacitors_branch2['capacitancia_campo_ajustada_uF'].idxmax()]
                    idx1 = cap1.name
                    idx2 = cap2.name
                    pos1 = cap1['posicao']
                    pos2 = cap2['posicao']
                    unbalanced_current_before = self.unbalanced_current
                    temp = self.result_df.loc[idx1, ['perna', 'ramo', 'posicao']]
                    self.result_df.loc[idx1, ['perna', 'ramo', 'posicao']] = self.result_df.loc[idx2, ['perna', 'ramo', 'posicao']]
                    self.result_df.loc[idx2, ['perna', 'ramo', 'posicao']] = temp
                    self.calcular_parametros()
                    if self.unbalanced_current < unbalanced_current_before:
                        self.swapped_capacitors.update([pos1, pos2])
                        self.permutacoes_feitas.append(
                            {
                                'ramo_origem': branch1,
                                'posicao_origem': pos1,
                                'ramo_destino': branch2,
                                'posicao_destino': pos2,
                                'corrente_desbalanco_A': self.unbalanced_current,
                                'permutacao': num_permutations+1
                            }
                        )
                        num_permutations +=1
                        print(f"Permutação {num_permutations}: trocou capacitor {pos1} (ramo {branch1}) com {pos2} (ramo {branch2}). Corrente de desbalanceamento reduziu para {self.unbalanced_current:.6f} A")
                        swap_made = True
                        break
                    else:
                        temp = self.result_df.loc[idx1, ['perna', 'ramo', 'posicao']]
                        self.result_df.loc[idx1, ['perna', 'ramo', 'posicao']] = self.result_df.loc[idx2, ['perna', 'ramo', 'posicao']]
                        self.result_df.loc[idx2, ['perna', 'ramo', 'posicao']] = temp
                        self.calcular_parametros()
                if swap_made:
                    break
            if not swap_made:
                print("Nenhuma permutação adicional reduz a corrente de desbalanceamento.")
                break
        print(f"Otimização concluída com {num_permutations} permutações.")
        if self.unbalanced_current <= tolerancia_diferenca:
            print("O sistema está balanceado após otimização.")
        else:
            print("Não foi possível balancear o sistema dentro das tolerâncias com o número máximo de permutações.")
    
    def get_results(self):
        results = {}
        results['is_balanced'] = self.unbalanced_current <= self.constraints['tolerancia_diferenca']
        results['unbalanced_current'] = self.unbalanced_current
        results['permutations'] = self.permutacoes_feitas
        results['capacitancias_ramos'] = self.capacitancias_ramos
        results['capacitancias_pernas'] = self.capacitancias_pernas
        results['capacitancias_racks'] = self.capacitancias_racks
        results['capacitancia_fase'] = self.capacitancia_fase
        results['reatancias_ramos'] = self.reatancias_ramos
        results['reatancias_pernas'] = self.reatancias_pernas
        results['reatancias_racks'] = self.reatancias_racks
        results['reatancia_fase'] = self.reatancia_fase
        results['V_fase'] = self.V_fase
        results['I_fase'] = self.I_fase
        results['V_racks'] = self.V_racks
        results['I_pernas'] = self.I_pernas
        results['updated_dataframe'] = self.result_df
        return results
