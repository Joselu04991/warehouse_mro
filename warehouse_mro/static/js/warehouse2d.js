let MAP_DATA = [];
let MAP_ZOOM = 1;

async function loadMap2D() {
    const response = await fetch("/warehouse2d/map-data");
    MAP_DATA = await response.json();

    renderMap(MAP_DATA);
    updateCounters(MAP_DATA);
    updateKpis(MAP_DATA);
}

function renderMap(data) {
    const container = document.getElementById("map-container");
    container.innerHTML = "";

    data.forEach(loc => {
        const div = document.createElement("div");
        div.classList.add("block");

        const status = loc.status; // "vacío", "normal", "bajo", "crítico"

        div.classList.add({
            "vacío": "block-vacio",
            "normal": "block-normal",
            "bajo": "block-bajo",
            "crítico": "block-critico"
        }[status] || "block-normal");

        div.innerHTML = `
            <div style="font-size:16px;">${loc.location}</div>
            <small style="opacity:.8;">${loc.items} materiales</small>
        `;

        div.onclick = () => showLocationDetail(loc.location);
        container.appendChild(div);
    });
}

function updateCounters(data) {
    document.getElementById("count-normal").innerText = data.filter(x => x.status === "normal").length;
    document.getElementById("count-bajo").innerText = data.filter(x => x.status === "bajo").length;
    document.getElementById("count-critico").innerText = data.filter(x => x.status === "crítico").length;
    document.getElementById("count-vacio").innerText = data.filter(x => x.status === "vacío").length;
}

function updateKpis(data) {
    const totalUbicaciones = data.length;
    const criticas = data.filter(x => x.status === "crítico");
    const vacias = data.filter(x => x.status === "vacío");
    const bajos = data.filter(x => x.status === "bajo");

    // Top 5 ubicaciones con más materiales
    const topItems = [...data]
        .sort((a, b) => b.items - a.items)
        .slice(0, 5);

    // Top 5 ubicaciones con mayor stock total
    const topStock = [...data]
        .sort((a, b) => b.total_libre - a.total_libre)
        .slice(0, 5);

    let html = `
        <p><strong>Total de ubicaciones:</strong> ${totalUbicaciones}</p>
        <p><strong>Ubicaciones críticas:</strong> ${criticas.length}</p>
        <p><strong>Ubicaciones con stock bajo:</strong> ${bajos.length}</p>
        <p><strong>Ubicaciones vacías:</strong> ${vacias.length}</p>

        <hr>
        <h6 class="fw-bold">Top 5 por número de materiales</h6>
        <ul class="mb-2">
    `;

    topItems.forEach(l => {
        html += `<li>${l.location} – ${l.items} materiales</li>`;
    });

    html += `</ul><h6 class="fw-bold">Top 5 por stock total</h6><ul>`;

    topStock.forEach(l => {
        html += `<li>${l.location} – ${l.total_libre}</li>`;
    });

    html += `</ul>`;

    document.getElementById("kpi-panel").innerHTML = html;
}

function filterStatus(status) {
    if (status === "todos") {
        renderMap(MAP_DATA);
        updateCounters(MAP_DATA);
        updateKpis(MAP_DATA);
        return;
    }
    const filtered = MAP_DATA.filter(x => x.status === status);
    renderMap(filtered);
    updateCounters(filtered);
    updateKpis(filtered);
}

document.getElementById("searchBox").addEventListener("input", (e) => {
    const text = e.target.value.toLowerCase();
    const filtered = MAP_DATA.filter(x => x.location.toLowerCase().includes(text));
    renderMap(filtered);
    updateCounters(filtered);
    updateKpis(filtered);
});

async function showLocationDetail(location) {
    const response = await fetch(`/warehouse2d/location/${location}`);
    const data = await response.json();

    document.getElementById("modal-location").innerHTML =
        `<span class="fw-bold">Ubicación:</span> ${data.ubicacion}`;

    let html = "";
    data.items.forEach(item => {
        html += `
        <tr>
            <td>${item.material_code}</td>
            <td>${item.material_text}</td>
            <td>${item.base_unit}</td>
            <td>${item.stock_seguridad}</td>
            <td>${item.stock_maximo}</td>
            <td>${item.libre_utilizacion}</td>
            <td class="fw-bold text-uppercase">${item.status}</td>
        </tr>`;
    });

    document.getElementById("location-details").innerHTML = html;

    const modal = new bootstrap.Modal(document.getElementById("locationModal"));
    modal.show();
}

function zoomIn() {
    MAP_ZOOM += 0.1;
    document.getElementById("map-container").style.transform = `scale(${MAP_ZOOM})`;
}

function zoomOut() {
    MAP_ZOOM = Math.max(0.5, MAP_ZOOM - 0.1);
    document.getElementById("map-container").style.transform = `scale(${MAP_ZOOM})`;
}

window.onload = loadMap2D;
