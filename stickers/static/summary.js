const overviewOutput = document.getElementById("overview-output");
const topOutput = document.getElementById("top-output");
const bottomOutput = document.getElementById("bottom-output");
const statusMessage = document.getElementById("status-message");

async function apiFetch(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    throw new Error(data.detail || data || response.statusText);
  }
  return data;
}

function renderOverview(report) {
  return `
    Total countries tracked: ${report.country_count}
    Total global sticker sets: ${report.global_count}
    Total tracked inventories: ${report.total_tracked_inventories}
    Total possible sticker IDs: ${report.total_possible_stickers}
    Total owned sticker IDs: ${report.total_owned_sticker_ids}

    Total duplicates: ${report.total_duplicates}
    Total missing sticker IDs: ${report.total_missing_sticker_ids}
    Missing means sticker IDs with zero copies.
  `.trim();
}

function renderCompletionList(items) {
  if (!items.length) {
    return "<p>No countries available.</p>";
  }

  return `<ul>${items
    .map((item) => {
      const displayName = item.country_name || item.country;
      return `<li>${displayName}: ${item.completion_percentage}% (${item.counts.found}/${item.counts.total})</li>`;
    })
    .join("")}</ul>`;
}

function renderTieNote(count, percentage) {
  if (!count) {
    return "";
  }
  return `<p>${count} more countries are tied at ${percentage}% and are not displayed.</p>`;
}

async function loadSummary() {
  try {
    const data = await apiFetch("/summary");
    overviewOutput.innerText = renderOverview(data);
    topOutput.innerHTML = renderCompletionList(data.top_countries) + renderTieNote(data.top_tie_count, data.top_tie_percentage);
    bottomOutput.innerHTML = renderCompletionList(data.bottom_countries) + renderTieNote(data.bottom_tie_count, data.bottom_tie_percentage);
    statusMessage.textContent = "Summary loaded.";
    statusMessage.className = "status success";
  } catch (error) {
    overviewOutput.textContent = "Unable to load summary.";
    topOutput.textContent = "";
    bottomOutput.textContent = "";
    statusMessage.textContent = `Error: ${error.message}`;
    statusMessage.className = "status error";
  }
}

loadSummary();
