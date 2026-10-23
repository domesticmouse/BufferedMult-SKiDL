/* ==========================================================================
   Eurorack Buffered Multiple — Shared Course Runtime (tutorial/assets/course.js)
   Centrally loads Prism.js (with keep-markup) & Mermaid.js (dark theme),
   and powers interactive fill-in-the-blank code exercises, retrieval quizzes,
   keyboard-accessible <pre> blocks, and the interactive component explorer.
   ========================================================================== */

(() => {
  const PRISM_BASE = "https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0";
  const MERMAID_URL =
    "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js";

  function loadStylesheet(href) {
    if (document.querySelector(`link[href="${href}"]`)) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.async = false;
      s.onload = () => resolve();
      s.onerror = (err) => reject(err);
      document.head.appendChild(s);
    });
  }

  async function initSyntaxAndDiagrams() {
    loadStylesheet(`${PRISM_BASE}/themes/prism-tomorrow.min.css`);
    try {
      window.Prism = window.Prism || {};
      window.Prism.manual = true;
      await loadScript(`${PRISM_BASE}/prism.min.js`);
      await loadScript(
        `${PRISM_BASE}/plugins/keep-markup/prism-keep-markup.min.js`
      );
      await loadScript(`${PRISM_BASE}/components/prism-python.min.js`);
      await loadScript(`${PRISM_BASE}/components/prism-bash.min.js`);
      await loadScript(`${PRISM_BASE}/components/prism-json.min.js`);
      await loadScript(`${PRISM_BASE}/components/prism-csv.min.js`);
      if (window.Prism && typeof window.Prism.highlightAll === "function") {
        window.Prism.highlightAll();
      }
    } catch (e) {
      console.warn("Prism CDN unavailable offline; falling back to plain <pre>.", e);
    }

    if (document.querySelector("pre.mermaid")) {
      try {
        await loadScript(MERMAID_URL);
        if (window.mermaid) {
          window.mermaid.initialize({
            startOnLoad: false,
            theme: "dark",
            securityLevel: "strict",
            fontFamily:
              '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
          });
          await window.mermaid.run({ querySelector: "pre.mermaid" });
        }
      } catch (e) {
        console.warn("Mermaid CDN unavailable offline; rendering raw diagram source.", e);
      }
    }
  }

  function enhanceCodeBlocks() {
    document.querySelectorAll("pre").forEach((pre) => {
      if (!pre.classList.contains("mermaid") && !pre.hasAttribute("tabindex")) {
        pre.setAttribute("tabindex", "0");
      }
    });

    document.querySelectorAll(".copy-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const figure = btn.closest(".code-figure");
        const codeEl = figure ? figure.querySelector("pre code") : null;
        if (!codeEl) return;
        const clone = codeEl.cloneNode(true);
        clone.querySelectorAll("input.code-blank").forEach((inp) => {
          const val = inp.value.trim() || inp.getAttribute("data-answer") || "";
          inp.replaceWith(document.createTextNode(val.split("|")[0]));
        });
        try {
          await navigator.clipboard.writeText(clone.textContent || "");
          const orig = btn.textContent;
          btn.textContent = "Copied!";
          setTimeout(() => {
            btn.textContent = orig;
          }, 1600);
        } catch {
          btn.textContent = "Copy failed";
        }
      });
    });
  }

  function initCodeExercises() {
    document.querySelectorAll(".exercise-box").forEach((box) => {
      const checkBtn = box.querySelector('[data-action="check"]');
      const hintBtn = box.querySelector('[data-action="hint"]');
      const resetBtn = box.querySelector('[data-action="reset"]');
      const feedback = box.querySelector(".feedback-msg");

      const getInputs = () => Array.from(box.querySelectorAll("input.code-blank"));

      const setFeedback = (ok, text) => {
        if (!feedback) return;
        feedback.textContent = text;
        feedback.classList.add("is-visible");
        feedback.classList.toggle("is-ok", ok);
        feedback.classList.toggle("is-err", !ok);
      };

      if (checkBtn) {
        checkBtn.addEventListener("click", () => {
          const inputs = getInputs();
          let correctCount = 0;
          inputs.forEach((inp) => {
            const rawExpected = (inp.getAttribute("data-answer") || "")
              .split("|")
              .map((s) => s.trim());
            const actual = inp.value.trim();
            const isMatch = rawExpected.includes(actual);
            inp.classList.toggle("is-correct", isMatch);
            inp.classList.toggle("is-incorrect", !isMatch);
            inp.setAttribute("aria-invalid", isMatch ? "false" : "true");
            if (isMatch) correctCount += 1;
          });

          if (correctCount === inputs.length) {
            setFeedback(
              true,
              `✓ All ${inputs.length}/${inputs.length} blanks correct! Ready to run in your terminal.`
            );
          } else {
            setFeedback(
              false,
              `✗ ${correctCount}/${inputs.length} blanks match. Review the highlighted inputs or click Show Hint.`
            );
          }
        });
      }

      if (hintBtn) {
        hintBtn.addEventListener("click", () => {
          const inputs = getInputs();
          const firstWrong = inputs.find((inp) => {
            const rawExpected = (inp.getAttribute("data-answer") || "")
              .split("|")
              .map((s) => s.trim());
            return !rawExpected.includes(inp.value.trim());
          });
          if (!firstWrong) {
            setFeedback(true, "✓ Every blank is already filled in correctly!");
            return;
          }
          const canonical = (firstWrong.getAttribute("data-answer") || "").split("|")[0];
          const hintNote =
            firstWrong.getAttribute("data-hint") ||
            `Expected value starts with "${canonical.slice(0, 2)}…" (${canonical.length} chars).`;
          setFeedback(false, `Hint: ${hintNote}`);
          firstWrong.focus();
        });
      }

      if (resetBtn) {
        resetBtn.addEventListener("click", () => {
          getInputs().forEach((inp) => {
            inp.value = "";
            inp.classList.remove("is-correct", "is-incorrect");
            inp.removeAttribute("aria-invalid");
          });
          if (feedback) {
            feedback.textContent = "";
            feedback.classList.remove("is-visible", "is-ok", "is-err");
          }
        });
      }
    });
  }

  function initQuizzes() {
    document.querySelectorAll(".quiz-card").forEach((card) => {
      const options = Array.from(card.querySelectorAll(".quiz-option"));
      const feedback = card.querySelector(".feedback-msg");

      options.forEach((btn) => {
        btn.addEventListener("click", () => {
          const isCorrect = btn.getAttribute("data-correct") === "true";
          const explanation = btn.getAttribute("data-explain") || "";

          options.forEach((other) => {
            other.classList.remove("is-correct", "is-wrong");
            other.setAttribute("aria-pressed", "false");
          });

          btn.classList.add(isCorrect ? "is-correct" : "is-wrong");
          btn.setAttribute("aria-pressed", "true");

          if (feedback) {
            feedback.textContent =
              (isCorrect ? "✓ Correct: " : "✗ Not quite: ") + explanation;
            feedback.classList.add("is-visible");
            feedback.classList.toggle("is-ok", isCorrect);
            feedback.classList.toggle("is-err", !isCorrect);
          }
        });
      });
    });
  }

  function initComponentExplorer() {
    const root = document.getElementById("part-explorer");
    if (!root) return;
    const searchInput = root.querySelector("#explorer-filter");
    const classFilter = root.querySelector("#explorer-class");
    const rows = Array.from(root.querySelectorAll("tbody tr[data-part]"));
    const countEl = root.querySelector("#explorer-count");

    function updateFilter() {
      const q = (searchInput ? searchInput.value : "").trim().toLowerCase();
      const cls = classFilter ? classFilter.value : "all";
      let visible = 0;

      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        const rowClass = row.getAttribute("data-class") || "";
        const matchQ = !q || text.includes(q);
        const matchCls = cls === "all" || rowClass === cls;
        const show = matchQ && matchCls;
        row.hidden = !show;
        if (show) visible += 1;
      });

      if (countEl) {
        countEl.textContent = `Showing ${visible} of ${rows.length} components`;
      }
    }

    if (searchInput) searchInput.addEventListener("input", updateFilter);
    if (classFilter) classFilter.addEventListener("change", updateFilter);
    updateFilter();
  }

  document.addEventListener("DOMContentLoaded", () => {
    enhanceCodeBlocks();
    initCodeExercises();
    initQuizzes();
    initComponentExplorer();
    initSyntaxAndDiagrams();
  });
})();
