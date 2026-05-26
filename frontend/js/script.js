const BASE_URL = "http://localhost:8000";
let barChart;
let hourlyChart;

function cleanText(text) {
  return text.replace(/\*\*/g, "").replace(/#/g, "");
}

function badgeClass(eventType) {
  if (eventType === "player_join") return "badge badge-join";
  if (eventType === "player_leave") return "badge badge-leave";
  return "badge badge-other";
}

function formatEventType(eventType) {
  const labels = { player_join: "Вхід", player_leave: "Вихід" };
  return labels[eventType] || eventType;
}

function formatDate(dateStr) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  if (isNaN(d)) return dateStr;
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${day}.${month} ${hh}:${mm}`;
}

function renderStats(data) {
  const statusColor = {
    "Сервер активний": "#16a34a",
    "Спостерігається відтік гравців": "#dc2626",
    "Сервер неактивний": "#94a3b8",
    "Стабільна активність": "#2563eb",
  };
  const color = statusColor[data.status] || "#0f172a";

  document.getElementById("stats").innerHTML = `
    <div class="stats-numbers">
      <div class="stat-num">
        <span class="stat-value">${data.total_events}</span>
        <span class="stat-label">Подій</span>
      </div>
      <div class="stat-num">
        <span class="stat-value green">${data.joins}</span>
        <span class="stat-label">Входів</span>
      </div>
      <div class="stat-num">
        <span class="stat-value red">${data.leaves}</span>
        <span class="stat-label">Виходів</span>
      </div>
      <div class="stat-num">
        <span class="stat-value blue">${data.unique_players}</span>
        <span class="stat-label">Гравців</span>
      </div>
    </div>
    <div class="stats-info">
      <div class="stat-info-item">
        <span class="stat-info-label">Статус</span>
        <span class="stat-info-value" style="color:${color}">${data.status}</span>
      </div>
      <div class="stat-info-item">
        <span class="stat-info-label">Тренд</span>
        <span class="stat-info-value">${data.trend}</span>
      </div>
      <div class="stat-info-item">
        <span class="stat-info-label">Пік активності</span>
        <span class="stat-info-value">${data.peak_hour !== null ? data.peak_hour + ":00" : "—"}</span>
      </div>
    </div>
  `;
}

function renderBarChart(data) {
  const ctx = document.getElementById("chart");
  if (barChart) barChart.destroy();
  barChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Join", "Leave"],
      datasets: [{
        data: [data.joins, data.leaves],
        backgroundColor: ["#22c55e", "#ef4444"],
        borderRadius: 8,
        borderSkipped: false,
      }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#f1f5f9" } },
        x: { grid: { display: false } }
      }
    }
  });
}

async function loadHourlyChart() {
  try {
    const res = await fetch(`${BASE_URL}/stats/hourly`);
    const data = await res.json();
    const ctx = document.getElementById("hourlyChart");
    if (hourlyChart) hourlyChart.destroy();
    hourlyChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.hours.map(h => `${h}:00`),
        datasets: [{
          label: "Подій",
          data: data.values,
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59,130,246,0.08)",
          tension: 0.4,
          fill: true,
          pointRadius: 3,
          pointBackgroundColor: "#3b82f6",
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#f1f5f9" } },
          x: { grid: { display: false } }
        }
      }
    });
  } catch (e) { console.error("HOURLY ERROR:", e); }
}

async function loadEvents() {
  try {
    const res = await fetch(`${BASE_URL}/events/recent`);
    const data = await res.json();
    const tbody = document.getElementById("events-table");
    tbody.innerHTML = "";
    data.events.forEach(e => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${e.id}</td>
        <td><span class="${badgeClass(e.event_type)}">${formatEventType(e.event_type)}</span></td>
        <td>${e.player_name || "—"}</td>
        <td>${formatDate(e.created_at)}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (e) { console.error("EVENTS ERROR:", e); }
}

async function loadData() {
  try {
    const reportRes = await fetch(`${BASE_URL}/report/today`);
    const data = await reportRes.json();

    renderStats(data);
    renderBarChart(data);

    const savedStats = JSON.parse(localStorage.getItem("stats") || "null");
    const isSame = savedStats &&
      savedStats.total_events === data.total_events &&
      savedStats.joins === data.joins &&
      savedStats.leaves === data.leaves &&
      savedStats.unique_players === data.unique_players;

    if (!isSame) {
      const summaryRes = await fetch(`${BASE_URL}/summary/today`);
      const summaryData = await summaryRes.json();
      document.getElementById("summary").innerText = cleanText(summaryData.summary);
      localStorage.setItem("stats", JSON.stringify(data));
      localStorage.setItem("summary", summaryData.summary);
    } else {
      const saved = localStorage.getItem("summary");
      if (saved) document.getElementById("summary").innerText = cleanText(saved);
    }

    loadEvents();
    loadPlayers();
    loadHourlyChart();
  } catch (e) {
    console.error(e);
    document.getElementById("stats").innerText = "❌ Помилка підключення до backend";
  }
}

loadData();

async function loadPlayers() {
  try {
    const res = await fetch(`${BASE_URL}/players/top`);
    const data = await res.json();
    const tbody = document.getElementById("players-table");
    tbody.innerHTML = "";

    if (!data.players.length) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:20px">Даних поки немає</td></tr>';
      return;
    }

    const medals = ["🥇", "🥈", "🥉"];
    const rankClass = ["rank-1", "rank-2", "rank-3"];

    data.players.forEach((p, i) => {
      const rank = i < 3
        ? `<span class="${rankClass[i]}">${medals[i]}</span>`
        : `${i + 1}`;
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${rank}</td>
        <td>${p.player_name || "—"}</td>
        <td><b>${p.total_sessions}</b></td>
        <td>${formatDate(p.first_seen)}</td>
        <td>${formatDate(p.last_seen)}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (e) {
    console.error("PLAYERS ERROR:", e);
  }
}