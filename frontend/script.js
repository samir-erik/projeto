const API_URL = "https://projeto-y7ry.onrender.com";
const cacheNoticias = {};
let noticiasExibidas = [], itensPorPagina = 9, paginaAtual = 1;

let datasValidas = [];

async function carregarConfiguracoes() {
    const res = await fetch(`${API_URL}/datas_disponiveis`);
    datasValidas = await res.json();
    
    if (datasValidas.length > 0) {
        document.getElementById("campoData").min = datasValidas[datasValidas.length - 1];
        document.getElementById("campoData").max = datasValidas[0];
    }
}

carregarConfiguracoes();

async function buscarPorData() {
    const dataSelecionada = document.getElementById("campoData").value;
    
    if (!dataSelecionada) { 
        carregarNoticias(); 
        return; 
    }

    if (!datasValidas.includes(dataSelecionada)) {
        alert("Ops! Não temos notícias coletadas para este dia específico.");
        return;
    }

    const chaveCache = `data_${dataSelecionada}`;
    if (cacheNoticias[chaveCache]) { 
        prepararExibicao(cacheNoticias[chaveCache]); 
        return; 
    }

    const div = document.getElementById("noticias");
    div.innerHTML = `<p style='text-align:center; grid-column: 1 / -1;'>Buscando notícias do dia ${dataSelecionada.split('-').reverse().join('/')}...</p>`;

    try {
        const res = await fetch(`${API_URL}/data/${dataSelecionada}`);
        const dados = await res.json();
        
        if (dados.length === 0) {
            div.innerHTML = `<p style='text-align:center; grid-column: 1 / -1;'>Nenhuma notícia encontrada para esta data. Tente outro dia!</p>`;
            return;
        }

        cacheNoticias[chaveCache] = dados;
        prepararExibicao(dados);
    } catch (e) { 
        div.innerHTML = "<p style='text-align:center; grid-column: 1 / -1;'>Erro ao filtrar por data.</p>"; 
    }
}

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

// --- DASHBOARD (ABA DE ANALYTICS) ---
let graficoRelogioInstancia = null; 
let graficoFontesInstancia = null; 
let graficoDelayInstancia = null; 

async function mostrarAbaAnalise(categoria = 'Todas') {
    const div = document.getElementById("noticias");
    div.innerHTML = "<p style='text-align:center; grid-column: 1 / -1;'>Carregando inteligência de dados...</p>";

    try {
        const res = await fetch(`${API_URL}/dashboard?categoria=${categoria}`);
        const dados = await res.json();

        div.innerHTML = `
            <div class="dashboard-aba">
                <div class="dashboard-header">
                    <div>
                        <h2>📊 Inteligência de Dados</h2>
                        <p style="color: #666; font-size: 0.95em; margin-top: 5px;">
                            Base de dados atual: <strong>${dados.total}</strong> notícias analisadas.
                        </p>
                    </div>
                    <select id="filtroCategoriaDashboard" onchange="mostrarAbaAnalise(this.value)">
                        <option value="Todas" ${categoria === 'Todas' ? 'selected' : ''}>Todas as Categorias</option>
                        <option value="Tecnologia" ${categoria === 'Tecnologia' ? 'selected' : ''}>Tecnologia</option>
                        <option value="Esportes" ${categoria === 'Esportes' ? 'selected' : ''}>Esportes</option>
                        <option value="Economia" ${categoria === 'Economia' ? 'selected' : ''}>Economia</option>
                        <option value="Geral" ${categoria === 'Geral' ? 'selected' : ''}>Geral</option>
                    </select>
                </div>

                <!-- LINHA 1: FONTES E PICO DE POSTAGEM -->
                <div class="secao-metadados">
                    <div class="card-analise">
                        <h3 style="margin-bottom: 15px;">📰 Top 5 Veículos (Fontes)</h3>
                        <!-- Caixa protetora do gráfico -->
                        <div style="position: relative; height: 250px; width: 100%;">
                            <canvas id="graficoFontes"></canvas>
                        </div>
                    </div>

                    <div class="card-analise">
                        <h3 style="margin-bottom: 15px;">⏰ Pico de Postagem</h3>
                        <!-- Caixa protetora do gráfico -->
                        <div style="position: relative; height: 250px; width: 100%;">
                            <canvas id="graficoRelogio"></canvas>
                        </div>
                    </div>
                </div>

                <!-- LINHA 2: NOVO GRÁFICO DE DELAY E SENTIMENTO -->
                <div class="secao-metadados" style="margin-top: 20px;">
                    <!-- Gráfico Ocupando 2/3 da tela -->
                    <div class="card-analise" style="grid-column: span 2;">
                        <h3 style="margin-bottom: 5px;">⚡ Histórico de Delay (Últimas Notícias)</h3>
                        <p style="font-size: 0.85em; color: #666; margin-bottom: 15px;">Tempo decorrido entre a publicação no portal original e a nossa coleta.</p>
                        
                        <!-- Caixa protetora do gráfico -->
                        <div style="position: relative; height: 220px; width: 100%;">
                            <canvas id="graficoDelay"></canvas>
                        </div>
                        
                        <!-- MÉDIA NO RODAPÉ DO GRÁFICO -->
                        <div style="text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;">
                            <p style="font-size: 1.1em; color: var(--text-main);">
                                Média Geral de Delay da Categoria: <strong style="font-size: 1.5em; color: var(--primary);">${dados.frescor_medio}h</strong>
                            </p>
                        </div>
                    </div>

                    <!-- Termômetro ao lado -->
                    <div class="card-analise" style="display: flex; flex-direction: column; justify-content: center;">
                        <h3 style="text-align:center;">🌡️ Termômetro</h3>
                        <p style="text-align:center; font-size: 1.2em; font-weight:bold; color: ${dados.sentimento.cor}; margin: 10px 0;">
                            ${dados.sentimento.humor}
                        </p>
                        <div class="barra-sentimento-container">
                            <div class="barra-sentimento" style="width: ${dados.sentimento.score_pos}%; background: ${dados.sentimento.cor}"></div>
                        </div>
                        <p style="text-align: center; font-size: 0.9em; margin-top: 10px;">
                            Índice de Positividade: <strong>${dados.sentimento.score_pos}%</strong>
                        </p>
                    </div>
                </div>
            </div>
        `;

        // Destrói gráficos antigos para evitar sobreposição
        if (graficoRelogioInstancia) graficoRelogioInstancia.destroy();
        if (graficoFontesInstancia) graficoFontesInstancia.destroy();
        if (graficoDelayInstancia) graficoDelayInstancia.destroy();

        // 1. Gráfico de Rosca (Relógio)
        const ctxRelogio = document.getElementById('graficoRelogio');
        if (ctxRelogio) {
            graficoRelogioInstancia = new Chart(ctxRelogio, {
                type: 'doughnut',
                data: {
                    labels: ['Manhã', 'Tarde', 'Noite', 'Madrugada'],
                    datasets: [{
                        data: [dados.relogio.manha, dados.relogio.tarde, dados.relogio.noite, dados.relogio.madrugada],
                        backgroundColor: ['#ffeb3b', '#ff9800', '#3f51b5', '#212121'],
                        borderWidth: 0
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
            });
        }

        // 2. Gráfico de Barras (Fontes)
        const ctxFontes = document.getElementById('graficoFontes');
        if (ctxFontes && dados.fontes && dados.fontes.length > 0) {
            graficoFontesInstancia = new Chart(ctxFontes, {
                type: 'bar',
                data: {
                    labels: dados.fontes.map(f => f.nome),
                    datasets: [{
                        data: dados.fontes.map(f => f.quantidade),
                        backgroundColor: 'rgba(26, 115, 232, 0.7)',
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
                    plugins: { legend: { display: false } }
                }
            });
        }

        // 3. Gráfico de Linhas (Delay)
        const ctxDelay = document.getElementById('graficoDelay');
        if (ctxDelay && dados.historico_delay && dados.historico_delay.dados.length > 0) {
            graficoDelayInstancia = new Chart(ctxDelay, {
                type: 'line',
                data: {
                    labels: dados.historico_delay.labels,
                    datasets: [{
                        label: 'Delay (Horas)',
                        data: dados.historico_delay.dados,
                        borderColor: '#f44336',
                        backgroundColor: 'rgba(244, 67, 54, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 3
                    }]
                },
                options: {
                    responsive: true, 
                    maintainAspectRatio: false,
                    scales: { 
                        y: { beginAtZero: true, title: { display: true, text: 'Horas' } },
                        x: { ticks: { display: false } } 
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }

    } catch (e) {
        div.innerHTML = "<p style='color:red; text-align:center;'>Erro ao conectar com o servidor. Verifica o terminal.</p>";
        console.error(e);
    }
}

carregarNoticias();