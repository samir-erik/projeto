// Configuração da API - Centralizada para facilitar se o endereço mudar
const API_URL = "https://projeto-y7ry.onrender.com";

// --- ESTADO GLOBAL DA APLICAÇÃO ---
const cacheNoticias = {}; // Sistema de Cache: Evita requisições repetidas ao servidor
let noticiasExibidas = []; // Lista de notícias atualmente carregada (para filtro/busca)
let itensPorPagina = 9;    // Quantidade de cards por lote (Paginação)
let paginaAtual = 1;

/**
 * Função principal para buscar todas as notícias.
 * Implementa cache simples para melhorar a performance.
 */
async function carregarNoticias() {
    // Se os dados já estiverem no cache, não vai ao servidor (Economia de dados)
    if (cacheNoticias['todas']) {
        prepararExibicao(cacheNoticias['todas']);
        return;
    }

    const div = document.getElementById("noticias");
    div.innerHTML = "<p style='text-align:center; grid-column: 1 / -1;'>Carregando portal...</p>";

    try {
        const res = await fetch(`${API_URL}/noticias`);
        const dados = await res.json();
        
        cacheNoticias['todas'] = dados; // Salva no cache para a próxima vez
        prepararExibicao(dados);
    } catch (e) {
        div.innerHTML = "<p style='text-align:center; grid-column: 1 / -1;'>Erro ao conectar com o servidor.</p>";
    }
}

/**
 * Filtra as notícias por categoria.
 */
async function filtrar(categoria) {
    if (cacheNoticias[categoria]) {
        prepararExibicao(cacheNoticias[categoria]);
        return;
    }

    const div = document.getElementById("noticias");
    div.innerHTML = `<p style='text-align:center; grid-column: 1 / -1;'>Buscando ${categoria}...</p>`;

    try {
        const res = await fetch(`${API_URL}/categoria/${categoria}`);
        const dados = await res.json();
        cacheNoticias[categoria] = dados;
        prepararExibicao(dados);
    } catch (e) {
        div.innerHTML = "<p>Erro ao filtrar categoria.</p>";
    }
}

/**
 * Prepara o array de notícias para a exibição e reseta a paginação.
 */
function prepararExibicao(lista) {
    noticiasExibidas = lista;
    paginaAtual = 1; 
    document.getElementById("noticias").innerHTML = ""; // Limpa o grid
    mostrarMais(); // Inicia a renderização do primeiro lote
}

/**
 * Renderiza as notícias em blocos (Paginação/Infinite Scroll).
 */
function mostrarMais() {
    const div = document.getElementById("noticias");
    const inicio = (paginaAtual - 1) * itensPorPagina;
    const fim = inicio + itensPorPagina;
    const lote = noticiasExibidas.slice(inicio, fim);

    if (lote.length === 0) return;

    lote.forEach(noticia => {
        div.innerHTML += `
            <div class="card fade-in">
                <img src="${noticia.imagem || 'https://via.placeholder.com/300x180'}" alt="Notícia" />
                <div class="card-content">
                    <h3>${noticia.titulo}</h3>
                    <p class="tag-categoria"><strong>${noticia.categoria}</strong></p>
                    <a href="${noticia.url}" target="_blank" onclick="registrarAcesso('${noticia.url}')">Ler na íntegra →</a>
                </div>
            </div>
        `;
    });
    paginaAtual++;
}

// --- BUSCA E EVENTOS ---

// Debounce: Aguarda o usuário parar de digitar para disparar a busca (Otimização de rede)
let timeoutBusca = null;
function buscar() {
    clearTimeout(timeoutBusca);
    timeoutBusca = setTimeout(async () => {
        const termo = document.getElementById("campoBusca").value;
        if (termo.length >= 3) {
            const res = await fetch(`${API_URL}/buscar/${termo}`);
            prepararExibicao(await res.json());
        } else if (termo.length === 0) {
            carregarNoticias();
        }
    }, 500); 
}

// Listener de Scroll para Rolagem Infinita
window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) {
        mostrarMais();
    }
});

/**
 * Incrementa o contador de acessos no banco de dados.
 */
async function registrarAcesso(url) {
    fetch(`${API_URL}/contar_acesso/${encodeURIComponent(url)}`, { method: 'POST' });
}

// --- ABA DE ANÁLISE (DASHBOARD) ---

async function mostrarAbaAnalise() {
    const div = document.getElementById("noticias");
    div.innerHTML = "<p style='text-align:center; padding:50px;'>Gerando inteligência de dados...</p>";

    try {
        const res = await fetch(`${API_URL}/dashboard`);
        const dados = await res.json();

        div.innerHTML = `
            <div class="dashboard-aba" style="grid-column: 1 / -1; width: 100%;">
                <div class="dashboard-header">
                    <h2>📊 Painel de Analytics</h2>
                    <p>Métricas de engajamento e análise de conteúdo</p>
                </div>

                <div class="metrics-row">
                    <div class="card-metrica">
                        <span>Total de Notícias</span>
                        <strong>${dados.estatisticas_gerais.total}</strong>
                    </div>
                    <div class="card-metrica">
                        <span>Cliques Computados</span>
                        <strong>${dados.estatisticas_gerais.cliques_totais}</strong>
                    </div>
                </div>

                <div class="analise-detalhada">
                    <!-- Fontes em destaque -->
                    <div class="secao-fontes" style="grid-column: 1 / -1; margin-bottom: 20px;">
                        <h3>📡 Portais Agregados</h3>
                        <ul class="lista-fontes">
                            ${dados.por_fonte.map(f => `
                                <li><span>${f.fonte}</span><span class="qtd-fonte">${f.quantidade} notícias</span></li>
                            `).join('')}
                        </ul>
                    </div>

                    <!-- Grid de 4 Cartões de Inteligência -->
                    <div class="secao-metadados" style="grid-column: 1 / -1; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">
                        
                        <div class="card-metadados">
                            <h3>🌡️ Humor do Dia</h3>
                            <p class="desc-metadado">Sentimento das manchetes:</p>
                            <div style="text-align: center;">
                                <h4 style="color: ${dados.sentimento.cor}; font-size: 1.4rem;">${dados.sentimento.humor}</h4>
                                <small>Score Positivo: ${dados.sentimento.score_pos}%</small>
                            </div>
                        </div>

                        <div class="card-metadados">
                            <h3>⏰ Relógio Temporal</h3>
                            <p class="desc-metadado">Distribuição de publicações:</p>
                            ${dados.relogio.map(r => `
                                <div style="font-size: 0.8rem; margin-bottom: 5px;">
                                    ${r.periodo}: <strong>${r.percentual}%</strong>
                                </div>
                            `).join('')}
                        </div>

                        <div class="card-metadados">
                            <h3>🎣 Sensacionalômetro</h3>
                            <p class="desc-metadado">Potencial de Clickbait:</p>
                            <div style="text-align: center;">
                                <h4 style="color: #ff5722; font-size: 1.8rem;">${dados.sensacionalismo.percentual}%</h4>
                                <small>Líder: ${dados.sensacionalismo.categoria_lider}</small>
                            </div>
                        </div>

                        <div class="card-metadados">
                            <h3>⚡ Índice de Frescor</h3>
                            <p class="desc-metadado">Latência média do portal:</p>
                            <div style="text-align: center;">
                                <h4 style="color: #00bcd4; font-size: 1.8rem;">${dados.frescor_horas}h</h4>
                                <small>Atraso médio vs Origem</small>
                            </div>
                        </div>
                    </div>

                    <!-- Ranking Final -->
                    <div class="secao-ranking" style="grid-column: 1 / -1;">
                        <h3>🏆 Ranking de Relevância (Top 5 Lidas)</h3>
                        <table class="tabela-analise">
                            <thead>
                                <tr><th>Manchete</th><th>Cliques</th></tr>
                            </thead>
                            <tbody>
                                ${dados.ranking_top_5.map(n => `
                                    <tr><td>${n.titulo}</td><td><strong>${n.acessos}</strong></td></tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    } catch (erro) {
        div.innerHTML = "<p style='text-align:center;'>Erro ao processar dashboard.</p>";
    }
}

// Inicialização
carregarNoticias();