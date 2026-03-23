console.log("JS CARREGOU");
let todasNoticias = [];

async function carregarNoticias() {
    const res = await fetch("http://127.0.0.1:5000/noticias");
    const dados = await res.json();

    todasNoticias = dados; // 🔥 salva tudo
    mostrar(dados);
}

async function filtrar(categoria) {
    const res = await fetch(`http://127.0.0.1:5000/categoria/${categoria}`);
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
        const res = await fetch(`http://127.0.0.1:5000/buscar/${termo}`);
        const dados = await res.json();
        mostrar(dados);
    } 
    // Se o usuário apagar tudo, recarrega todas as notícias
    else if (termo.length === 0) {
        carregarNoticias();
    }
}

carregarNoticias();