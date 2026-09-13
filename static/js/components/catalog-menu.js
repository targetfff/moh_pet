(function () {
  const config = document.getElementById("catalog-menu-config");
  const menuToggle = document.getElementById("catalog-menu-toggle");
  const backdrop = document.getElementById("catalog-menu-backdrop");
  const rootDrawer = document.getElementById("catalog-root-drawer");
  const rootList = document.getElementById("catalog-root-list");
  const detailDrawer = document.getElementById("catalog-detail-drawer");
  const detailBack = document.getElementById("catalog-detail-back");
  const detailParentTitle = document.getElementById("catalog-detail-parent-title");
  const detailTitle = document.getElementById("catalog-detail-title");
  const detailList = document.getElementById("catalog-detail-list");

  if (
    !config || !menuToggle || !backdrop || !rootDrawer || !rootList
    || !detailDrawer || !detailBack || !detailParentTitle
    || !detailTitle || !detailList
  ) {
    return;
  }

  const indexUrl = config.dataset.indexUrl;
  const treeUrl = config.dataset.treeUrl;

  let categoryTree = null;
  let categoryTreePromise = null;
  let categoryPath = [];
  let rootsRendered = false;

  function menuIsOpen() {
    return document.body.classList.contains("catalog-menu-open");
  }

  function isInsideMenu(target) {
    return rootDrawer.contains(target) || detailDrawer.contains(target);
  }

  function preventBackgroundScroll(event) {
    if (!menuIsOpen()) {
      return;
    }

    if (isInsideMenu(event.target)) {
      return;
    }

    event.preventDefault();
  }

  window.addEventListener(
    "wheel",
    preventBackgroundScroll,
    { passive: false }
  );

  window.addEventListener(
    "touchmove",
    preventBackgroundScroll,
    { passive: false }
  );

  function setHeaderHidden(hidden) {
    if (
      window.MOH
      && typeof window.MOH.setHeaderHidden === "function"
    ) {
      window.MOH.setHeaderHidden(hidden);
    }
  }

  function hasChildren(category) {
    return Array.isArray(category.children)
      && category.children.length > 0;
  }

  function goToCategory(category) {
    const url = new URL(indexUrl, window.location.origin);
    url.searchParams.set("category", String(category.id));
    window.location.assign(url.toString());
  }

  function createCategoryRow(category, onExpand) {
    const row = document.createElement("div");
    row.className = "category-row";
    row.dataset.categoryId = String(category.id);

    const selectButton = document.createElement("button");
    selectButton.type = "button";
    selectButton.className = "category-row__select";
    selectButton.textContent = category.title;
    selectButton.addEventListener("click", () => goToCategory(category));
    row.appendChild(selectButton);

    if (hasChildren(category)) {
      const expandButton = document.createElement("button");
      expandButton.type = "button";
      expandButton.className = "category-row__expand";
      expandButton.textContent = "›";
      expandButton.setAttribute(
        "aria-label",
        `Показать подкатегории: ${category.title}`
      );

      expandButton.addEventListener("click", (event) => {
        event.stopPropagation();
        onExpand(category);
      });

      row.appendChild(expandButton);
    }

    return row;
  }

  async function getCategoryTree() {
    if (categoryTree) {
      return categoryTree;
    }

    if (categoryTreePromise) {
      return categoryTreePromise;
    }

    categoryTreePromise = fetch(treeUrl, {
      headers: {
        "X-Requested-With": "XMLHttpRequest"
      }
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      })
      .then((result) => {
        const categories = Array.isArray(result)
          ? result
          : result.categories;

        if (!Array.isArray(categories)) {
          throw new Error("Некорректное дерево категорий.");
        }

        categoryTree = categories;
        return categories;
      })
      .finally(() => {
        categoryTreePromise = null;
      });

    return categoryTreePromise;
  }

  function markActiveRoot(categoryId) {
    rootList.querySelectorAll(".category-row").forEach((row) => {
      row.classList.toggle(
        "is-active",
        Number(row.dataset.categoryId) === Number(categoryId)
      );
    });
  }

  function renderRoots(categories) {
    rootList.innerHTML = "";

    categories.forEach((category) => {
      rootList.appendChild(
        createCategoryRow(category, (selected) => {
          categoryPath = [selected];
          markActiveRoot(selected.id);
          renderDetail(selected);
        })
      );
    });

    rootsRendered = true;
  }

  function renderDetail(category) {
    const depth = categoryPath.length;
    detailTitle.textContent = category.title;

    if (depth > 1) {
      const parent = categoryPath[depth - 2];
      detailParentTitle.textContent = parent.title;
      detailBack.hidden = false;
    } else {
      detailParentTitle.textContent = "";
      detailBack.hidden = true;
    }

    detailList.innerHTML = "";

    category.children.forEach((child) => {
      detailList.appendChild(
        createCategoryRow(child, (selected) => {
          categoryPath.push(selected);
          renderDetail(selected);
        })
      );
    });

    detailDrawer.classList.add("is-open");
    detailDrawer.setAttribute("aria-hidden", "false");
  }

  detailBack.addEventListener("click", () => {
    if (categoryPath.length <= 1) {
      return;
    }

    categoryPath.pop();
    renderDetail(categoryPath[categoryPath.length - 1]);
  });

  async function openMenu() {
    setHeaderHidden(false);

    rootDrawer.classList.add("is-open");
    backdrop.classList.add("is-open");
    menuToggle.classList.add("is-open");
    document.body.classList.add("catalog-menu-open");

    rootDrawer.setAttribute("aria-hidden", "false");
    menuToggle.setAttribute("aria-expanded", "true");

    try {
      if (!categoryTree) {
        rootList.innerHTML = `
          <div class="category-menu-state">
            Загружаем категории...
          </div>
        `;
      }

      const categories = await getCategoryTree();

      if (!categories.length) {
        rootList.innerHTML = `
          <div class="category-menu-state">
            Категорий пока нет.
          </div>
        `;
        return;
      }

      if (!rootsRendered) {
        renderRoots(categories);
      }
    } catch (error) {
      console.error("Ошибка загрузки категорий:", error);

      rootList.innerHTML = `
        <div class="category-menu-state">
          Не удалось загрузить категории.
        </div>
      `;
    }
  }

  function closeMenu() {
    rootDrawer.classList.remove("is-open");
    detailDrawer.classList.remove("is-open");
    backdrop.classList.remove("is-open");
    menuToggle.classList.remove("is-open");
    document.body.classList.remove("catalog-menu-open");

    rootDrawer.setAttribute("aria-hidden", "true");
    detailDrawer.setAttribute("aria-hidden", "true");
    menuToggle.setAttribute("aria-expanded", "false");
  }

  menuToggle.addEventListener("click", () => {
    if (rootDrawer.classList.contains("is-open")) {
      closeMenu();
    } else {
      openMenu();
    }
  });

  backdrop.addEventListener("click", closeMenu);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeMenu();
    }
  });
})();
