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
    const div = document.getElementById("noticias"); // Usa o mesmo container para facilitar
    div.innerHTML = "<p>Carregando análises...</p>";
    
    const res = await fetch(`${API_URL}/dashboard`);
    const dados = await res.json();

    div.innerHTML = `
        <div class="dashboard-aba" style="grid-column: 1/-1; background: white; padding: 20px; border-radius: 10px;">
            <h2>📊 Dashboard de Notícias</h2>
            <p>Total: ${dados.estatisticas_gerais.total} | Cliques: ${dados.estatisticas_gerais.cliques_totais}</p>
            <hr>
            <h3>🏆 Top 5 Mais Lidas</h3>
            <ul>
                ${dados.ranking_top_5.map(n => `<li>${n.titulo} (<strong>${n.acessos} cliques</strong>)</li>`).join('')}
            </ul>
        </div>
    `;
}

carregarNoticias();