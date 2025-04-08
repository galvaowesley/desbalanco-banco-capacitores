Com todos esses dados, agora eu quero resolver um problema de otimização. 
É esperado que:

* Carrega-se um arquivo config.json com as restrições. Isso é uma premissa, e o arquivo config.json é fornecido.
* Carrega-se também o dataframe com os dados dos capacitores, que é fornecido.
* A capacitância entre ramos de uma mesma perna seja a mesma, a sua diferença esteja seja menor ou igual a tolerância especificada no arquivo config.json, pela chave config['constraints']['tolerancia_diferenca'] 
* A capacitância entre pernas de um mesmo banco seja a mesma, a sua diferença esteja seja menor ou igual a tolerância especificada no arquivo config.json, pela chave config['constraints']['tolerancia_diferenca']
* A  capacitÂncia nominal da fase calculada, calculada no método get_capacitancia_fase(), não pode ser maior que a capacitância nominal de fábrica, especificada em ['constants']["capacit_nom_fase_uF"], mais x%. Essa tolerancia de x% é dada por config['constraints']['capacitance']['tolerancia_var_capacit_fase']
* Além disso, a corrente de desbalanceamento deve ser mais próxima de zero possível, ou seja, o sistema deve ser balanceado. Com uma tolerância desejada menor ou igual a config['constraints']['tolerancia_diferenca']
* Pense que fisicamente é muito complicado fazer essas trocas num banco de capacitores de uma subestação, pois eles são muito grandes e pesados. Portanto, É desejável o mínimo de trocas possíveis para se alcançar o balanceamento ótimo. Portanto, as permutações devem ser menores ou iguais config['constraints']['max_permutacoes']
* Pra isso fazemos a seguinte otimização:
  * Como condição inicial, verifica-se se o sistema já está balanceado. Se a corrente de desbalanceamento for menor ou igual a ['constraints']['tolerancia_diferenca'], o sistema já bem balanceado e não é necessário fazer nenhuma permutação.
    * Caso a corrente de desbalanceamento seja maior ou igual a ['constraints']['corrente_desbalanco_alarme_A'], o sistema não está balanceado e é necessário fazer permutações.
  * Entre pernas distintas de um mesmo rack, faz-se a permuta entre capacitores. Olha-se para o capacitor de menor valor de capacitância ajustada de um determinado ramo da primeira perna e troca-se com o de maior valor de capacitância ajustada de um outro ramo da segunda perna. Faz-se isso até que a diferença entre os capacitores seja menor ou igual a ['constraints']['tolerancia_diferenca'] ou que a corrente de desbalanceamento seja menor ou igual ['constraints']['tolerancia_diferenca']
  * O algoritmo é limitado por um número máximo de permutações, dado por config['constraints']['max_permutacoes'] e por config['constraints']['tolerancia_diferenca'].
  * Pensando numa heurística, ordena-se as capacitâncias de cada ramo de cada perna. Salvam-se as posições originais dos capacitores. Faz-se a permutação entre um par de capacitores de ramos distintos de pernas distintas. Calcula-se a corrente de desbalanceamento. Se a corrente de desbalanceamento for menor que a corrente de desbalanceamento anterior, salva-se a permutação. São feitas apenas 1 permutação por iteração. Isso é importante para que não haja o efeito de desbalanceamento devido a volta a um estado anterior. Ou seja, apenas algumas permutações são feitas para balancear o sistema, e não todas as permutações possíveis. Isto é mandatório. 

* Saída desejada: 
  * O algoritmo deve oferecer a solução ótima, ou seja, a solução que minimiza a corrente de desbalanceamento e que minimiza o número de permutações.
  * O algoritmo deve avisar se o sistema está ou não desbalanceado.
  * O algoritmo deve fornecer as permutações únicas que foram feitas, com as informações de quais capacitores foram trocados pelo campo "posicao_eln", qual ramo, qual perna e qual rack.
  * O algoritmo deve fornecer todos os parâmetros de capacitancia, reataância, tensão e correntes, inclusive a corrente de desbalanceamento logo após a otimização.
  * O algoritmo deve fornecer também o dataframe atualizado com as permutações feitas. Faça uma cópia do dataframe original e atualize com as permutações feitas.




```json
{
    "constants" : {
        "capacit_nom_capacitor_uF" : 24.3,    // Capacitância nominal de fábrica do capacitor
        "capacit_nom_fase_uF" : 3.24,         // Capacitância nominal de fábrica da fase
        "temp_ref_C": 20,                     // Temperatura de referência para cálculo da capacitância
        "tensao_nom_kV": 530,                 // Tensão nominal do sistema
    },

    "constraints" : {
        "delta_range_capacit" : [-5, 5], // Faixa de variação da capacitância em relação à capacitância nominal (%)
        "val_admit_capacit_capacitor_uF" : [23.085, 25.515], // Valores admitidos para a capacitância do capacitor (uF), dada a faixa de variação permitida
        "corrente_desbalanco_alarme_A" : 0.17, // Configuração de alarme para corrente de desbalanço (A)
        "tensao_nom_sistema_kV": 500
    }
}
```

| Fase | Rack |      | Perna |      | Ramo |          |
|------|------|------|-------|------|------|----------|
| 3292 | R1   | 6171 | P1    | 3086 | A1   | 1,544767 |
|      |      |      |       |      | A2   | 1,541294 |
|      |      |      | P2    | 3085 | B1   | 1,543810 |
|      |      |      |       |      | B2   | 1,541610 |
|      | R2   | 7054 | P3    | 3527 | A3   | 1,765159 |
|      |      |      |       |      | A4   | 1,762225 |
|      |      |      | P4    | 3527 | B3   | 1,766487 |
|      |      |      |       |      | B4   | 1,760146 |

