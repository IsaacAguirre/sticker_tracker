const groupSelect = document.getElementById("group-select");
const countrySelect = document.getElementById("country-select");
const loadReportButton = document.getElementById("load-report");
const stickerInput = document.getElementById("sticker-input");
const saveStickersButton = document.getElementById("save-stickers");
const reportOutput = document.getElementById("report-output");
const saveStatus = document.getElementById("save-status");

let groupMap = {};
let expandedParallelId = null;

async function apiFetch(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    throw new Error(data.detail || data || response.statusText);
  }
  return data;
}

function formatReport(data) {
  const dupEntries = Object.entries(data.duplicates || {});
  const dupText = dupEntries.length > 0 ? dupEntries.map(([id, count]) => `${id} (x${count})`).join(", ") : "none";
  const totalDups = data.counts.total_duplicates || 0;
  const displayName = data.country_name || data.country;

  return [
    `Country: ${displayName}`,
    `Completion: ${data.completion_percentage}%`,
    `Unique Found: ${data.counts.found} / ${data.counts.total}`,
    `Missing: ${data.counts.missing}`,
    `Total Duplicates (Extras): ${totalDups}`,
    "",
    `Missing: ${data.missing.join(", ") || "none"}`,
    `Duplicates: ${dupText}`,
  ].join("\n");
}

function showMessage(message, type = "success") {
  saveStatus.textContent = message;
  saveStatus.className = `status ${type}`;
}

async function loadGroups() {
  try {
    const data = await apiFetch("/groups");
    groupMap = data.groups || {};
    const groupOptions = Object.keys(groupMap)
      .map((groupKey) => `<option value="${groupKey}">${groupKey}</option>`)
      .join("");
    groupSelect.innerHTML = groupOptions;
    if (groupSelect.options.length > 0) {
      countrySelect.innerHTML = groupMap[groupSelect.value]
        .map((code) => `<option value="${code}">${code}</option>`)
        .join("");
    }
  } catch (error) {
    reportOutput.textContent = `Error loading groups: ${error.message}`;
    showMessage("Could not load groups.", "error");
  }
}

function updateCountryOptions() {
  const selectedGroup = groupSelect.value;
  const countries = groupMap[selectedGroup] || [];
  countrySelect.innerHTML = countries
    .map((code) => `<option value="${code}">${code}</option>`)
    .join("");
}

async function loadReport() {
  const countryCode = countrySelect.value;
  if (!countryCode) {
    return;
  }

  try {
    const data = await apiFetch(`/inventory/${countryCode}`);
    renderStickerGrid(data);
    showMessage("Report loaded.", "success");
  } catch (error) {
    reportOutput.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    showMessage("Could not load report.", "error");
  }
}

function renderStickerGrid(data) {
  reportOutput.innerHTML = "";
  const parallelTypes = data.parallel_types || [];
  
  const dupEntries = Object.entries(data.duplicates || {});
  const dupListText = dupEntries.length > 0 
    ? dupEntries.map(([id, count]) => `<strong>${id}</strong> (${count - 1})`).join(", ") 
    : "none";

  const summary = document.createElement("div");
  summary.className = "report-summary";
  summary.innerHTML = `
    <h2>${data.country_name || data.country}</h2>
    <p>Completion: <strong>${data.completion_percentage}%</strong> (${data.counts.found} / ${data.counts.total})</p>
    <p>Total Extras: <strong>${data.counts.total_duplicates}</strong></p>
    <p style="font-size: 0.9em; color: #555; margin-top: 5px;">Detailed Extras (ID and quantity): ${dupListText}</p>
  `;
  reportOutput.appendChild(summary);

  Object.entries(data.sections).forEach(([sectionName, stickers]) => {
    const sectionHeader = document.createElement("h3");
    sectionHeader.textContent = sectionName;
    reportOutput.appendChild(sectionHeader);

    const grid = document.createElement("div");
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = "repeat(auto-fill, minmax(120px, 1fr))";
    grid.style.gap = "10px";
    grid.style.padding = "10px 0";

    Object.entries(stickers).forEach(([id, count]) => {
      const stickerParallels = (data.parallels && data.parallels[id]) || {};
      const hasParallels = Object.values(stickerParallels).some(v => v > 0);

      const card = document.createElement("div");
      card.id = `sticker-${id}`;
      card.style.border = count > 1 ? "2px solid #fbc02d" : "1px solid #ccc";
      card.style.padding = "10px";
      card.style.textAlign = "center";
      card.style.backgroundColor = count > 1 ? "#fff9c4" : (count > 0 ? "#e6fffa" : "#fff5f5");
      card.style.position = "relative";
      card.style.borderRadius = "4px";
      
      const isExpanded = expandedParallelId === id;
      card.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 5px;">${id}</div>
        <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
          <button onclick="updateCount('${id}', ${count - 1})" style="padding: 2px 8px;">-</button>
          <span>${count}</span>
          <button onclick="updateCount('${id}', ${count + 1})" style="padding: 2px 8px;">+</button>
        </div>
        ${parallelTypes.length > 0 ? `
          <div style="margin-top: 10px; border-top: 1px dashed #ccc; padding-top: 5px;">
            <button onclick="toggleParallels('${id}')" style="font-size: 0.8em; background: none; border: 1px solid #999; border-radius: 3px; cursor: pointer; color: ${hasParallels ? '#d32f2f' : '#666'}">
              ${hasParallels ? '★ Parallels' : 'Parallels'}
            </button>
          <div id="parallels-${id}" style="display: ${isExpanded ? 'block' : 'none'}; margin-top: 5px; font-size: 0.85em; text-align: left;">
              ${parallelTypes.map(type => {
                const pCount = stickerParallels[type] || 0;
                return `
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                    <span style="color: ${type}; font-weight: bold;">${type}:</span>
                    <div style="display: flex; gap: 4px; align-items: center;">
                      <button onclick="updateParallelCount('${id}', '${type}', ${pCount - 1})" style="padding: 0 4px; font-size: 0.8em;">-</button>
                      <span>${pCount}</span>
                      <button onclick="updateParallelCount('${id}', '${type}', ${pCount + 1})" style="padding: 0 4px; font-size: 0.8em;">+</button>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>` : ''}
      `;
      grid.appendChild(card);
    });
    reportOutput.appendChild(grid);
  });
}

window.toggleParallels = function(id) {
  const el = document.getElementById(`parallels-${id}`);
  if (el) {
    const isOpening = el.style.display === "none";
    el.style.display = isOpening ? "block" : "none";
    expandedParallelId = isOpening ? id : null;
  }
};

window.updateCount = async function(stickerId, newCount) {
  if (newCount < 0) return;
  const countryCode = countrySelect.value;
  try {
    const data = await apiFetch(`/inventory/${countryCode}/sticker`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sticker_id: stickerId, count: newCount }),
    });
    renderStickerGrid(data);
  } catch (error) {
    showMessage(error.message, "error");
  }
};

window.updateParallelCount = async function(stickerId, type, newCount) {
  if (newCount < 0) return;
  const countryCode = countrySelect.value;
  try {
    const data = await apiFetch(`/inventory/${countryCode}/parallel`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sticker_id: stickerId, parallel_type: type, count: newCount }),
    });
    renderStickerGrid(data);
  } catch (error) {
    showMessage(error.message, "error");
  }
};

async function saveStickers() {
  const countryCode = countrySelect.value;
  const stickersText = stickerInput.value.trim();
  if (!countryCode || !stickersText) {
    showMessage("Select a group and country, and enter sticker numbers.", "error");
    return;
  }

  try {
    const payload = { stickers: stickersText };
    const data = await apiFetch(`/inventory/${countryCode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderStickerGrid(data);
    showMessage("Stickers saved successfully.", "success");
    stickerInput.value = "";
  } catch (error) {
    showMessage(error.message, "error");
  }
}

loadGroups();
groupSelect.addEventListener("change", updateCountryOptions);
loadReportButton.addEventListener("click", loadReport);
saveStickersButton.addEventListener("click", saveStickers);
