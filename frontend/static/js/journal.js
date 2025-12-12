document.addEventListener("DOMContentLoaded", () => {

    let currentTab = "sales";
    loadJournalList(currentTab);

    // =============== FORMAT DATE ===============
    function formatDate(dateStr) {
        if (!dateStr) return "-";
        const d = new Date(dateStr);
        const day = String(d.getDate()).padStart(2, "0");
        const month = String(d.getMonth() + 1).padStart(2, "0");
        const year = String(d.getFullYear()).slice(2);
        const hours = String(d.getHours()).padStart(2, "0");
        const minutes = String(d.getMinutes()).padStart(2, "0");
        return `${day}.${month}.${year} ${hours}:${minutes}`;
    }

    // ================== TAB SWITCH ==================
    document.querySelectorAll("#journalTabs button").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll("#journalTabs button").forEach(x => x.classList.remove("active"));
            btn.classList.add("active");
            currentTab = btn.dataset.type;
            loadJournalList(currentTab);
        });
    });

    // ================= LOAD JOURNAL LIST =================
    function loadJournalList(type) {
        document.getElementById("journalContent").innerHTML = "Загрузка...";

        fetch(`/api/journals/?department=` + type)
            .then(r => r.json())
            .then(data => {
                if (!data.results || data.results.length === 0) {
                    document.getElementById("journalContent").innerHTML =
                        "<p class='text-muted'>Записів немає</p>";
                    return;
                }

                let html = `
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Дата</th>
                                <th>Клієнт</th>
                                <th>Телефон</th>
                                ${type === "service" ? "<th>Марка</th>" : ""}
                                ${type === "service" ? "<th>Модель</th>" : ""}
                                ${type === "service" ? "<th>Номер</th>" : ""}
                                <th>Коментар</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                data.results.forEach(r => {
                    const client = r.client ?? {};
                    const vehicle = r.vehicle ?? {};

                    html += `
                        <tr>
                            <td>${formatDate(r.date)}</td>
                            <td>${client?.name ?? "-"}</td>
                            <td>${client?.phone ?? "-"}</td>
                            ${type === "service" ? `<td>${vehicle?.brand ?? "-"}</td>` : ""}
                            ${type === "service" ? `<td>${vehicle?.model ?? "-"}</td>` : ""}
                            ${type === "service" ? `<td>${vehicle?.plate_number ?? "-"}</td>` : ""}
                            <td>${r.comment ?? "-"}</td>
                        </tr>
                    `;
                });

                html += "</tbody></table>";
                document.getElementById("journalContent").innerHTML = html;
            })
            .catch(e => {
                document.getElementById("journalContent").innerHTML =
                    `<p class="text-danger">Помилка: ${e}</p>`;
            });
    }

    // ============== OPEN MODAL ====================
    const modalEl = document.getElementById("journalModal");
    const modal = new bootstrap.Modal(modalEl);

    document.getElementById("openCreateModal").onclick = () => {
        document.getElementById("department").value = currentTab;

        document.getElementById("vehicle_block").style.display =
            currentTab === "service" ? "block" : "none";

        // очищаем поля
        clientInput.value = "";
        phoneInput.value = "";
        vehicleInput.value = "";
        brandInput.value = "";
        modelInput.value = "";
        comment.value = "";
        clientInput.dataset.clientId = "";
        vehicleInput.dataset.vehicleId = "";

        loadServices();
        modal.show();
    };

    // =============== LOAD SERVICE LIST ===============
    function loadServices() {
        if (currentTab !== "service") return;
        fetch("/api/services/")
            .then(r => r.json())
            .then(data => {
                let select = document.getElementById("service_input");
                select.innerHTML = "";
                data.results.forEach(s => {
                    select.innerHTML += `<option value="${s.id}">${s.name}</option>`;
                });
            });
    }

    // =============== AUTOCOMPLETE CLIENT ===============
    const clientInput = document.getElementById("client_input");
    const clientResults = document.getElementById("client_search_results");
    const phoneInput = document.getElementById("phone_input");

    clientInput.addEventListener("input", () => {
        const q = clientInput.value;
        if (q.length < 2) return;

        fetch(`/api/clients/auto_find/?q=${q}`)
            .then(r => r.json())
            .then(data => {
                clientResults.innerHTML = "";
                data.results.forEach(c => {
                    let item = document.createElement("button");
                    item.className = "list-group-item list-group-item-action";
                    item.textContent = `${c.name} — ${c.phone}`;
                    item.onclick = () => {
                        clientInput.value = c.name;
                        phoneInput.value = c.phone;
                        clientInput.dataset.clientId = c.id;
                        clientResults.innerHTML = "";
                    };
                    clientResults.appendChild(item);
                });
            });
    });

    // =============== AUTOCOMPLETE VEHICLE ===============
    const vehicleInput = document.getElementById("vehicle_input");
    const vehicleResults = document.getElementById("vehicle_search_results");
    const brandInput = document.getElementById("brand_input");
    const modelInput = document.getElementById("model_input");

    vehicleInput.addEventListener("input", () => {
        const q = vehicleInput.value;
        if (q.length < 2) return;

        fetch(`/api/vehicles/auto_find_by_number/?plate_number=${q}`)
            .then(r => r.json())
            .then(data => {
                vehicleResults.innerHTML = "";
                data.results.forEach(v => {
                    let item = document.createElement("button");
                    item.className = "list-group-item list-group-item-action";
                    item.textContent = `${v.plate_number} — ${v.brand} ${v.model}`;
                    item.onclick = () => {
                        vehicleInput.value = v.plate_number;
                        brandInput.value = v.brand;
                        modelInput.value = v.model;
                        vehicleInput.dataset.vehicleId = v.id;
                        vehicleResults.innerHTML = "";
                    };
                    vehicleResults.appendChild(item);
                });
            });
    });

    // =============== SAVE JOURNAL RECORD ===============
    document.getElementById("saveJournal").onclick = async () => {

        let client_id = clientInput.dataset.clientId || null;
        let vehicle_id = vehicleInput.dataset.vehicleId || null;

        // ===== CREATE NEW CLIENT IF NECESSARY =====
        if (!client_id) {
            const newClient = await fetch("/api/clients/", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    name: clientInput.value,
                    phone: phoneInput.value
                })
            }).then(r => r.json());
            client_id = newClient.id;
        }

        // ===== CREATE NEW VEHICLE IF NECESSARY (service only) =====
        if (currentTab === "service" && !vehicle_id) {
            const newVehicle = await fetch("/api/vehicles/", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    plate_number: vehicleInput.value,
                    brand: brandInput.value,
                    model: modelInput.value,
                    client_id
                })
            }).then(r => r.json());
            vehicle_id = newVehicle.id;
        }

        // ====== CREATE JOURNAL ENTRY ======
        const payload = {
            date: document.getElementById("datetime").value,
            comment: document.getElementById("comment").value,
            department: currentTab,
            client_id: client_id,
            vehicle_id: currentTab === "service" ? vehicle_id : null,
            service_id: currentTab === "service" ? document.getElementById("service_input").value : null
        };

        await fetch("/api/journals/", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        modal.hide();
        loadJournalList(currentTab);
    };

});
