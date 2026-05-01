const API_URL = "https://projeto-y7ry.onrender.com";

// 🚀 1. SISTEMA DE CACHE: Guarda os dados para evitar requisições repetidas
const cacheNoticias = {};

// 🚀 2. CONTROLE DE ROLAGEM INFINITA
let noticiasExibidas = []; // Guarda a lista completa da categoria atual
let itensPorPagina = 9;    // Quantas notícias aparecem por vez
let paginaAtual = 1;

async function carregarNoticias() {
    // Se já temos as notícias no cache, usa elas (resposta instantânea)
    if (cacheNoticias['todas']) {
        prepararExibicao(cacheNoticias['todas']);
        return;
    }

    const div = document.getElementById("noticias");
    div.innerHTML = "<p style='text-align:center; grid-column: 1 / -1;'>Carregando as últimas notícias...</p>";

    try {
        const res = await fetch(`${API_URL}/noticias`);
        const dados = await res.json();
        cacheNoticias['todas'] = dados; // Salva no cache
        prepararExibicao(dados);
    } catch (e) {
        div.innerHTML = "<p>Erro ao carregar notícias. Tente novamente.</p>";
    }
}

async function filtrar(categoria) {
    // Se a categoria já está no cache, carrega em 0 segundos
    if (cacheNoticias[categoria]) {
        prepararExibicao(cacheNoticias[categoria]);
        return;
    }

    const div = document.getElementById("noticias");
    div.innerHTML = `<p style='text-align:center; grid-column: 1 / -1;'>Buscando notícias de ${categoria}...</p>`;

    try {
        const res = await fetch(`${API_URL}/categoria/${categoria}`);
        const dados = await res.json();
        cacheNoticias[categoria] = dados; // Salva no cache
        prepararExibicao(dados);
    } catch (e) {
        div.innerHTML = `<p>Erro ao carregar ${categoria}.</p>`;
    }
}

// 🚀 3. PREPARA A EXIBIÇÃO E RESETA A ROLAGEM
function prepararExibicao(lista) {
    noticiasExibidas = lista;
    paginaAtual = 1; // Volta para a página 1
    document.getElementById("noticias").innerHTML = ""; // Limpa a tela antiga
    mostrarMais(); // Renderiza o primeiro lote
}

// 🚀 4. RENDERIZA AS NOTÍCIAS AOS POUCOS
function mostrarMais() {
    const div = document.getElementById("noticias");

    if (noticiasExibidas.length === 0) {
        div.innerHTML = "<p style='text-align:center; grid-column: 1 / -1;'>Nenhuma notícia encontrada.</p>";
        return;
    }

    // Calcula o lote atual que vamos fatiar do array
    const inicio = (paginaAtual - 1) * itensPorPagina;
    const fim = inicio + itensPorPagina;
    const pedaco = noticiasExibidas.slice(inicio, fim);

    // Se já passou do fim do array, não faz nada
    if (pedaco.length === 0) return;

    pedaco.forEach(noticia => {
        div.innerHTML += `
            <div class="card fade-in">
                <img src="${noticia.imagem || 'https://via.placeholder.com/300x180'}" />
                <div class="card-content">
                    <h3>${noticia.titulo}</h3>
                    <p><strong>${noticia.categoria}</strong></p>
                    <a href="${noticia.url}" target="_blank" onclick="registrarAcesso('${noticia.url}')">Ler mais →</a>
                </div>
            </div>
        `;
    });

    paginaAtual++; // Prepara para a próxima rolagem
}

// 🚀 5. DETECTA A ROLAGEM DA PÁGINA (SCROLL)
window.addEventListener('scroll', () => {
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
    // Se o usuário rolou até perto do fim da página (margem de 50px)
    if (scrollTop + clientHeight >= scrollHeight - 50) {
        mostrarMais(); // Dispara o carregamento de mais 6 notícias
    }
});

// BUSCA COM DELAY (Debounce) PARA NÃO TRAVAR O SITE
let timeoutBusca = null;
async function buscar() {
    clearTimeout(timeoutBusca); // Limpa o timer anterior
    
    // Aguarda o usuário parar de digitar por 500ms antes de ir no banco
    timeoutBusca = setTimeout(async () => {
        const termo = document.getElementById("campoBusca").value;
        const div = document.getElementById("noticias");

        if (termo.length >= 3) {
            div.innerHTML = `<p style='text-align:center; grid-column: 1 / -1;'>Pesquisando por "${termo}"...</p>`;
            const res = await fetch(`${API_URL}/buscar/${termo}`);
            const dados = await res.json();
            prepararExibicao(dados);
        } else if (termo.length === 0) {
            carregarNoticias();
        }
    }, 500); 
}

async function registrarAcesso(url) {
    await fetch(`${API_URL}/contar_acesso/${encodeURIComponent(url)}`, { method: 'POST' });
}

// Mantém sua função de Dashboard original aqui (apenas omiti para economizar espaço, mantenha a que você já tem no arquivo!)
// async function mostrarAbaAnalise() { ... }

async function mostrarAbaAnalise() {
    const div = document.getElementById("noticias");
    div.innerHTML = "<p style='text-align:center; padding:50px;'>Carregando análises detalhadas...</p>";

    try {
        const res = await fetch(`${API_URL}/dashboard`);
        const dados = await res.json();

        div.innerHTML = `
            <div class="dashboard-aba" style="grid-column: 1 / -1; width: 100%;">
                <div class="dashboard-header">
                    <h2>📊 Analytics do Portal</h2>
                    <p>Visão geral de desempenho e engajamento</p>
                </div>

                <div class="metrics-row">
                    <div class="card-metrica">
                        <span>Total de Notícias</span>
                        <strong>${dados.estatisticas_gerais.total}</strong>
                    </div>
                    <div class="card-metrica">
                        <span>Engajamento Total</span>
                        <strong>${dados.estatisticas_gerais.cliques_totais} <small>cliques</small></strong>
                    </div>
                </div>

                <div class="analise-detalhada">
                <div class="secao-fontes">
                        <h3>📡 Principais Portais (Fontes)</h3>
                        <ul class="lista-fontes">
                            ${dados.por_fonte.map(f => `
                                <li>
                                    <span class="nome-fonte">${f.fonte}</span>
                                    <span class="qtd-fonte"><strong>${f.quantidade}</strong> notícias</span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                    <div class="secao-metadados" style="grid-column: 1 / -1; display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 40px;">
                    
                    <div class="card-metadados">
                        <h3>✍️ Perfil de Redação</h3>
                        <p class="desc-metadado">Média de caracteres nos títulos por categoria:</p>
                        <ul class="lista-fontes">
                            ${dados.tamanho_titulos.map(t => `
                                <li>
                                    <span class="nome-fonte">${t.categoria}</span>
                                    <span class="qtd-fonte" style="background: #e0f2f1; color: #00897b;"><strong>${t.media_caracteres}</strong> letras</span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                    
                    <div class="card-metadados">
                        <h3>🛠️ Qualidade da API (Completude)</h3>
                        <p class="desc-metadado">Taxa de sucesso na captação dos dados originais:</p>
                        
                        <div class="progresso-container" style="margin-top: 25px;">
                            <div class="progresso-texto">
                                <span>📸 Notícias com Imagem Válida</span>
                                <span>${dados.qualidade_dados.com_imagem}%</span>
                            </div>
                            <div class="barra-fundo">
                                <div class="barra-preenchida" style="width: ${dados.qualidade_dados.com_imagem}%; background: linear-gradient(90deg, #ff9800, #ff5722);"></div>
                            </div>
                        </div>

                        <div class="progresso-container" style="margin-top: 25px;">
                            <div class="progresso-texto">
                                <span>📝 Notícias com Descrição</span>
                                <span>${dados.qualidade_dados.com_descricao}%</span>
                            </div>
                            <div class="barra-fundo">
                                <div class="barra-preenchida" style="width: ${dados.qualidade_dados.com_descricao}%; background: linear-gradient(90deg, #00bcd4, #2196f3);"></div>
                            </div>
                        </div>
                    </div>

                </div>
                    <div class="secao-stats">
                    
                        <h3>Distribuição por Categoria</h3>
                        ${dados.por_categoria.map(cat => `
                            <div class="progresso-container">
                                <div class="progresso-texto">
                                    <span>${cat.categoria} (${cat.quantidade})</span>
                                    <span>${cat.percentual}%</span>
                                </div>
                                <div class="barra-fundo">
                                    <div class="barra-preenchida" style="width: ${cat.percentual}%"></div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="secao-nuvem" style="grid-column: 1 / -1; margin-top: 20px;">
                        <h3>☁️ Termos em Alta (Nuvem de Palavras)</h3>
                        <div class="nuvem-container">
                            ${dados.nuvem_palavras.map(p => `
                                <span style="font-size: ${12 + (p.peso * 3)}px; opacity: ${0.6 + (p.peso / 20)};">
                                    ${p.palavra}
                                </span>
                            `).join(' ')}
                        </div>
                    </div>
                    <div class="secao-ranking">
                        <h3>🏆 Top 5 Mais Lidas</h3>
                        <table class="tabela-analise">
                            <thead>
                                <tr><th>Notícia</th><th>Acessos</th></tr>
                            </thead>
                            <tbody>
                                ${dados.ranking_top_5.map(n => `
                                    <tr>
                                        <td>${n.titulo}</td>
                                        <td><strong>${n.acessos}</strong></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    } catch (erro) {
        div.innerHTML = "<p>Erro ao carregar o dashboard. Verifique a conexão com a API.</p>";
    }
}


carregarNoticias();