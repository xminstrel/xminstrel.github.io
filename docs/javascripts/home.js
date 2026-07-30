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
      ? "夜深了，欢迎来知识花园散步"
      : hour < 11
        ? "早上好，来翻一页新笔记"
        : hour < 14
          ? "中午好，随便逛逛吧"
          : hour < 18
            ? "下午好，来捡一片知识碎片"
            : "晚上好，欢迎来知识花园散步";

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
      if (event.detail === 0) {
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
