/* Search combobox: custom dropdown (no native datalist).
   Suggestions from name + description + type. Offline, zero dependencies. */
(function () {
  "use strict";

  var root = document.querySelector("[data-combo]");
  if (!root) return;
  var input = root.querySelector("[data-combo-input]");
  var list = root.querySelector("[data-combo-list]");
  var dataEl = document.getElementById("suggest-data");
  if (!input || !list || !dataEl) return;

  var items = [];
  try { items = JSON.parse(dataEl.textContent) || []; } catch (e) { items = []; }

  var active = -1;      // index of the highlighted entry
  var current = [];     // current filtered entries

  function norm(s) { return (s || "").toString().toLowerCase(); }

  function match(q) {
    q = norm(q).trim();
    if (!q) return [];
    var out = [];
    for (var i = 0; i < items.length && out.length < 8; i++) {
      var it = items[i];
      var hay = norm(it.name) + " " + norm(it.description) + " " + norm(it.type);
      if (hay.indexOf(q) !== -1) out.push(it);
    }
    return out;
  }

  function close() {
    list.hidden = true;
    list.innerHTML = "";
    input.setAttribute("aria-expanded", "false");
    active = -1;
    current = [];
  }

  function submit() { input.form && input.form.submit(); }

  function choose(it) { input.value = it.name; close(); submit(); }

  function render(q) {
    current = match(q);
    if (!current.length) { close(); return; }
    list.innerHTML = "";
    current.forEach(function (it, idx) {
      var li = document.createElement("li");
      li.className = "combo-opt";
      li.setAttribute("role", "option");
      li.id = "combo-opt-" + idx;

      var badge = document.createElement("span");
      badge.className = "combo-type badge-type-" + it.type;
      badge.textContent = it.type;

      var body = document.createElement("span");
      body.className = "combo-text";
      var name = document.createElement("span");
      name.className = "combo-name";
      name.textContent = it.name;
      var desc = document.createElement("span");
      desc.className = "combo-desc";
      desc.textContent = it.description || "";
      body.appendChild(name);
      body.appendChild(desc);

      li.appendChild(badge);
      li.appendChild(body);
      // mousedown (not click) to beat the input blur
      li.addEventListener("mousedown", function (e) { e.preventDefault(); choose(it); });
      list.appendChild(li);
    });
    list.hidden = false;
    input.setAttribute("aria-expanded", "true");
    active = -1;
  }

  function highlight(next) {
    var opts = list.querySelectorAll(".combo-opt");
    if (!opts.length) return;
    if (active >= 0 && opts[active]) opts[active].classList.remove("is-active");
    active = (next + opts.length) % opts.length;
    opts[active].classList.add("is-active");
    input.setAttribute("aria-activedescendant", opts[active].id);
    opts[active].scrollIntoView({ block: "nearest" });
  }

  input.addEventListener("input", function () { render(input.value); });
  input.addEventListener("focus", function () { if (input.value) render(input.value); });

  input.addEventListener("keydown", function (e) {
    if (list.hidden) {
      if (e.key === "ArrowDown" && input.value) render(input.value);
      return;
    }
    if (e.key === "ArrowDown") { e.preventDefault(); highlight(active + 1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); highlight(active - 1); }
    else if (e.key === "Enter") {
      if (active >= 0 && current[active]) { e.preventDefault(); choose(current[active]); }
      // otherwise Enter submits the form with free text (native behavior)
    } else if (e.key === "Escape") { close(); }
  });

  input.addEventListener("blur", function () { setTimeout(close, 120); });
  document.addEventListener("click", function (e) {
    if (!root.contains(e.target)) close();
  });
})();
