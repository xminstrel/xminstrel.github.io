document$.subscribe(() => {
  if (window.__tocFoldObserver) {
    window.__tocFoldObserver.disconnect();
    window.__tocFoldObserver = null;
  }

  const toc = document.querySelector(".md-sidebar--secondary .md-nav--secondary");
  if (!toc || toc.dataset.tocFoldReady === "true") {
    return;
  }

  const links = toc.querySelectorAll(".md-nav__link");
  if (links.length < 8) {
    return;
  }

  const branches = Array.from(toc.querySelectorAll(".md-nav__item"))
    .map((item, index) => ({
      item,
      index,
      link: item.querySelector(":scope > .md-nav__link"),
      nested: item.querySelector(":scope > .md-nav"),
    }))
    .filter(({ link, nested }) => link && nested);

  if (!branches.length) {
    return;
  }

  toc.dataset.tocFoldReady = "true";

  const setBranchState = (branch, collapsed) => {
    const { item, link, nested, index } = branch;
    let button = item.querySelector(":scope > .toc-fold__toggle");

    if (!nested.id) {
      nested.id = `toc-fold-section-${index + 1}`;
    }

    if (!button) {
      button = document.createElement("button");
      button.className = "toc-fold__toggle";
      button.type = "button";
      button.setAttribute("aria-controls", nested.id);
      button.innerHTML = '<span aria-hidden="true">⌄</span>';
      nested.before(button);

      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        setBranchState(branch, !item.classList.contains("toc-fold__branch--collapsed"));
        updateAllButton();
      });

      link.addEventListener("click", () => {
        setBranchState(branch, false);
        branches
          .filter(({ item: parent }) => parent !== item && parent.contains(item))
          .forEach((parent) => setBranchState(parent, false));
        updateAllButton();
      });
    }

    item.classList.add("toc-fold__branch");
    item.classList.toggle("toc-fold__branch--collapsed", collapsed);
    button.setAttribute("aria-expanded", String(!collapsed));
    button.setAttribute(
      "aria-label",
      `${collapsed ? "展开" : "收起"}“${link.textContent.trim()}”子目录`,
    );
    button.title = button.getAttribute("aria-label");
  };

  const controls = document.createElement("div");
  controls.className = "toc-fold__controls";

  const allButton = document.createElement("button");
  allButton.className = "toc-fold__all";
  allButton.type = "button";
  controls.append(allButton);

  const updateAllButton = () => {
    const hasCollapsedBranch = branches.some(({ item }) =>
      item.classList.contains("toc-fold__branch--collapsed"),
    );
    allButton.textContent = hasCollapsedBranch ? "展开全部" : "收起全部";
    allButton.setAttribute("aria-expanded", String(!hasCollapsedBranch));
  };

  allButton.addEventListener("click", () => {
    const shouldExpand = branches.some(({ item }) =>
      item.classList.contains("toc-fold__branch--collapsed"),
    );
    branches.forEach((branch) => setBranchState(branch, !shouldExpand));
    updateAllButton();
  });

  const title = toc.querySelector(":scope > .md-nav__title");
  if (title) {
    title.after(controls);
  } else {
    toc.prepend(controls);
  }

  const activeLink = toc.querySelector(".md-nav__link--active");
  branches.forEach((branch) => {
    setBranchState(branch, !activeLink || !branch.item.contains(activeLink));
  });
  updateAllButton();

  window.__tocFoldObserver = new MutationObserver((mutations) => {
    const activeLinkChanged = mutations.some(
      ({ target }) => target instanceof Element && target.matches(".md-nav__link"),
    );
    if (!activeLinkChanged) {
      return;
    }

    const currentLink = toc.querySelector(".md-nav__link--active");
    if (!currentLink) {
      return;
    }

    branches
      .filter(({ item }) => item.contains(currentLink))
      .forEach((branch) => setBranchState(branch, false));
    updateAllButton();
  });
  window.__tocFoldObserver.observe(toc, {
    attributes: true,
    attributeFilter: ["class"],
    subtree: true,
  });
});
