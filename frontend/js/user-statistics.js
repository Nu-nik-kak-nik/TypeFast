class UserStatistics {
  constructor() {
    this.userId = window.location.pathname.split("/").pop();
    this.statisticsContainer = document.getElementById("user-statistics");
    this.charts = {};
    this.currentTheme = localStorage.getItem("theme") || "dark";

    window.userStatsInstance = this;

    this.init();
  }

  setThemeFromLocalStorage() {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
      document.body.setAttribute("data-theme", savedTheme);
      this.currentTheme = savedTheme;
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

    window.addEventListener("storage", (event) => {
      if (event.key === "theme") {
        this.currentTheme = event.newValue;
        document.body.setAttribute("data-theme", event.newValue);
        this.updateChartsTheme();
      }
    });
  }

  async loadStatistics() {
    if (this.userId === "anonymous") {
      this.renderStatistics({ all_test_results: [] });
      return;
    }

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

    if (!hasResults) {
      this.statisticsContainer.innerHTML = this.renderNoResults();
      return;
    }

    this.statisticsContainer.innerHTML = `
      <div class="user-stats">
        <div class="stats-subheader">
          <h2>Общая статистика</h2>
          <span class="tests-count">Всего тестов: ${data.all_test_results.length}</span>
        </div>

        ${this.renderStatsGrid(data)}
        ${this.renderChartsSection(data)}
      </div>
    `;

    this.initCharts(data.all_test_results);
  }

  renderStatsGrid(data) {
    const avgStats = data.avg_statistics || {};
    const progressMetrics = data.progress_metrics || {};
    const lastResult = data.last_result || {};
    const bestPerformance = data.best_performance || {};

    const getProgressPercentage = (metricKey) => {
      return progressMetrics[metricKey] || 0;
    };

    const getProgressIndicator = (value) => {
      if (value > 0) {
        return {
          color: "var(--success)",
          icon: "📈",
          text: "Улучшение",
        };
      } else if (value < 0) {
        return {
          color: "var(--error)",
          icon: "📉",
          text: "Снижение",
        };
      } else {
        return {
          color: "var(--secondary)",
          icon: "➖",
          text: "Без изменений",
        };
      }
    };

    const speedProgressPercent = getProgressPercentage("speed_progress");
    const accuracyProgressPercent = getProgressPercentage("accuracy_progress");
    const timeProgressPercent = getProgressPercentage("time_progress");

    return `
      <div class="stats-grid">
        ${this.renderStatCard("📅", "Последний тест", [
          {
            label: "Скорость",
            value: `${lastResult.chars_per_minute || 0} зн./мин`,
          },
          {
            label: "Точность",
            value: `${lastResult.accuracy || 0}%`,
          },
          {
            label: "Время",
            value: `${lastResult.time || 0} сек`,
          },
        ])}

        ${this.renderStatCard("🚀", "Лучший результат", [
          {
            label: "Скорость",
            value: `${bestPerformance.chars_per_minute || 0} зн./мин`,
          },
          {
            label: "Точность",
            value: `${bestPerformance.accuracy || 0}%`,
          },
          {
            label: "Время",
            value: `${bestPerformance.time || 0} сек`,
          },
        ])}

        ${this.renderStatCard("📊", "Средние показатели", [
          {
            label: "Скорость",
            value: avgStats.chars_per_minute
              ? `${avgStats.chars_per_minute.toFixed(2)} зн./мин`
              : "Нет данных",
          },
          {
            label: "Точность",
            value: avgStats.accuracy
              ? `${avgStats.accuracy.toFixed(2)}%`
              : "Нет данных",
          },
          {
            label: "Среднее время",
            value: avgStats.time
              ? `${avgStats.time.toFixed(2)} сек`
              : "Нет данных",
          },
        ])}

        ${this.renderStatCard("⚖️", "Прогресс", [
          {
            label: "Скорость",
            value: `${speedProgressPercent.toFixed(1)}%`,
            extra: getProgressIndicator(speedProgressPercent),
          },
          {
            label: "Точность",
            value: `${accuracyProgressPercent.toFixed(1)}%`,
            extra: getProgressIndicator(accuracyProgressPercent),
          },
          {
            label: "Время",
            value: `${timeProgressPercent.toFixed(1)}%`,
            extra: getProgressIndicator(timeProgressPercent),
          },
        ])}
      </div>
    `;
  }

  renderChartsSection(data) {
    return `
      <div class="charts-section responsive-charts">
        <h3>Визуальная статистика</h3>
        <div class="charts-container">
          <div class="chart-wrapper">
            <canvas id="speed-chart" class="responsive-chart"></canvas>
            <div class="chart-title">Динамика скорости</div>
          </div>
          <div class="chart-wrapper">
            <canvas id="accuracy-chart" class="responsive-chart"></canvas>
            <div class="chart-title">Динамика точности</div>
          </div>
        </div>
      </div>
    `;
  }

  renderStatCard(icon, title, items) {
    return `
      <div class="stat-card">
      <div class="stat-card__icon">${icon}</div>
        <div class="stat-card__content">
          <h4 class="stat-card__title">${title}</h4>
          ${items
            .map(
              (item) => `
                <div class="stat-item">
                  <span class="stat-label">${item.label}:</span>
                  <span class="stat-value" ${item.extra ? `style="color: ${item.extra.color}"` : ""}>
                    ${item.value}
                    ${item.extra ? `<span class="progress-icon" title="${item.extra.text}">${item.extra.icon}</span>` : ""}
                  </span>
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
      <div class="no-results__icon">📝</div>
        <h3>Тесты еще не пройдены</h3>
        <p>Статистика появится после прохождения первых тестов</p>
      </div>
    `;
  }

  initCharts(tests) {
    this.dates = tests.map((test) => this.formatDate(test.created_at, true));
    const speeds = tests.map((test) => test.chars_per_minute);
    const accuracies = tests.map((test) => test.accuracy);

    const speedTrendLine = this.calculateTrendLine(speeds);
    const accuracyTrendLine = this.calculateTrendLine(accuracies);

    this.charts.speed = this.createChart(
      "speed-chart",
      [
        {
          data: speeds,
          borderColor: getComputedStyle(
            document.documentElement,
          ).getPropertyValue("--accent"),
          backgroundColor: "rgba(254, 128, 25, 0.1)",
          label: "Скорость (зн./мин)",
          pointBackgroundColor: getComputedStyle(
            document.documentElement,
          ).getPropertyValue("--accent"),
        },
        {
          data: speedTrendLine,
          borderColor: "rgba(254, 128, 25, 0.5)",
          label: "Тренд скорости",
          borderDash: [5, 5],
          pointRadius: 0,
        },
      ],
      "Скорость печати",
    );

    this.charts.accuracy = this.createChart(
      "accuracy-chart",
      [
        {
          data: accuracies,
          borderColor: getComputedStyle(
            document.documentElement,
          ).getPropertyValue("--success"),
          backgroundColor: "rgba(184, 187, 38, 0.1)",
          label: "Точность (%)",
          pointBackgroundColor: getComputedStyle(
            document.documentElement,
          ).getPropertyValue("--success"),
        },
        {
          data: accuracyTrendLine,
          borderColor: "rgba(184, 187, 38, 0.5)",
          label: "Тренд точности",
          borderDash: [5, 5],
          pointRadius: 0,
        },
      ],
      "Точность печати",
    );

    this.fixChartResponsiveness();
  }

  fixChartResponsiveness() {
    const observer = new ResizeObserver((entries) => {
      entries.forEach((entry) => {
        const chartWrapper = entry.target;
        const canvas = chartWrapper.querySelector("canvas");
        if (canvas && canvas.chart) {
          canvas.chart.resize();
        }
      });
    });

    document.querySelectorAll(".chart-wrapper").forEach((wrapper) => {
      observer.observe(wrapper);
    });
  }

  createChart(canvasId, datasets, title) {
    const gridColor =
      this.currentTheme === "dark"
        ? "rgba(255, 255, 255, 0.1)"
        : "rgba(0, 0, 0, 0.1)";
    const textColor =
      this.currentTheme === "dark"
        ? "rgba(255, 255, 255, 0.7)"
        : "rgba(0, 0, 0, 0.7)";

    return new Chart(document.getElementById(canvasId), {
      type: "line",
      data: {
        labels: this.dates,
        datasets: datasets.map((dataset) => ({
          data: dataset.data,
          borderColor: dataset.borderColor,
          backgroundColor: dataset.backgroundColor || "transparent",
          label: dataset.label,
          borderWidth: dataset.borderWidth || 3,
          tension: dataset.tension || 0.4,
          fill: dataset.fill !== undefined ? dataset.fill : true,
          pointBackgroundColor:
            dataset.pointBackgroundColor || dataset.borderColor,
          pointBorderColor: dataset.pointBorderColor || "#fff",
          pointBorderWidth: dataset.pointBorderWidth || 2,
          pointRadius:
            dataset.pointRadius !== undefined ? dataset.pointRadius : 5,
          pointHoverRadius: dataset.pointHoverRadius || 7,
          borderDash: dataset.borderDash,
        })),
      },
      options: this.getChartOptions(title, gridColor, textColor),
    });
  }

  calculateTrendLine(data) {
    if (data.length <= 1) return data;

    let sumX = 0,
      sumY = 0,
      sumXY = 0,
      sumXX = 0;

    data.forEach((y, x) => {
      sumX += x;
      sumY += y;
      sumXY += x * y;
      sumXX += x * x;
    });

    const n = data.length;
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    return data.map((_, i) => slope * i + intercept);
  }

  getChartOptions(title, gridColor, textColor) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: "bottom",
          labels: {
            color: textColor,
            font: {
              family: "JetBrains Mono, Fira Code, monospace",
              size: 12,
            },
          },
        },
        tooltip: {
          backgroundColor:
            this.currentTheme === "dark"
              ? "rgba(0, 0, 0, 0.9)"
              : "rgba(255, 255, 255, 0.9)",
          titleColor: this.currentTheme === "dark" ? "#fff" : "#000",
          bodyColor: this.currentTheme === "dark" ? "#fff" : "#000",
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
          beginAtZero: false,
          grid: {
            color: gridColor,
          },
          ticks: {
            color: textColor,
            font: {
              family: "JetBrains Mono, Fira Code, monospace",
            },
          },
          grace: "5%",
        },
        x: {
          grid: {
            color: gridColor,
          },
          ticks: {
            color: textColor,
            font: {
              family: "JetBrains Mono, Fira Code, monospace",
            },
            maxRotation: 45,
            minRotation: 45,
          },
        },
      },
      layout: {
        padding: {
          left: 10,
          right: 10,
          top: 10,
          bottom: 10,
        },
      },
    };
  }

  updateChartsTheme() {
    const gridColor =
      this.currentTheme === "dark"
        ? "rgba(255, 255, 255, 0.1)"
        : "rgba(0, 0, 0, 0.1)";
    const textColor =
      this.currentTheme === "dark"
        ? "rgba(255, 255, 255, 0.7)"
        : "rgba(0, 0, 0, 0.7)";

    Object.values(this.charts).forEach((chart) => {
      chart.options.scales.y.grid.color = gridColor;
      chart.options.scales.y.ticks.color = textColor;
      chart.options.scales.x.grid.color = gridColor;
      chart.options.scales.x.ticks.color = textColor;
      chart.options.plugins.legend.labels.color = textColor;
      chart.options.plugins.tooltip.backgroundColor =
        this.currentTheme === "dark"
          ? "rgba(0, 0, 0, 0.9)"
          : "rgba(255, 255, 255, 0.9)";
      chart.options.plugins.tooltip.titleColor =
        this.currentTheme === "dark" ? "#fff" : "#000";
      chart.options.plugins.tooltip.bodyColor =
        this.currentTheme === "dark" ? "#fff" : "#000";
      chart.update();
    });
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
        <button class="btn btn--primary" onclick="location.reload()">Попробовать снова</button>
      </div>
    `;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.userStatsInstance = new UserStatistics();
});

window.addEventListener("beforeunload", () => {
  if (window.userStatsInstance) {
    window.userStatsInstance.destroy();
  }
});
