function initHomeExperience() {
  const shell = document.querySelector("[data-home-shell]");
  if (!shell || shell.dataset.homeReady === "true") {
    return;
  }

  shell.dataset.homeReady = "true";

  const now = new Date();
  const hour = now.getHours();
  const greeting =
    hour < 6
      ? "夜深了，早点休息吧"
      : hour < 11
        ? "早上好，睡个回笼觉吧"
        : hour < 14
          ? "中午好，今天吃什么呢"
          : hour < 18
            ? "下午好，晚上吃什么"
            : "晚上好，记得早点睡觉哦";

  const greetingTarget = shell.querySelector("[data-home-greeting]");
  if (greetingTarget) {
    greetingTarget.textContent = greeting;
  }

  const dateTarget = shell.querySelector("[data-home-date]");
  if (dateTarget) {
    dateTarget.textContent = new Intl.DateTimeFormat("zh-CN", {
      month: "long",
      day: "numeric",
      weekday: "long",
    }).format(now);
  }

  const searchButton = shell.querySelector("[data-home-search]");
  if (searchButton) {
    searchButton.addEventListener("click", () => {
      const searchToggle = document.querySelector("input[data-md-toggle='search']");
      if (!searchToggle) {
        return;
      }

      searchToggle.checked = true;
      searchToggle.dispatchEvent(new Event("change", { bubbles: true }));
      window.setTimeout(() => {
        const searchInput = document.querySelector(".md-search__input");
        if (searchInput) {
          searchInput.focus();
        }
      }, 80);
    });
  }

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  const hero = shell.querySelector("[data-home-hero]");

  const quotes = [
    { text: "二泉映月，他才不管红与不红。", source: "个人碎碎念" },
    { text: "人生不是由别人赋予的，而是由自己选择的。", source: "《被讨厌的勇气》" },
    { text: "决定自己人生的是活在“此时此刻”的你自己。", source: "《被讨厌的勇气》" },
    { text: "健全的自卑感，不是来自与别人的比较。", source: "《被讨厌的勇气》" },
    { text: "改变要承担代价和风险，但原地不动也有代价。", source: "读书时想到的" },
    { text: "太多对确定性的追求，有时也会阻碍改变。", source: "读书时想到的" },
    { text: "这里记录课程笔记和生活片段，写着玩玩啦。", source: "个人碎碎念" },
  ];
  const quoteButton = shell.querySelector("[data-home-quote-toggle]");
  const quoteText = shell.querySelector("[data-home-quote]");
  const quoteSource = shell.querySelector("[data-home-quote-source]");
  const quoteBox = shell.querySelector(".home-quote");
  let quoteIndex = 0;

  if (quoteButton && quoteText && quoteSource && quoteBox) {
    quoteButton.addEventListener("click", () => {
      const nextCandidate = Math.floor(Math.random() * (quotes.length - 1));
      quoteIndex = nextCandidate >= quoteIndex ? nextCandidate + 1 : nextCandidate;
      quoteText.textContent = quotes[quoteIndex].text;
      quoteSource.textContent = quotes[quoteIndex].source;

      if (!reducedMotion) {
        quoteBox.classList.remove("is-refreshed");
        window.requestAnimationFrame(() => quoteBox.classList.add("is-refreshed"));
      }
    });

    quoteBox.addEventListener("animationend", () => {
      quoteBox.classList.remove("is-refreshed");
    });
  }

  if (hero && finePointer && !reducedMotion) {
    hero.addEventListener("pointermove", (event) => {
      const bounds = hero.getBoundingClientRect();
      hero.style.setProperty("--pointer-x", `${event.clientX - bounds.left}px`);
      hero.style.setProperty("--pointer-y", `${event.clientY - bounds.top}px`);
    });
  }

  if (!reducedMotion) {
    const particleColors = [
      "var(--home-sage)",
      "var(--home-coral)",
      "var(--home-sun)",
      "var(--home-lilac)",
    ];

    shell.addEventListener("click", (event) => {
      const interactiveTarget =
        event.target instanceof Element &&
        event.target.closest("a, button, input, select, textarea, [role='button']");

      if (event.detail === 0 || interactiveTarget) {
        return;
      }

      const particleCount = finePointer ? 9 : 7;
      for (let index = 0; index < particleCount; index += 1) {
        const particle = document.createElement("span");
        const angle = (Math.PI * 2 * index) / particleCount + (Math.random() - 0.5) * 0.38;
        const distance = 28 + Math.random() * (finePointer ? 38 : 26);

        particle.className = "home-click-particle";
        if (index % 4 === 0) {
          particle.classList.add("home-click-particle--ring");
        }
        particle.style.left = `${event.clientX}px`;
        particle.style.top = `${event.clientY}px`;
        particle.style.setProperty("--particle-x", `${Math.cos(angle) * distance}px`);
        particle.style.setProperty("--particle-y", `${Math.sin(angle) * distance}px`);
        particle.style.setProperty("--particle-rotate", `${Math.round(Math.random() * 180)}deg`);
        particle.style.setProperty("--particle-size", `${0.28 + Math.random() * 0.22}rem`);
        particle.style.setProperty(
          "--particle-color",
          particleColors[index % particleColors.length],
        );

        document.body.append(particle);
        particle.addEventListener("animationend", () => particle.remove(), { once: true });
      }
    });
  }

  const revealItems = shell.querySelectorAll(".home-reveal");
  if (reducedMotion || !("IntersectionObserver" in window)) {
    revealItems.forEach((item) => item.classList.add("is-visible"));
    return;
  }

  shell.classList.add("is-enhanced");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    { rootMargin: "0px 0px -8%", threshold: 0.08 },
  );
  revealItems.forEach((item) => observer.observe(item));
}

if (typeof document$ !== "undefined") {
  document$.subscribe(initHomeExperience);
} else if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initHomeExperience);
} else {
  initHomeExperience();
}
