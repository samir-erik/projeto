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