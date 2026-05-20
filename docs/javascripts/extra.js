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

function formatRepoNumber(value) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "";
  }

  if (value >= 1000) {
    return (value / 1000).toFixed(value >= 10000 ? 0 : 1).replace(/\.0$/, "") + "k";
  }

  return String(value);
}

function renderRepoFacts(data) {
  document
    .querySelectorAll(".md-source[data-md-component='source']")
    .forEach(function (source) {
      if (source.querySelector(".md-source__facts")) {
        return;
      }

      var repository = source.querySelector(".md-source__repository");
      if (!repository) {
        return;
      }

      var facts = document.createElement("ul");
      facts.className = "md-source__facts";

      var stars = document.createElement("li");
      stars.className = "md-source__fact md-source__fact--stars";
      stars.textContent = formatRepoNumber(data.stars) || "Star";
      stars.title = "GitHub stars";
      facts.appendChild(stars);

      if (typeof data.forks === "number") {
        var forks = document.createElement("li");
        forks.className = "md-source__fact md-source__fact--forks";
        forks.textContent = formatRepoNumber(data.forks);
        forks.title = "GitHub forks";
        facts.appendChild(forks);
      }

      repository.appendChild(facts);
    });
}

function hasMissingRepoFacts() {
  return Array.prototype.some.call(
    document.querySelectorAll(".md-source[data-md-component='source']"),
    function (source) {
      return !source.querySelector(".md-source__facts");
    }
  );
}

function patchGitHubSourceFacts() {
  var cacheKey = "xminblog.github_source_facts";
  var cached = null;

  try {
    cached = JSON.parse(localStorage.getItem(cacheKey) || "null");
  } catch (error) {
    cached = null;
  }

  window.setTimeout(function () {
    if (!hasMissingRepoFacts()) {
      return;
    }

    if (cached && typeof cached.stars === "number") {
      renderRepoFacts(cached);
    }

    fetch("https://api.github.com/repos/xminstrel/xminstrel.github.io", {
      headers: { Accept: "application/vnd.github+json" },
      cache: "no-store",
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("GitHub API returned " + response.status);
        }
        return response.json();
      })
      .then(function (repo) {
        var data = {
          stars: repo.stargazers_count,
          forks: repo.forks_count,
          updatedAt: Date.now(),
        };
        try {
          localStorage.setItem(cacheKey, JSON.stringify(data));
        } catch (error) {
          // Ignore storage failures and still render the freshly fetched value.
        }

        document.querySelectorAll(".md-source__facts").forEach(function (existing) {
          existing.remove();
        });
        renderRepoFacts(data);
      })
      .catch(function () {
        if (hasMissingRepoFacts()) {
          renderRepoFacts({ stars: null });
        }
      });
  }, 1200);
}

if (typeof document$ !== "undefined") {
  document$.subscribe(function () {
    collapsePrimaryNavigation();
    patchGitHubSourceFacts();
  });
} else if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", function () {
    collapsePrimaryNavigation();
    patchGitHubSourceFacts();
  });
} else {
  collapsePrimaryNavigation();
  patchGitHubSourceFacts();
}
