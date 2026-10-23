// Load the pinned, local renderer only when a page actually contains math.
(() => {
  const assetBase = new URL("../assets/vendor/katex/", document.currentScript.src);
  let renderer;
  const loadScript = (name) => new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = new URL(name, assetBase).href;
    script.onload = resolve;
    script.onerror = () => { script.remove(); reject(new Error(`Cannot load ${name}`)); };
    document.head.append(script);
  });
  const loadRenderer = () => {
    if (!renderer) {
      const css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = new URL("katex.min.css", assetBase).href;
      document.head.append(css);
      renderer = loadScript("katex.min.js")
        .then(() => loadScript("auto-render.min.js"))
        .catch((error) => { renderer = null; throw error; });
    }
    return renderer;
  };
  document$.subscribe(async () => {
    const content = document.querySelector(".md-content__inner");
    if (!content || !content.querySelector(".arithmatex")) return;
    try {
      await loadRenderer();
      if (!content.isConnected) return;
      content.querySelectorAll(".arithmatex").forEach((element) => {
        if (element.dataset.mathReady) return;
        renderMathInElement(element, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\(", right: "\\)", display: false },
            { left: "\\[", right: "\\]", display: true },
          ],
          throwOnError: false,
        });
        element.dataset.mathReady = "true";
      });
    } catch (error) {
      console.error("Formula renderer could not be loaded", error);
    }
  });
})();
