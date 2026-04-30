console.log("JS CARREGOU");
// URL da sua API no Render
const API_URL = "https://projeto-y7ry.onrender.com";

async function carregarNoticias() {
    const res = await fetch(`${API_URL}/noticias`);
    const dados = await res.json();
    mostrar(dados);
}

async function filtrar(categoria) {
    const div = document.getElementById("noticias");
    div.innerHTML = "<p>Carregando notícias de " + categoria + "...</p>";

    try {
        const res = await fetch(`${API_URL}/categoria/${categoria}`);
        const dados = await res.json();
        
        if (dados.length === 0) {
            div.innerHTML = `<p>Nenhuma notícia encontrada para a categoria ${categoria}.</p>`;
        } else {
            mostrar(dados);
        }
    } catch (erro) {
        div.innerHTML = "<p>Erro ao conectar com o servidor.</p>";
    }
}

function mostrar(lista) {
    const div = document.getElementById("noticias");
    div.innerHTML = "";

    lista.forEach(noticia => {
        div.innerHTML += `
            <div class="card">
                <img src="${noticia.imagem || 'https://via.placeholder.com/300x180?text=Sem+Imagem'}" />
                <div class="card-content">
                    <h3>${noticia.titulo}</h3>
                    <p><strong>Categoria:</strong> ${noticia.categoria || 'Geral'}</p>
                    <a href="${noticia.url}" target="_blank">Ler mais →</a>
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

// Função para registrar o clique na notícia
async function registrarAcesso(url) {
    await fetch(`${API_URL}/contar_acesso/${encodeURIComponent(url)}`, { method: 'POST' });
}

// Modifique sua função mostrar() para incluir o onclick no link
function mostrar(lista) {
    const div = document.getElementById("noticias");
    div.innerHTML = "";
    lista.forEach(noticia => {
        div.innerHTML += `
            <div class="card">
                <img src="${noticia.imagem || 'https://via.placeholder.com/300x180'}" />
                <div class="card-content">
                    <h3>${noticia.titulo}</h3>
                    <p><strong>Categoria:</strong> ${noticia.categoria || 'Geral'}</p>
                    <a href="${noticia.url}" target="_blank" onclick="registrarAcesso('${noticia.url}')">Ler mais →</a>
                </div>
            </div>
        `;
    });
}

// Função para carregar o Dashboard
async function carregarDashboard() {
    const res = await fetch(`${API_URL}/dashboard`);
    const dados = await res.json();
    
    const painel = document.getElementById("painelAnalise");
    const conteudo = document.getElementById("statsConteudo");
    painel.style.display = "block";

    let html = "<h3>Notícias por Categoria:</h3><ul>";
    dados.por_categoria.forEach(item => {
        html += `<li>${item.categoria}: <strong>${item.quantidade}</strong></li>`;
    });
    html += "</ul>";

    if(dados.mais_acessada) {
        html += `<br><h3>🏆 Mais Acessada:</h3>
                 <p>${dados.mais_acessada.titulo} (<strong>${dados.mais_acessada.acessos} cliques</strong>)</p>`;
    }

    conteudo.innerHTML = html;
}

carregarNoticias();