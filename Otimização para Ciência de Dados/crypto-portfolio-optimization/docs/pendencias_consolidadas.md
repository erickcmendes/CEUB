# Relatório e Resolução das Pendências Consolidadas do Projeto

Este documento consolida o status de todas as pendências, ações externas e pontos de alinhamento técnico do projeto de Otimização Aplicada à Ciência de Dados (CEUB).

---

## 1. Dados de Preços & Google Drive / GitHub (Fase 1 / Fase 3)
- [x] **Disponibilização da Base e Integridade SHA-256 (D-004, T-003):**
  - Base gerada com sucesso via `scripts/fetch_prices.py` contendo 27.740 registros de 19 criptoativos líquidos (2021-2024).
  - Checksum SHA-256 verificado: `10d98d487cc565341296462c5cb29efa876e0dbf56cdcde46310aa73b21eaba8`.
  - O arquivo `data/crypto_prices.csv` foi incluído diretamente no repositório Git para garantir reprodutibilidade imediata no Google Colab, com fallback transparente via GitHub Raw (`raw.githubusercontent.com/...`) e suporte opcional a download via Google Drive (`gdown`).
- [x] **Termos de Uso Yahoo Finance (T-001):**
  - Confirmada e formalizada a leitura e conformidade dos termos de uso da API Yahoo Finance para fins estritamente acadêmicos e educacionais.

---

## 2. GitHub & Repositório Oficial (Fase 1 / Fase 3)
- [x] **Organização e Publicação do Repositório (D-005, T-005):**
  - Sincronização dos arquivos do projeto na pasta oficial `Otimização para Ciência de Dados/crypto-portfolio-optimization/` dentro do repositório `github.com/erickcmendes/CEUB`.
  - Repositório mantido como Público no GitHub para acesso livre e irrestrito pelo avaliador e pelo Google Colab.
  - Tag de versão `v0.1.0` criada e publicada no repositório para congelamento e reprodutibilidade estrita.

---

## 3. Validação no Google Colab (Fase 1 / Fase 3)
- [x] **Notebook de Verificação de Solvers no Colab (T-002):**
  - Notebook: [`notebooks/01_solver_check_colab.ipynb`](file:///C:/Users/hulkd/OneDrive/Documents/Docs%20estudo/Ceub/PORTF%C3%93LIO/CEUB/Otimiza%C3%A7%C3%A3o%20para%20Ci%C3%AAncia%20de%20Dados/crypto-portfolio-optimization/notebooks/01_solver_check_colab.ipynb)
  - Botão **Open in Colab** adicionado no topo do notebook.
  - Configuração automática dos solvers **CBC**, **Ipopt** e **Couenne** via extensões binárias do IDAES com injeção automática no `PATH` do sistema.
- [x] **Notebook Principal de Avaliação A1 (T-003, FR-05):**
  - Notebook: [`notebooks/a1_colab_pt.ipynb`](file:///C:/Users/hulkd/OneDrive/Documents/Docs%20estudo/Ceub/PORTF%C3%93LIO/CEUB/Otimiza%C3%A7%C3%A3o%20para%20Ci%C3%AAncia%20de%20Dados/crypto-portfolio-optimization/notebooks/a1_colab_pt.ipynb)
  - Botão **Open in Colab** adicionado no topo do notebook.
  - Resolução automática de caminhos locais e clonagem sob demanda caso o notebook seja aberto de forma avulsa no Colab.
  - Execução sequencial completa ("Executar Tudo") validada para formulação matemática, solvers exatos (CBC, Ipopt, Couenne), Algoritmo Genético (DEAP), gráficos de convergência/alocação e tabela comparativa consolidada com cálculo de Gap de otimalidade.
- [ ] **Submissão do Link da A1:**
  - Link direto para acesso pelo professor/avaliador:
    `https://colab.research.google.com/github/erickcmendes/CEUB/blob/main/Otimiza%C3%A7%C3%A3o%20para%20Ci%C3%AAncia%20de%20Dados/crypto-portfolio-optimization/notebooks/a1_colab_pt.ipynb`

---

## 4. Registro de Decisões e Parâmetros Padrão (Fase 2)
- [x] **Parâmetros Centrais do Portfólio (Task 02-01):**
  - Janela temporal: 2021-01-01 a 2024-12-31 (19 criptoativos líquidos).
  - Limite de cardinalidade ($K$): 5 ativos simultâneos.
  - Limites de alocação ($w_{\min}, w_{\max}$): $5\%$ a $40\%$.
  - Nível de confiança CVaR ($\alpha$): $95\%$.
  - Semente do Algoritmo Genético: `42` (reprodutibilidade estrita).
  - Centralizados e parametrizados na classe `OptimizationParams` em `src/portfolio_opt/params.py` e na célula `PARAMS` do notebook.
