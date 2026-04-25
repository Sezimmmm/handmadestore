document.addEventListener("DOMContentLoaded", function () {
  function syncAddToCartLink() {
    var a = document.getElementById("add-to-cart");
    if (!a) return;
    var base = a.getAttribute("data-cart-add");
    if (!base) return;
    var next = a.getAttribute("data-next") || "";
    var params = new URLSearchParams();
    if (next) params.set("next", next);
    var sel = document.querySelector(".pd-variant.sel");
    if (sel) {
      var id = sel.getAttribute("data-variant-id");
      if (id) params.set("variant", id);
    }
    var q = params.toString();
    a.href = q ? base + "?" + q : base;
  }

  syncAddToCartLink();

  document.addEventListener("click", function (event) {
    var btn = event.target.closest(".pd-variant");
    if (!btn) return;
    var url = btn.getAttribute("data-image-url");
    if (url) {
      var img = document.getElementById("pd-main-img");
      if (img) {
        img.src = url;
        var alt = btn.getAttribute("data-alt");
        if (alt) img.alt = alt;
      }
    }
    document.querySelectorAll(".pd-variant").forEach(function (b) {
      b.classList.remove("sel");
      b.setAttribute("aria-pressed", "false");
    });
    btn.classList.add("sel");
    btn.setAttribute("aria-pressed", "true");
    var label = document.getElementById("pd-color-label");
    if (label) {
      var name = btn.getAttribute("data-color-name");
      if (name) label.textContent = name;
    }
    syncAddToCartLink();
  });
});
