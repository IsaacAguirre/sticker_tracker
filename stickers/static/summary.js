console.log("summary.js loaded");
const overviewOutput = document.getElementById("overview-output");
const topOutput = document.getElementById("top-output");
const bottomOutput = document.getElementById("bottom-output");
const statusMessage = document.getElementById("status-message");

function renderOverview(report) {
  return `
    <div class="html-report" style="line-height: 1.6;">
      <div class="trackers-row">
        <div class="tracker">
          <div class="tracker-title">Trackers Complete</div>
          <div class="tracker-bar" aria-hidden="true"><div class="tracker-fill" style="width: ${report.inventory_completion_percentage}%;"></div></div>
          <div class="tracker-text">${report.total_inventories_completed} / ${report.total_tracked_inventories} (${report.inventory_completion_percentage}%)</div>
        </div>
        <div class="tracker">
          <div class="tracker-title">Sticker Progress</div>
          <div class="tracker-bar" aria-hidden="true"><div class="tracker-fill" style="width: ${report.overall_sticker_completion_percentage}%;"></div></div>
          <div class="tracker-text">${report.total_owned_sticker_ids} / ${report.total_possible_stickers} (${report.overall_sticker_completion_percentage}%)</div>
        </div>
        <div class="tracker" style="background: #eff6ff; padding: 10px; border-radius: 12px; border: 1px solid #bfdbfe;">
          <div class="tracker-title" style="color: var(--primary);">Unique Coverage</div>
          <div class="tracker-bar" aria-hidden="true"><div class="tracker-fill" style="width: ${report.overall_unique_completion_percentage}%;"></div></div>
          <div class="tracker-text"><strong>${report.total_unique_slots_filled} / ${report.total_possible_stickers} (${report.overall_unique_completion_percentage}%)</strong></div>
          <small style="color: #60a5fa; display: block; margin-top: 4px; font-size: 0.7rem;">Counts IDs with Base or Parallel</small>
        </div>
      </div>
      <hr>
      <p>Total countries tracked: ${report.country_count}</p>
      <p>Total global sticker sets: ${report.global_count}</p>
      <p>Total tracked inventories: ${report.total_tracked_inventories}</p>
      <p>Total possible sticker IDs: ${report.total_possible_stickers}</p>
      <p>Total owned sticker IDs: ${report.total_owned_sticker_ids}</p>
      <br>
      <p>Total duplicates: ${report.total_duplicates}</p>
      <p>Total missing sticker IDs: ${report.total_missing_sticker_ids}</p>
      <small><em>Missing means sticker IDs with zero copies. Duplicates count extra copies only.</em></small>
    </div>
  `;
}

function renderCompletionList(items) {
  if (!items.length) {
    return "<p>No countries available.</p>";
  }

  return `<ul>${items
    .map((item) => {
      const displayName = item.country_name || item.country;
      const flagUrl = getFlagUrl(item.country);
      const flagHtml = flagUrl ? `<img src="${flagUrl}" class="flag-icon" alt="">` : '';
      return `<li>${flagHtml}${displayName}: ${item.completion_percentage}% (${item.counts.found}/${item.counts.total})</li>`;
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
    console.log("summary data:", data);
    overviewOutput.innerHTML = renderOverview(data);
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
