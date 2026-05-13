# AOI / PCB Inspector

Sistema de inspeção automática de placas de circuito impresso, utilizando visão computacional, processamento de imagem, modelos YOLO e dados extraídos de projetos PCB.

O projeto permite cadastrar uma placa de referência, extrair informações do arquivo PCB, enviar uma imagem real da placa e gerar uma imagem final com marcações de componentes, possíveis defeitos e validações visuais.

---

## Visão Geral

O **AOI / PCB Inspector** é uma aplicação voltada para inspeção visual automatizada de placas eletrônicas.

A proposta é combinar:

- dados do projeto PCB;
- imagem real da placa;
- alinhamento por perspectiva;
- análise com OpenCV;
- detecção com modelos YOLO;
- visualização do resultado no frontend.

Com isso, o sistema consegue gerar uma imagem processada contendo referências visuais, caixas de componentes e marcações de possíveis defeitos.

---

## Objetivo

O objetivo do projeto é desenvolver uma solução de **AOI — Automated Optical Inspection**, capaz de auxiliar na validação visual de placas eletrônicas.

A aplicação busca reduzir inspeções manuais repetitivas e facilitar a identificação de componentes, ausência de peças, desalinhamentos e possíveis defeitos visuais.

---

## Funcionalidades

- Cadastro de novo projeto PCB;
- Extração automática de arquivos KiCad;
- Geração de CSV de posições dos componentes;
- Upload de imagem real da placa;
- Detecção do contorno da PCB;
- Alinhamento da imagem com base no projeto;
- Conversão de coordenadas em milímetros para pixels;
- Desenho de pontos, labels e caixas dos componentes;
- Aplicação de modelos YOLO para detecção;
- Geração de imagem final processada;
- Exibição do resultado diretamente no frontend.

---

## Tecnologias Utilizadas

### Backend

- Python
- FastAPI
- OpenCV
- NumPy
- Ultralytics YOLO
- KiCad CLI

### Frontend

- HTML
- CSS
- JavaScript

### Inteligência Artificial

- YOLO para detecção de componentes;
- YOLO para detecção de defeitos.

---

## Arquitetura do Projeto

```txt
INSPECAO-PCB/
│
├── backend/
│   │
│   ├── main.py
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── inspecao.py
│   │       └── projetos.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── services/
│   │   ├── inspecao_service.py
│   │   ├── projeto_service.py
│   │   ├── importador_service.py
│   │   └── kicad_cli_service.py
│   │
│   ├── app/
│   │   │
│   │   ├── processing/
│   │   │   ├── pipeline.py
│   │   │   ├── analyze.py
│   │   │   ├── align.py
│   │   │   ├── draw.py
│   │   │   ├── mm_to_pixel.py
│   │   │   └── parser.py
│   │   │
│   │   ├── detectors/
│   │   │   └── yolo_detector.py
│   │   │
│   │   └── kicad/
│   │       ├── pcb_parser.py
│   │       └── extractor.py
│   │
│   ├── models/
│   │   ├── componentes/
│   │   │   ├── best.pt
│   │   │   ├── best2.pt
│   │   │   └── best3.pt
│   │   │
│   │   └── defeitos/
│   │       └── best.pt
│   │
│   └── data/
│       └── projetos/
│           └── nome_do_projeto/
│               ├── original/
│               ├── convert/
│               ├── csv/
│               ├── pcb/
│               ├── uploads/
│               ├── output/
│               └── temp/
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── .gitignore
└── README.md
