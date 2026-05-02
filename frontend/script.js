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
async function mostrarAbaAnalise() {
    const div = document.getElementById("noticias");
    div.innerHTML = "<p style='text-align:center; padding:50px;'>Gerando inteligência de dados...</p>";
    try {
        const res = await fetch(`${API_URL}/dashboard`);
        const dados = await res.json();

        div.innerHTML = `
            <div class="dashboard-aba" style="grid-column: 1 / -1; width: 100%;">
                <!-- 💡 INSIGHT ANALÍTICO -->
                <div style="background: linear-gradient(135deg, #6e8efb 0%, #a777e3 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 30px; box-shadow: var(--shadow);">
                    <h3 style="margin-bottom: 10px;">💡 Insight da Inteligência</h3>
                    <p style="font-size: 0.95rem; opacity: 0.9;">Destaque em <strong>${dados.sensacionalismo.categoria_lider}</strong>.</p>
                    <hr style="margin: 15px 0; opacity: 0.3;">
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                        <h4 style="margin: 5px 0;">${dados.noticia_destaque.titulo}</h4>
                        <p style="font-size: 0.85rem;"><strong>Motivo:</strong> ${dados.noticia_destaque.motivo}</p>
                    </div>
                </div>

                <div class="metrics-row">
                    <div class="card-metrica"><span>Notícias</span><strong>${dados.estatisticas_gerais.total}</strong></div>
                    <div class="card-metrica"><span>Cliques</span><strong>${dados.estatisticas_gerais.cliques_totais}</strong></div>
                </div>

                <div class="analise-detalhada">
                    <div class="secao-fontes" style="grid-column: 1 / -1; display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div><h3>📡 Fontes</h3><ul class="lista-fontes">${dados.por_fonte.map(f => `<li><span>${f.fonte}</span><span class="qtd-fonte">${f.quantidade}</span></li>`).join('')}</ul></div>
                        <div><h3>🏎️ Agilidade</h3><ul class="lista-fontes">${dados.velocidade_fontes.map(v => `<li><span>${v.fonte}</span><span style="color:#34a853;">${v.latencia}h atraso</span></li>`).join('')}</ul></div>
                    </div>

                    <div class="secao-metadados" style="grid-column: 1 / -1; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px;">
                        <div class="card-metadados"><h3>🌡️ Humor</h3><h4 style="color:${dados.sentimento.cor}">${dados.sentimento.humor}</h4></div>
                        <div class="card-metadados"><h3>📈 Eficiência</h3>${dados.eficiencia_categoria.slice(0,3).map(e => `<small>${e.categoria}: <strong>${e.media}</strong></small><br>`).join('')}</div>
                        <div class="card-metadados"><h3>🎣 Clickbait</h3><h4>${dados.sensacionalismo.percentual}%</h4></div>
                        <div class="card-metadados"><h3>⚡ Frescor</h3><h4>${dados.frescor_horas}h</h4></div>
                    </div>

                    <div class="secao-ranking" style="grid-column: 1 / -1;">
                        <h3>🏆 Top 5 Lidas</h3>
                        <table class="tabela-analise">${dados.ranking_top_5.map(n => `<tr><td>${n.titulo}</td><td><strong>${n.acessos}</strong></td></tr>`).join('')}</table>
                    </div>
                </div>
            </div>`;
    } catch (erro) { div.innerHTML = "<p>Erro ao processar dashboard.</p>"; }
}
carregarNoticias();