document.addEventListener("DOMContentLoaded", () => {
    let currentTab = "sales";
    loadJournalList(currentTab);

    // =========== TAB SWITCH ============
    document.querySelectorAll("#journalTabs button").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll("#journalTabs button").forEach(x => x.classList.remove("active"));
            btn.classList.add("active");
            currentTab = btn.dataset.type;
            loadJournalList(currentTab);
        });
    });

    // =========== LOAD LISTS =============
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
                            <th>Авто</th>
                            <th>Коментар</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            data.results.forEach(r => {
                html += `
                    <tr>
                        <td>${r.date}</td>
                        <td>${r.client.name || "-"}</td>
                        <td>${r.client.phone || "-"}</td>
                        <td>${r.vehicle.plate_number || "-"}</td>
                        <td>${r.comment || "-"}</td>
                    </tr>
                `;
            });

            html += "</tbody></table>";

            document.getElementById("journalContent").innerHTML = html;
        })
        .catch(err => {
            document.getElementById("journalContent").innerHTML =
                "<p class='text-danger'>Помилка завантаження ${err}</p>";
        });
    }

    // =========== OPEN MODAL ============
    const modalEl = document.getElementById("journalModal");
    const modal = new bootstrap.Modal(modalEl);

    document.getElementById("openCreateModal").onclick = () => {
        document.getElementById("department").value = currentTab;

        // Сервис → показываем авто
        document.getElementById("vehicle_block").style.display =
            currentTab === "service" ? "block" : "none";

        modal.show();
    };

    // =========== AUTOCOMPLETE CLIENT ============
    const clientInput = document.getElementById("client_input");
    const clientResults = document.getElementById("client_search_results");

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
                        clientInput.value = `${c.name}`;
                        clientInput.dataset.clientId = c.id;
                        clientResults.innerHTML = "";
                    };
                    clientResults.appendChild(item);
                });
            });
    });

    // =========== AUTOCOMPLETE VEHICLE ============
    const vehicleInput = document.getElementById("vehicle_input");
    const vehicleResults = document.getElementById("vehicle_search_results");

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
                        vehicleInput.dataset.vehicleId = v.id;
                        vehicleResults.innerHTML = "";
                    };
                    vehicleResults.appendChild(item);
                });
            });
    });

    // =========== SAVE JOURNAL ============
    document.getElementById("saveJournal").onclick = () => {
        let payload = {
            datetime: document.getElementById("datetime").value,
            comment: document.getElementById("comment").value,
            department: currentTab,
            client_id: clientInput.dataset.clientId || null,
            vehicle_id: vehicleInput.dataset.vehicleId || null
        };

        fetch("/api/journals/", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        })
            .then(r => r.json())
            .then(data => {
                modal.hide();
                loadJournalList(currentTab);
            });
    };
});
