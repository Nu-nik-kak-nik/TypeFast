class UserStatistics {
  constructor() {
    this.userId = window.location.pathname.split("/").pop();
    this.statisticsContainer = document.getElementById("user-statistics");
    this.charts = {};

    this.init();
  }

  setThemeFromLocalStorage() {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
      document.body.setAttribute("data-theme", savedTheme);
    }
  }

  async init() {
    this.setThemeFromLocalStorage();
    this.setupEventListeners();
    await this.loadStatistics();
  }

  destroy() {
    Object.values(this.charts).forEach((chart) => chart.destroy());
  }

  setupEventListeners() {
    document.getElementById("back-btn").addEventListener("click", () => {
      window.history.back();
    });
  }

  async loadStatistics() {
    try {
      this.showLoading(true);

      const response = await fetch(`/api/statistics/${this.userId}`, {
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Ошибка загрузки: ${response.status}`);
      }

      const data = await response.json();
      this.renderStatistics(data);
    } catch (error) {
      console.error("Ошибка загрузки статистики:", error);
      this.showError(error.message);
    } finally {
      this.showLoading(false);
    }
  }

  renderStatistics(data) {
    const hasResults = data.all_test_results?.length > 0;

    this.statisticsContainer.innerHTML = `
            <div class="user-stats">
                <div class="stats-subheader">
                    <h2>Общая статистика</h2>
                    ${hasResults ? `<span class="tests-count">Всего тестов: ${data.all_test_results.length}</span>` : ""}
                </div>

                ${hasResults ? this.renderStatsGrid(data) : this.renderNoResults()}

                ${hasResults ? this.renderChartsSection(data) : ""}
            </div>
        `;

    if (hasResults) {
      this.initCharts(data.all_test_results);
    }
  }

  renderStatsGrid(data) {
    return `
            <div class="stats-grid">
                ${this.renderStatCard("📊", "Последний тест", [
                  {
                    label: "Скорость",
                    value: `${data.last_result?.chars_per_minute || 0} зн./мин`,
                  },
                  {
                    label: "Точность",
                    value: `${data.last_result?.accuracy || 0}%`,
                  },
                ])}

                ${this.renderStatCard("🚀", "Лучший результат", [
                  {
                    label: "Скорость",
                    value: `${data.best_performance?.chars_per_minute || 0} зн./мин`,
                  },
                  {
                    label: "Точность",
                    value: `${data.best_performance?.accuracy || 0}%`,
                  },
                ])}

                ${this.renderStatCard("📈", "Средние показатели", [
                  {
                    label: "Скорость",
                    value: `${data.avg_statistics?.avg_chars_per_minute || 0} зн./мин`,
                  },
                  {
                    label: "Точность",
                    value: `${data.avg_statistics?.avg_accuracy || 0}%`,
                  },
                ])}
            </div>
        `;
  }

  renderChartsSection(data) {
    return `
            <div class="charts-section">
                <h3>Визуальная статистика</h3>
                <div class="charts-container">
                    <div class="chart-wrapper">
                        <canvas id="speed-chart"></canvas>
                        <div class="chart-title">Динамика скорости</div>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="accuracy-chart"></canvas>
                        <div class="chart-title">Динамика точности</div>
                    </div>
                </div>
            </div>
        `;
  }

  renderStatCard(icon, title, items) {
    return `
            <div class="stat-card">
                <div class="stat-icon">${icon}</div>
                <div class="stat-content">
                    <h4>${title}</h4>
                    ${items
                      .map(
                        (item) => `
                        <div class="stat-item">
                            <span class="stat-label">${item.label}:</span>
                            <span class="stat-value">${item.value}</span>
                        </div>
                    `,
                      )
                      .join("")}
                </div>
            </div>
        `;
  }

  renderNoResults() {
    return `
            <div class="no-results">
                <div class="no-results-icon">📝</div>
                <h3>Тесты еще не пройдены</h3>
                <p>Статистика появится после прохождения первых тестов</p>
            </div>
        `;
  }

  initCharts(tests) {
    const dates = tests.map((test) => this.formatDate(test.created_at, true));
    const speeds = tests.map((test) => test.chars_per_minute);
    const accuracies = tests.map((test) => test.accuracy);

    this.charts.speed = new Chart(document.getElementById("speed-chart"), {
      type: "line",
      data: {
        labels: dates,
        datasets: [
          {
            label: "Скорость (зн./мин)",
            data: speeds,
            borderColor: getComputedStyle(
              document.documentElement,
            ).getPropertyValue("--accent"),
            backgroundColor: "rgba(254, 128, 25, 0.1)",
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointBackgroundColor: getComputedStyle(
              document.documentElement,
            ).getPropertyValue("--accent"),
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
            pointRadius: 5,
            pointHoverRadius: 7,
          },
        ],
      },
      options: this.getChartOptions("Скорость печати"),
    });

    this.charts.accuracy = new Chart(
      document.getElementById("accuracy-chart"),
      {
        type: "line",
        data: {
          labels: dates,
          datasets: [
            {
              label: "Точность (%)",
              data: accuracies,
              borderColor: getComputedStyle(
                document.documentElement,
              ).getPropertyValue("--success"),
              backgroundColor: "rgba(184, 187, 38, 0.1)",
              borderWidth: 3,
              tension: 0.4,
              fill: true,
              pointBackgroundColor: getComputedStyle(
                document.documentElement,
              ).getPropertyValue("--success"),
              pointBorderColor: "#fff",
              pointBorderWidth: 2,
              pointRadius: 5,
              pointHoverRadius: 7,
            },
          ],
        },
        options: this.getChartOptions("Точность печати"),
      },
    );
  }

  getChartOptions(title) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          backgroundColor: "rgba(0, 0, 0, 0.8)",
          titleFont: {
            family: "JetBrains Mono, Fira Code, monospace",
          },
          bodyFont: {
            family: "JetBrains Mono, Fira Code, monospace",
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: "rgba(255, 255, 255, 0.1)",
          },
          ticks: {
            font: {
              family: "JetBrains Mono, Fira Code, monospace",
            },
          },
        },
        x: {
          grid: {
            display: false,
          },
          ticks: {
            font: {
              family: "JetBrains Mono, Fira Code, monospace",
            },
            maxRotation: 45,
            minRotation: 45,
          },
        },
      },
    };
  }

  formatDate(dateString, short = false) {
    if (!dateString) return "Нет данных";

    const date = new Date(dateString);
    if (short) {
      return date.toLocaleDateString("ru-RU", {
        day: "2-digit",
        month: "2-digit",
      });
    }

    return date.toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  showLoading(show) {
    const loading = this.statisticsContainer.querySelector(".loading");
    if (loading) {
      loading.style.display = show ? "flex" : "none";
    }
  }

  showError(message) {
    this.statisticsContainer.innerHTML = `
            <div class="error-state">
                <div class="error-icon">⚠️</div>
                <h3>Ошибка загрузки</h3>
                <p>${message || "Не удалось загрузить статистику"}</p>
                <button class="btn-primary" onclick="location.reload()">Попробовать снова</button>
            </div>
        `;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  new UserStatistics();
});

window.addEventListener("storage", (event) => {
  if (event.key === "theme") {
    document.body.setAttribute("data-theme", event.newValue);
  }
});

window.addEventListener("beforeunload", () => {
  if (window.userStatsInstance) {
    window.userStatsInstance.destroy();
  }
});
