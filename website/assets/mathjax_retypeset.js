// Re-trigger MathJax typesetting after Dash/React re-renders on page navigation.
// Uses a MutationObserver on the Dash page container so any content update causes
// a debounced typesetPromise() call — no Dash callbacks or layout changes needed.
(function () {
    function retypeset() {
        if (window.MathJax && window.MathJax.typesetPromise) {
            clearTimeout(window._mjRetypesetTimer);
            window._mjRetypesetTimer = setTimeout(function () {
                MathJax.typesetPromise();
            }, 80);
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        var target = document.body;
        var observer = new MutationObserver(retypeset);
        observer.observe(target, { childList: true, subtree: true });
    });
})();
