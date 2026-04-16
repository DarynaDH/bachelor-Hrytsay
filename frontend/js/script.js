const BASE_URL = "http://localhost:8000";
let lastStats = null;
let chart;

// очищення тексту від markdown
function cleanText(text) {
  return text
    .replace(/\*\*/g, "")
    .replace(/#/g, "");
}

function renderChart(data) {
  const ctx = document.getElementById('chart');

  if (chart) chart.destroy();

  chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Join', 'Leave'],
      datasets: [{
        label: 'Активність',
        data: [data.joins, data.leaves],
        backgroundColor: ['#3b82f6', '#1e3a8a'],
        borderRadius: 8
      }]
    },
    options: {
      plugins: {
        legend: {
          labels: { color: '#1e293b' }
        }
      },
      scales: {
        x: {
          ticks: { color: '#1e293b' },
          grid: { display: false }
        },
        y: {
          ticks: { color: '#1e293b' },
          grid: { color: '#e2e8f0' }
        }
      }
    }
  });
}

async function loadData() {
  try {
    const report = await fetch(`${BASE_URL}/report/today`);
    const data = await report.json();

    document.getElementById("stats").innerHTML = `
      <div>Подій: ${data.total_events}</div>
      <div>Join: ${data.joins}</div>
      <div>Leave: ${data.leaves}</div>
      <div>Унікальні гравці: ${data.unique_players}</div>
    `;

    renderChart(data);

    // беремо попередні дані з localStorage
    const savedStats = JSON.parse(localStorage.getItem("stats"));

    const isSame =
      savedStats &&
      savedStats.total_events === data.total_events &&
      savedStats.joins === data.joins &&
      savedStats.leaves === data.leaves &&
      savedStats.unique_players === data.unique_players;

    if (!isSame) {
      console.log("Дані змінились — викликаємо AI");

      const summaryRes = await fetch(`${BASE_URL}/summary/today`);
      const summaryData = await summaryRes.json();

      document.getElementById("summary").innerText =
        cleanText(summaryData.summary);

      // зберігаємо
      localStorage.setItem("stats", JSON.stringify(data));
      localStorage.setItem("summary", summaryData.summary);

    } else {
      console.log("Без змін — беремо кеш");

      const savedSummary = localStorage.getItem("summary");

      if (savedSummary) {
        document.getElementById("summary").innerText =
          cleanText(savedSummary);
      }
    }

  } catch (error) {
    console.error(error);
    alert("Помилка підключення до backend");
  }
}

// авто-завантаження
loadData();