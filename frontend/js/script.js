const textDisplay = document.getElementById("text-display");
const textInput = document.getElementById("text-input");
const resetBtn = document.getElementById("reset-btn");
const speedElement = document.getElementById("speed");
const accuracyElement = document.getElementById("accuracy");
const timerElement = document.getElementById("timer");
const resultElement = document.getElementById("result");
const resultSpeed = document.getElementById("result-speed");
const resultAccuracy = document.getElementById("result-accuracy");
const resultTime = document.getElementById("result-time");
const themeBtn = document.getElementById("theme-btn");
const themeIcon = document.querySelector(".theme-icon");
const progressBar = document.getElementById("progress-bar");
const progressContainer = document.querySelector(".progress-container");
const languageSwitch = document.querySelector(".language-switch");
const languageButtons = document.querySelectorAll(".switch-btn");
const languageHint = document.querySelector(".language-hint");
const langName = document.querySelector(".lang-name");

let currentText = "";
let timer = null;
let startTime = null;
let totalChars = 0;
let correctChars = 0;
let isActive = false;
let isCompleted = false;
let currentLanguage = localStorage.getItem("selectedLanguage") || "ru";
let currentDifficulty = localStorage.getItem("selectedDifficulty") || "easy";
let lastAccuracyUpdate = 0;

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--accent);
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    z-index: 1000;
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.3s ease;
  `;

  document.body.appendChild(toast);

  requestAnimationFrame(() => {
    toast.style.opacity = "1";
    toast.style.transform = "translateX(0)";
  });

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

async function fetchTextFromBackend(language, difficulty) {
  try {
    const response = await fetch(
      `/api/text?lang=${language}&difficulty=${difficulty}`,
    );

    if (!response.ok) {
      throw new Error("Не удалось получить текст");
    }

    const data = await response.json();
    return data.text;
  } catch (error) {
    console.error("Ошибка загрузки текста:", error);
    showToast("Ошибка загрузки текста. Используем локальную версию", "error");
    const texts = textSamples[language][difficulty];
    const randomIndex = Math.floor(Math.random() * texts.length);
    return texts[randomIndex];
  }
}

async function init() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }

  await selectRandomText(currentLanguage, currentDifficulty);

  speedElement.textContent = "0";
  accuracyElement.textContent = "100%";
  timerElement.textContent = "0:00";

  textInput.value = "";
  textInput.disabled = false;

  totalChars = 0;
  correctChars = 0;
  isActive = false;
  isCompleted = false;

  resultElement.style.display = "none";

  progressContainer.classList.remove("visible");
  progressBar.style.width = "0%";

  textInput.focus();
}

async function selectRandomText(language = "ru", difficulty = "easy") {
  try {
    textDisplay.classList.add("changing");
    currentText = await fetchTextFromBackend(language, difficulty);
    renderText();
    updateLanguageHint(language);
  } catch (error) {
    console.error("Ошибка загрузки текста:", error);
    showToast("Ошибка загрузки текста", "error");
    const texts = textSamples[language][difficulty];
    const randomIndex = Math.floor(Math.random() * texts.length);
    currentText = texts[randomIndex];
    renderText();
    updateLanguageHint(language);
  } finally {
    textDisplay.classList.remove("changing");
  }
}

function updateLanguageHint(language) {
  const languageNames = {
    ru: "Русский",
    en: "Английский",
  };
  langName.textContent = languageNames[language];
}

function renderText() {
  const fragment = document.createDocumentFragment();

  currentText.split("").forEach((char, index) => {
    const span = document.createElement("span");
    span.className = "char";
    span.textContent = char;

    if (index === 0) {
      span.classList.add("current-char");
    }

    fragment.appendChild(span);
  });

  textDisplay.innerHTML = "";
  textDisplay.appendChild(fragment);
  textInput.setAttribute("maxlength", currentText.length);
}

function updateProgressBar(currentIndex, totalLength) {
  const progress = (currentIndex / totalLength) * 100;
  progressBar.style.width = `${progress}%`;

  if (currentIndex > 0 && !progressContainer.classList.contains("visible")) {
    progressContainer.classList.add("visible");
  }
}

function startTest() {
  if (isActive) return;

  isActive = true;
  startTime = new Date();
  timer = setInterval(updateTimer, 1000);
}

function resetTest() {
  clearInterval(timer);
  timer = null;
  init();
}

function updateTimer() {
  const currentTime = new Date();
  const elapsedTime = Math.floor((currentTime - startTime) / 1000);
  const minutes = Math.floor(elapsedTime / 60);
  const seconds = elapsedTime % 60;
  timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, "0")}`;

  if (elapsedTime > 0) {
    const speed = Math.round((totalChars / elapsedTime) * 60);
    speedElement.textContent = speed;
  }
}

function updateAccuracy() {
  const accuracy =
    totalChars > 0 ? Math.round((correctChars / totalChars) * 100) : 100;
  accuracyElement.textContent = `${accuracy}%`;
  return accuracy;
}

async function finishTest() {
  if (isCompleted) return;

  isActive = false;
  isCompleted = true;
  clearInterval(timer);
  timer = null;
  textInput.disabled = true;

  const elapsedTime = Math.floor((new Date() - startTime) / 1000);

  try {
    const testResultData = {
      user_id: localStorage.getItem("user_id") || "",
      chars_per_minute: parseFloat(speedElement.textContent) || 0.0,
      accuracy: parseFloat(accuracyElement.textContent) || 0.0,
      time_seconds: elapsedTime,
      language: currentLanguage,
      difficulty: currentDifficulty,
    };

    console.log("Отправляемые данные:", testResultData);

    const response = await fetch("/api/test-result", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(testResultData),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Ошибка сервера: ${errorText}`);
    }

    const result = await response.json();

    if (result.user_id) {
      localStorage.setItem("user_id", result.user_id);
    }

    showToast("Результат сохранен!", "success");
  } catch (error) {
    console.error("Ошибка сохранения результата:", error);
    showToast("Ошибка сохранения результата", "error");
  }

  const minutes = Math.floor(elapsedTime / 60);
  const seconds = elapsedTime % 60;

  resultSpeed.textContent = speedElement.textContent;
  resultAccuracy.textContent = accuracyElement.textContent;
  resultTime.textContent = `${minutes}:${seconds.toString().padStart(2, "0")}`;

  resultElement.style.display = "block";
}

function handleInput() {
  if (isCompleted) return;

  let inputText = textInput.value;
  if (inputText.length > currentText.length) {
    inputText = inputText.slice(0, currentText.length);
    textInput.value = inputText;
  }

  const newLength = inputText.length;
  totalChars = newLength;

  if (!isActive && totalChars > 0) {
    startTest();
  }

  updateProgressBar(totalChars, currentText.length);

  let newCorrectChars = 0;
  const chars = textDisplay.querySelectorAll(".char");

  for (let i = 0; i < chars.length; i++) {
    chars[i].className = "char";

    if (i < newLength) {
      if (inputText[i] === currentText[i]) {
        chars[i].classList.add("correct");
        newCorrectChars++;
      } else {
        chars[i].classList.add("incorrect");
      }
    } else if (i === newLength) {
      chars[i].classList.add("current-char");
    }
  }

  correctChars = newCorrectChars;

  const now = Date.now();
  if (now - lastAccuracyUpdate > 300) {
    updateAccuracy();
    lastAccuracyUpdate = now;
  }

  if (isActive) {
    const currentTime = new Date();
    const elapsedTime = (currentTime - startTime) / 1000;
    if (elapsedTime > 0) {
      const speed = Math.round((totalChars / elapsedTime) * 60);
      speedElement.textContent = speed;
    }
  }

  if (newLength >= currentText.length) {
    finishTest();
  }
}

function switchLanguage(language) {
  if (language === currentLanguage) return;

  currentLanguage = language;
  localStorage.setItem("selectedLanguage", language);

  languageButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === language);
  });

  languageSwitch.setAttribute("data-current-lang", language);
  resetTest();
}

function toggleTheme() {
  const currentTheme = document.body.getAttribute("data-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  document.body.setAttribute("data-theme", newTheme);
  themeIcon.textContent = newTheme === "dark" ? "🌙" : "☀️";
  localStorage.setItem("theme", newTheme);
}

function preventTextCopying() {
  textDisplay.style.userSelect = "none";
  textDisplay.style.webkitUserSelect = "none";
  textDisplay.style.mozUserSelect = "none";
  textDisplay.style.msUserSelect = "none";

  textDisplay.addEventListener("contextmenu", (e) => {
    e.preventDefault();
  });

  textDisplay.addEventListener("dragstart", (e) => {
    e.preventDefault();
  });

  textDisplay.addEventListener("keydown", (e) => {
    if (
      e.ctrlKey &&
      (e.key === "c" || e.key === "C" || e.key === "a" || e.key === "A")
    ) {
      e.preventDefault();
    }
  });
}

function loadSavedSettings() {
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.body.setAttribute("data-theme", savedTheme);
  themeIcon.textContent = savedTheme === "dark" ? "🌙" : "☀️";

  const savedLanguage = localStorage.getItem("selectedLanguage") || "ru";
  currentLanguage = savedLanguage;
  languageSwitch.setAttribute("data-current-lang", savedLanguage);
  languageButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === savedLanguage);
  });

  const savedDifficulty = localStorage.getItem("selectedDifficulty") || "easy";
  currentDifficulty = savedDifficulty;
  document.querySelectorAll(".difficulty-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.difficulty === savedDifficulty);
  });
}

function cleanup() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadSavedSettings();
  init();
  preventTextCopying();
});

window.addEventListener("beforeunload", cleanup);
window.addEventListener("pagehide", cleanup);

const profileBtn = document.getElementById("profile-btn");

if (profileBtn) {
  profileBtn.addEventListener("click", function () {
    const userId = localStorage.getItem("user_id") || "anonymous";
    window.location.href = `/statistics/${userId}`;
  });
}

resetBtn.addEventListener("click", resetTest);
textInput.addEventListener("input", debounce(handleInput, 50));
themeBtn.addEventListener("click", toggleTheme);

document.querySelectorAll(".difficulty-btn").forEach((btn) => {
  btn.addEventListener("click", function () {
    document.querySelectorAll(".difficulty-btn").forEach((b) => {
      b.classList.remove("active");
    });

    this.classList.add("active");
    currentDifficulty = this.dataset.difficulty;
    localStorage.setItem("selectedDifficulty", currentDifficulty);
    resetTest();
  });
});

languageButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    switchLanguage(btn.dataset.lang);
  });
});

document.querySelector(".switch-track").addEventListener("click", () => {
  const newLang = currentLanguage === "ru" ? "en" : "ru";
  switchLanguage(newLang);
});

textInput.addEventListener("paste", (e) => {
  e.preventDefault();
});
