const API_URL = "https://projeto-y7ry.onrender.com";
const cacheNoticias = {};
let noticiasExibidas = [], itensPorPagina = 9, paginaAtual = 1;

// --- NAVEGAÇÃO E CACHE ---[cite: 9]
async function carregarNoticias() {
    if (cacheNoticias['todas']) { prepararExibicao(cacheNoticias['todas']); return; }
    const div = document.getElementById("noticias");
    div.innerHTML = "<p style='text-align:center; grid-column: 1 / -1;'>Carregando portal...</p>";
    try {
        const res = await fetch(`${API_URL}/noticias`);
        const dados = await res.json();
        cacheNoticias['todas'] = dados;
        prepararExibicao(dados);
    } catch (e) { div.innerHTML = "<p>Erro ao conectar com o servidor.</p>"; }
}

async function filtrar(categoria) {
    if (cacheNoticias[categoria]) { prepararExibicao(cacheNoticias[categoria]); return; }
    const div = document.getElementById("noticias");
    div.innerHTML = `<p style='text-align:center; grid-column: 1 / -1;'>Buscando ${categoria}...</p>`;
    try {
        const res = await fetch(`${API_URL}/categoria/${categoria}`);
        const dados = await res.json();
        cacheNoticias[categoria] = dados;
        prepararExibicao(dados);
    } catch (e) { div.innerHTML = "<p>Erro ao filtrar.</p>"; }
}

function prepararExibicao(lista) {
    noticiasExibidas = lista; paginaAtual = 1;
    document.getElementById("noticias").innerHTML = "";
    mostrarMais();
}

function mostrarMais() {
    const div = document.getElementById("noticias");
    const pedaco = noticiasExibidas.slice((paginaAtual - 1) * itensPorPagina, paginaAtual * itensPorPagina);
    if (pedaco.length === 0) return;
    pedaco.forEach(noticia => {
        div.innerHTML += `
            <div class="card fade-in">
                <img src="${noticia.imagem || 'https://via.placeholder.com/300x180'}" />
                <div class="card-content">
                    <h3>${noticia.titulo}</h3>
                    <p class="tag-categoria"><strong>${noticia.categoria}</strong></p>
                    <a href="${noticia.url}" target="_blank" onclick="registrarAcesso('${noticia.url}')">Ler na íntegra →</a>
                </div>
            </div>`;
    });
    paginaAtual++;
}

// --- BUSCA E EVENTOS ---[cite: 9]
let timeoutBusca = null;
function buscar() {
    clearTimeout(timeoutBusca);
    timeoutBusca = setTimeout(async () => {
        const termo = document.getElementById("campoBusca").value;
        if (termo.length >= 3) {
            const res = await fetch(`${API_URL}/buscar/${termo}`);
            prepararExibicao(await res.json());
        } else if (termo.length === 0) carregarNoticias();
    }, 500); 
}

window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) mostrarMais();
});

async function registrarAcesso(url) {
    fetch(`${API_URL}/contar_acesso/${encodeURIComponent(url)}`, { method: 'POST' });
}

// --- DASHBOARD (ABA DE ANALYTICS) ---[cite: 7, 9, 10]
async function mostrarAbaAnalise(categoria = 'Todas') {
    const div = document.getElementById("noticias");
    div.innerHTML = "Carregando inteligência de dados...";

    try {
        const res = await fetch(`${API_URL}/dashboard?categoria=${categoria}`);
        const dados = await res.json();

        div.innerHTML = `
            <div class="dashboard-aba">
                <div class="dashboard-header">
                    <h2>📊 Inteligência de Dados</h2>
                    <select id="filtroCategoriaDashboard" onchange="mostrarAbaAnalise(this.value)">
                        <option value="Todas" ${categoria === 'Todas' ? 'selected' : ''}>Todas as Categorias</option>
                        <option value="Tecnologia" ${categoria === 'Tecnologia' ? 'selected' : ''}>Tecnologia</option>
                        <option value="Esportes" ${categoria === 'Esportes' ? 'selected' : ''}>Esportes</option>
                        <option value="Economia" ${categoria === 'Economia' ? 'selected' : ''}>Economia</option>
                    </select>
                </div>

                <div class="secao-metadados">
                    <div class="card-analise"><h3>✍️ Perfil</h3><p>Tamanho médio: ${dados.media_titulo} carac.</p></div>
                    <div class="card-analise"><h3>⚡ Agilidade</h3><div class="valor-frescor">${dados.frescor_medio}h</div></div>
                    <div class="card-analise"><h3>🛠️ Qualidade</h3><p>📸 Img: ${dados.qualidade.img}% | 📝 Desc: ${dados.qualidade.desc}%</p></div>
                    <div class="card-analise">
                        <h3>🌡️ Termômetro (${dados.sentimento.humor})</h3>
                        <div class="barra-sentimento-container">
                            <div class="barra-sentimento" style="width: ${dados.sentimento.score_pos}%; background: ${dados.sentimento.cor}"></div>
                        </div>
                    </div>
                    <div class="card-analise"><h3>📢 Sensacionalismo</h3><p>Clickbait: ${dados.sensacionalismo}%</p></div>
                    <div class="card-analise"><h3>⏰ Pico de Postagem</h3><p>🌅 M: ${dados.relogio.manha}% | ☀️ T: ${dados.relogio.tarde}% | 🌙 N: ${dados.relogio.noite}%</p></div>
                </div>
            </div>
        `;
    } catch (e) {
        div.innerHTML = "<p style='color:red'>Erro ao conectar com o servidor. Verifica o terminal do Python.</p>";
        console.error(e);
    }
}

carregarNoticias();