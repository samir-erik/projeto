const API_URL = "https://projeto-y7ry.onrender.com";

async function carregarNoticias() {
    const res = await fetch(`${API_URL}/noticias`);
    const dados = await res.json();
    mostrar(dados);
}

async function filtrar(categoria) {
    const div = document.getElementById("noticias");
    div.innerHTML = `<p>Carregando ${categoria}...</p>`;
    const res = await fetch(`${API_URL}/categoria/${categoria}`);
    const dados = await res.json();
    mostrar(dados);
}

function mostrar(lista) {
    const div = document.getElementById("noticias");
    div.innerHTML = "";
    if (lista.length === 0) {
        div.innerHTML = "<p>Nenhuma notícia encontrada.</p>";
        return;
    }
    lista.forEach(noticia => {
        div.innerHTML += `
            <div class="card">
                <img src="${noticia.imagem || 'https://via.placeholder.com/300x180'}" />
                <div class="card-content">
                    <h3>${noticia.titulo}</h3>
                    <p><strong>${noticia.categoria}</strong></p>
                    <a href="${noticia.url}" target="_blank" onclick="registrarAcesso('${noticia.url}')">Ler mais →</a>
                </div>
            </div>
        `;
    });
}

async function buscar() {
    const termo = document.getElementById("campoBusca").value;
    if (termo.length >= 3) {
        const res = await fetch(`${API_URL}/buscar/${termo}`);
        const dados = await res.json();
        mostrar(dados);
    } else if (termo.length === 0) {
        carregarNoticias();
    }
}

async function registrarAcesso(url) {
    await fetch(`${API_URL}/contar_acesso/${encodeURIComponent(url)}`, { method: 'POST' });
}

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
css
/* ESTILOS DO DASHBOARD AVANÇADO */
.dashboard-aba {
    background: white;
    padding: 30px;
    border-radius: 20px;
    box-shadow: var(--shadow);
}

.dashboard-header { margin-bottom: 30px; }
.dashboard-header h2 { font-size: 2rem; color: var(--text-main); }

.metrics-row {
    display: flex;
    gap: 20px;
    margin-bottom: 40px;
}

.card-metrica {
    flex: 1;
    padding: 25px;
    background: #f8f9fa;
    border-radius: 15px;
    border-bottom: 4px solid var(--primary);
    text-align: center;
}

.card-metrica span { color: var(--text-muted); font-weight: 600; font-size: 0.9rem; }
.card-metrica strong { display: block; font-size: 2rem; color: var(--primary); margin-top: 5px; }

.analise-detalhada {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 40px;
}

/* Barras de Progresso */
.progresso-container { margin-bottom: 20px; }
.progresso-texto { display: flex; justify-content: space-between; margin-bottom: 8px; font-weight: 600; }
.barra-fundo { background: #eee; height: 12px; border-radius: 6px; overflow: hidden; }
.barra-preenchida { 
    background: linear-gradient(90deg, var(--primary), var(--accent)); 
    height: 100%; 
    transition: width 1s ease-in-out; 
}

/* Tabela de Ranking */
.tabela-analise { width: 100%; border-collapse: collapse; }
.tabela-analise th { text-align: left; padding: 12px; color: var(--text-muted); border-bottom: 2px solid #eee; }
.tabela-analise td { padding: 15px 12px; border-bottom: 1px solid #eee; font-size: 0.9rem; }

@media (max-width: 900px) {
    .analise-detalhada { grid-template-columns: 1fr; }
    .metrics-row { flex-direction: column; }
}

carregarNoticias();