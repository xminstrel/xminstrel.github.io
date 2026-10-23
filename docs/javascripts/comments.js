// Rebind comments after instant navigation and defer the external embed until needed.
(() => {
  let observer;
  const theme = () => document.body.dataset.mdColorScheme === "slate" ? "transparent_dark" : "light";
  document$.subscribe(() => {
    observer?.disconnect();
    const container = document.querySelector("[data-comments]");
    if (!container) return;
    const mount = () => {
      if (!container.isConnected || container.dataset.ready) return;
      container.dataset.ready = "true";
      const script = document.createElement("script");
      script.src = "https://giscus.app/client.js";
      const settings = {
        repo: "xminstrel/xminstrel.github.io", "repo-id": "R_kgDOQ7oY9A",
        category: "Announcements", "category-id": "DIC_kwDOQ7oY9M4C1XRo",
        mapping: "pathname", strict: "0", "reactions-enabled": "1",
        "emit-metadata": "0", "input-position": "bottom", theme: theme(), lang: "zh-CN",
      };
      Object.entries(settings).forEach(([key, value]) => script.setAttribute(`data-${key}`, value));
      script.crossOrigin = "anonymous";
      script.async = true;
      container.append(script);
    };
    const pageObserver = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) { pageObserver.disconnect(); mount(); }
    }, { rootMargin: "200px" });
    observer = pageObserver;
    pageObserver.observe(container);
  });
  new MutationObserver(() => {
    document.querySelector(".giscus-frame")?.contentWindow.postMessage(
      { giscus: { setConfig: { theme: theme() } } }, "https://giscus.app",
    );
  }).observe(document.body, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
})();
