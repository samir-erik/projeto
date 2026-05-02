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
            <div>
                <h2>📊 Inteligência de Dados</h2>
                <p style="color: #666; font-size: 0.95em; margin-top: 5px;">
                    Base de dados atual: <strong>${dados.total}</strong> notícias analisadas.
                </p>
            </div>
            <select id="filtroCategoriaDashboard" onchange="mostrarAbaAnalise(this.value)">
        <option value="Todas" ${categoria === 'Todas' ? 'selected' : ''}>Todas as Categorias</option>
        <option value="Tecnologia" ${categoria === 'Tecnologia' ? 'selected' : ''}>Tecnologia</option>
        <option value="Esportes" ${categoria === 'Esportes' ? 'selected' : ''}>Esportes</option>
        <option value="Economia" ${categoria === 'Economia' ? 'selected' : ''}>Economia</option>
        <option value="Geral" ${categoria === 'Geral' ? 'selected' : ''}>Geral</option>
    </select>
        </div>

                <div class="secao-metadados">   
                    <div class="card-analise">
                <h3>⚡ Agilidade (Delay Médio)</h3>
                <p style="font-size: 0.85em; color: #666; margin-bottom: 10px;">Tempo médio decorrido desde a publicação original das notícias.</p>
                <div class="valor-frescor">${dados.frescor_medio}h</div>
            </div>

            <div class="card-analise">
                <h3>📢 Sensacionalômetro</h3>
                <p style="font-size: 0.85em; color: #666; margin-bottom: 10px;">Mede a % de títulos que usam caixa alta ou pontuações de impacto (!, ?) para atrair cliques.</p>
                <p style="font-size: 1.1em; margin-top: 10px;">Índice de "Clickbait": <strong>${dados.sensacionalismo}%</strong></p>
            </div>
                    
                    <div class="card-analise">
                <h3>🌡️ Termômetro (${dados.sentimento.humor})</h3>
                <p style="font-size: 0.85em; color: #666; margin-bottom: 10px;">Mede o nível de palavras positivas nos títulos.</p>
                
                <div class="barra-sentimento-container">
                    <div class="barra-sentimento" style="width: ${dados.sentimento.score_pos}%; background: ${dados.sentimento.cor}"></div>
                </div>
                
                <p style="text-align: right; font-size: 0.9em; margin-top: 5px; font-weight: bold; color: ${dados.sentimento.cor};">
                    Índice de Positividade: ${dados.sentimento.score_pos}%
                </p>
            </div>
                    <div class="card-analise"><h3>⏰ Pico de Postagem</h3><p>🌅 M: ${dados.relogio.manha}% | ☀️ T: ${dados.relogio.tarde}% | 🌙 N: ${dados.relogio.noite}%</p></div>
                </div>
            </div>
        `;
    } catch (e) {
        div.innerHTML = "<p style='color:red'>Erro ao conectar com o servidor. Verifica o terminal do Python.</p>";
        console.error(e);
    }
}

// --- NOVO: FILTRO POR DATA ---
async function buscarPorData() {
    const dataSelecionada = document.getElementById("campoData").value;
    
    // Se o usuário limpar a data, volta a carregar todas as notícias
    if (!dataSelecionada) {
        carregarNoticias();
        return;
    }

    // Usando a mesma lógica de cache inteligente que você já fez para as categorias
    const chaveCache = `data_${dataSelecionada}`;
    if (cacheNoticias[chaveCache]) { 
        prepararExibicao(cacheNoticias[chaveCache]); 
        return; 
    }

    const div = document.getElementById("noticias");
    div.innerHTML = `<p style='text-align:center; grid-column: 1 / -1;'>Buscando notícias do dia ${dataSelecionada.split('-').reverse().join('/')}...</p>`;

    try {
        const res = await fetch(`${API_URL}/data/${dataSelecionada}`);
        const dados = await res.json();
        
        if (dados.length === 0) {
            div.innerHTML = `<p style='text-align:center; grid-column: 1 / -1;'>Nenhuma notícia encontrada para esta data. Tente outro dia!</p>`;
            return;
        }

        cacheNoticias[chaveCache] = dados;
        prepararExibicao(dados);
    } catch (e) { 
        div.innerHTML = "<p style='text-align:center; grid-column: 1 / -1;'>Erro ao filtrar por data.</p>"; 
    }
}

carregarNoticias();