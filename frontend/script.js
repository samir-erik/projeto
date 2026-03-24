console.log("JS CARREGOU");
// URL da sua API no Render
const API_URL = "https://api-noticias-s2f9.onrender.com";

// URL base da sua API no Render
const API_URL = "https://api-noticias-s2f9.onrender.com";

async function carregarNoticias() {
    const res = await fetch(`${API_URL}/noticias`);
    const dados = await res.json();
    mostrar(dados);
}

async function filtrar(categoria) {
    const res = await fetch(`${API_URL}/categoria/${categoria}`);
    const dados = await res.json();

    todasNoticias = dados; // 🔥 importante
    mostrar(dados);
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

carregarNoticias();