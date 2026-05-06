const API_URL = "http://127.0.0.1:8000";

let imagemParaEnvio = null;
let videoStream = null;

const imgEnviada = document.getElementById("img-enviada");
const imgResultado = document.getElementById("img-resultado");
const hiddenFileInput = document.getElementById("hidden-file-input");

function normalizarProjeto(nome) {
    return String(nome || "").trim().toLowerCase().replaceAll(" ", "_");
}

async function carregarCSVs() {
    const select = document.getElementById("select-csv");

    try {
        const response = await fetch(`${API_URL}/projetos-csv/`);
        const data = await response.json();

        select.innerHTML = "";

        if (!response.ok || data.erro) {
            select.innerHTML = `<option value="">Erro ao carregar projetos</option>`;
            return;
        }

        if (!data.csvs || data.csvs.length === 0) {
            select.innerHTML = `<option value="">Nenhum CSV encontrado</option>`;
            return;
        }

        data.csvs.forEach((item) => {
            const option = document.createElement("option");

            const nomeProjeto =
                item.nome_projeto ||
                item.projeto ||
                item.nome ||
                String(item).replace(".csv", "");

            const arquivo =
                item.arquivo ||
                item.csv ||
                String(item);

            const payload = {
                nome_projeto: nomeProjeto,
                arquivo: arquivo,
            };

            option.value = JSON.stringify(payload);
            option.textContent = `${arquivo}`;

            select.appendChild(option);
        });
    } catch (error) {
        console.error("Erro ao carregar CSVs:", error);
        select.innerHTML = `<option value="">Falha ao carregar projetos</option>`;
    }
}

window.addEventListener("DOMContentLoaded", carregarCSVs);

function abrirModal(id) {
    document.getElementById(id).style.display = "flex";
}

function fecharModal(id) {
    document.getElementById(id).style.display = "none";
}

document.getElementById("btn-novo-projeto").addEventListener("click", () => {
    abrirModal("modal-projeto");
});

async function salvarProjeto() {
    const nomeInput = document.getElementById("nome-projeto").value.trim();
    const arquivoInput = document.getElementById("arquivo-projeto").files[0];

    if (!nomeInput || !arquivoInput) {
        alert("Digite um nome e selecione um arquivo de projeto PCB!");
        return;
    }

    const formData = new FormData();
    formData.append("nome_projeto", nomeInput);
    formData.append("arquivo_projeto", arquivoInput);

    const btnSalvar = document.querySelector("#modal-projeto button[onclick='salvarProjeto()']");
    const textoOriginal = btnSalvar.textContent;

    btnSalvar.textContent = "Processando...";
    btnSalvar.disabled = true;

    try {
        const response = await fetch(`${API_URL}/novo-projeto/`, {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!response.ok || data.erro) {
            throw new Error(data.erro || "Erro ao salvar projeto.");
        }

        alert("Projeto salvo com sucesso!");

        fecharModal("modal-projeto");

        document.getElementById("nome-projeto").value = "";
        document.getElementById("arquivo-projeto").value = "";

        await carregarCSVs();
    } catch (error) {
        alert("Erro: " + error.message);
    } finally {
        btnSalvar.textContent = textoOriginal;
        btnSalvar.disabled = false;
    }
}

document.getElementById("btn-importar-arquivo").addEventListener("click", () => {
    hiddenFileInput.click();
});

hiddenFileInput.addEventListener("change", function () {
    if (this.files && this.files[0]) {
        imagemParaEnvio = this.files[0];
        imgEnviada.src = URL.createObjectURL(imagemParaEnvio);
        imgResultado.src = "";
    }
});

document.getElementById("btn-usar-camera").addEventListener("click", async () => {
    abrirModal("modal-camera");

    try {
        videoStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment" },
        });

        document.getElementById("video-preview").srcObject = videoStream;
    } catch (err) {
        alert("Erro ao acessar a câmera: " + err);
        fecharCamera();
    }
});

function fecharCamera() {
    fecharModal("modal-camera");

    if (videoStream) {
        videoStream.getTracks().forEach((track) => track.stop());
        videoStream = null;
    }
}

function capturarFoto() {
    const video = document.getElementById("video-preview");
    const canvas = document.getElementById("canvas-capture");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
        imagemParaEnvio = new File([blob], "camera_capture.jpg", {
            type: "image/jpeg",
        });

        imgEnviada.src = URL.createObjectURL(blob);
        imgResultado.src = "";

        fecharCamera();
    }, "image/jpeg");
}

function abrirZoom(imgId) {
    const imgSrc = document.getElementById(imgId).src;

    if (!imgSrc) {
        alert("Nenhuma imagem para ampliar!");
        return;
    }

    document.getElementById("modal-zoom-img").src = imgSrc;
    abrirModal("modal-zoom");
}

document.getElementById("btn-inspecionar").addEventListener("click", async () => {
    if (!imagemParaEnvio) {
        alert("Importe um arquivo ou tire uma foto primeiro.");
        return;
    }

    const select = document.getElementById("select-csv");

    if (!select.value) {
        alert("Selecione um projeto válido.");
        return;
    }

    let projetoSelecionado;

    try {
        projetoSelecionado = JSON.parse(select.value);
    } catch {
        alert("Projeto selecionado inválido.");
        return;
    }

    const nomeProjeto = projetoSelecionado.nome_projeto;
    const arquivoCsv = projetoSelecionado.arquivo;

    if (!nomeProjeto || !arquivoCsv) {
        alert("Projeto selecionado incompleto.");
        return;
    }

    const formData = new FormData();
    formData.append("imagem", imagemParaEnvio, "imagem_placa.jpg");
    formData.append("projeto_csv", arquivoCsv);
    formData.append("nome_projeto", nomeProjeto);

    document.getElementById("loading-msg").style.display = "block";
    imgResultado.src = "";

    try {
        const response = await fetch(`${API_URL}/inspecionar-placa/`, {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!response.ok || data.erro) {
            throw new Error(data.erro || "Erro ao inspecionar placa.");
        }

        const nomeResultado =
            data.resultado ||
            data.nome_arquivo ||
            `resultado_${normalizarProjeto(nomeProjeto)}.png`;

        const urlResultado =
            data.url ||
            `${API_URL}/resultado/${encodeURIComponent(normalizarProjeto(nomeProjeto))}/${encodeURIComponent(nomeResultado)}`;

        imgResultado.src = `${urlResultado}?t=${Date.now()}`;
        imgResultado.style.display = "block";
    } catch (error) {
        alert("Erro: " + error.message);
    } finally {
        document.getElementById("loading-msg").style.display = "none";
    }
});

const inputProjeto = document.getElementById("arquivo-projeto");
const nomeArquivoProjeto = document.getElementById("arquivo-projeto-nome");

if (inputProjeto && nomeArquivoProjeto) {
    inputProjeto.addEventListener("change", () => {
        const arquivo = inputProjeto.files?.[0];

        nomeArquivoProjeto.textContent = arquivo
            ? arquivo.name
            : "Nenhum arquivo selecionado";
    });
}