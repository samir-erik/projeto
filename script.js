console.log("JS CARREGOU");
let todasNoticias = [];

// URL base da sua API no Render
const API_URL = "https://api-noticias-s2f9.onrender.com";

async function carregarNoticias() {
    const res = await fetch(`${API_URL}/noticias`);
    const dados = await res.json();

    todasNoticias = dados; // 🔥 salva tudo
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
                <img src="${noticia.imagem}" />
                <div class="card-content">
                    <h3>${noticia.titulo}</h3>
                    <p>${noticia.categoria}</p>
                    <a href="${noticia.url}" target="_blank">Ler mais →</a>
                </div>
            </div>
        `;
    });
}

async function buscar() {
    const termo = document.getElementById("campoBusca").value;

    // Só busca se o usuário digitar pelo menos 3 letras
    if (termo.length >= 3) {
        const res = await fetch(`${API_URL}/buscar/${termo}`);
        const dados = await res.json();
        mostrar(dados);
    } 
    // Se o usuário apagar tudo, recarrega todas as notícias
    else if (termo.length === 0) {
        carregarNoticias();
    }
}

carregarNoticias();