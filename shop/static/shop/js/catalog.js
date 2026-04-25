document.addEventListener("click", (event) => {
  const colorDot = event.target.closest(".product-colors .pc-dot");
  if (colorDot) {
    const productColors = colorDot.closest(".product-colors");
    if (!productColors) return;
    productColors.querySelectorAll(".pc-dot").forEach((dot) => dot.classList.remove("sel"));
    colorDot.classList.add("sel");
  }
});

document.addEventListener("change", (event) => {
  const categoryInput = event.target.closest('#catalogFilterForm input[name="category"]');
  if (categoryInput) {
    const form = document.querySelector("#catalogFilterForm");
    if (form) form.requestSubmit();
  }

  const sortSelect = event.target.closest('#catalogSortForm select[name="sort"]');
  if (sortSelect) {
    const form = document.querySelector("#catalogSortForm");
    if (form) form.requestSubmit();
  }
});
