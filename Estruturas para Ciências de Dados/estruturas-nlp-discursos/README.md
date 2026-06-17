# Estruturas de Dados para Processamento de Linguagem Natural

**Skip-gram e busca semântica sobre discursos parlamentares brasileiros**

Trabalho final da disciplina *Estruturas para Ciência de Dados* (graduação em
Data Science e Machine Learning, CEUB). Implementação, **do zero** (sem PyTorch,
TensorFlow, JAX, Gensim ou bibliotecas de embeddings prontas), de um pipeline
completo de embeddings distribucionais — Word2Vec/Skip-gram com *hierarchical
softmax* — e de busca semântica aproximada sobre ~8.000 discursos da 57ª
legislatura da Câmara dos Deputados.

O objetivo é usar, de forma **integrada e justificada**, quatro estruturas de
dados clássicas — cada uma introduzida porque a matemática do problema a exige,
não porque a rubrica a permite.

## As quatro estruturas

| Estrutura | Papel | Complexidade-chave |
|---|---|---|
| **Dicionário** (hash table) | Vocabulário: `token → id`, frequências, subsampling | Acesso O(1) médio |
| **Heap → Árvore de Huffman** | *Hierarchical softmax* (código de prefixo ótimo) | Treino O(log V) |
| **Pilha** | Grafo computacional do *autograd* (backpropagation) | *Backward* O(n) |
| **Grafo** (HNSW) | Índice de vizinhos mais próximos aproximados | Busca O(log N) |

## Estrutura do repositório

```
estruturas-nlp-discursos/
├── README.md            # Este arquivo (defesa arquitetural completa na Etapa 10)
├── notebook.ipynb       # Trabalho principal, construído etapa por etapa
├── coleta_corpus.py     # Coleta e amostragem do corpus (Etapa 1) — contrato de reprodução
├── requirements.txt     # Dependências
├── data/                # Corpus e cache (não versionado — regenerável)
└── artefatos/           # Vocab, árvore de Huffman, embeddings (não versionado — regenerável)
```

Os diretórios `data/` e `artefatos/` não vão para o repositório (são
regeneráveis). `coleta_corpus.py` é o contrato de reprodução: com a mesma *seed*
e o mesmo período, qualquer pessoa obtém o mesmo corpus.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python coleta_corpus.py        # Etapa 1 — gera data/discursos.parquet (~15 min)
jupyter notebook notebook.ipynb # Etapas 2+ — vocabulário, Huffman, treino, busca
```

## Estado atual

- [x] Etapa 1 — Coleta e amostragem do corpus
- [x] Etapa 2 — Vocabulário e subsampling (dicionário)
- [x] Etapa 3 — Árvore de Huffman e *hierarchical softmax* (heap → árvore)
- [ ] Etapa 4 — Mini-autograd (pilha)
- [ ] Etapas 5–9 — Modelo Skip-gram, treino, inspeção, indexação e busca
- [ ] Etapa 10 — Defesa arquitetural escrita

## Referências

Mikolov et al. (2013a, 2013b); Shannon (1948); Huffman (1952);
Malkov & Yashunin (2016); Levy & Goldberg (2014).
