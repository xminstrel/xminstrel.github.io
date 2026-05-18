function collapsePrimaryNavigation() {
  document
    .querySelectorAll(".md-sidebar--primary .md-nav__toggle[id^='__nav_']")
    .forEach(function (toggle) {
      toggle.checked = false;
      toggle.classList.remove("md-toggle--indeterminate");

      var nav = toggle.parentElement
        ? toggle.parentElement.querySelector(":scope > .md-nav")
        : null;

      if (nav) {
        nav.setAttribute("aria-expanded", "false");
      }
    });
}

if (typeof document$ !== "undefined") {
  document$.subscribe(collapsePrimaryNavigation);
} else if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", collapsePrimaryNavigation);
} else {
  collapsePrimaryNavigation();
}
