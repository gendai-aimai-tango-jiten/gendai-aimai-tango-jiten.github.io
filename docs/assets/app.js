(function () {
  var grid = document.getElementById('grid');
  if (!grid) return;
  var q = document.getElementById('q');
  var sort = document.getElementById('sort');
  var empty = document.getElementById('empty');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.wcard'));
  var tag = new URLSearchParams(location.search).get('tag') || '';

  function norm(s) {
    // カタカナをひらがなに寄せ、大文字小文字を無視する
    return (s || '').toLowerCase().replace(/[ァ-ヶ]/g, function (c) {
      return String.fromCharCode(c.charCodeAt(0) - 0x60);
    });
  }

  function apply() {
    var term = norm(q.value.trim());
    var shown = 0;
    cards.forEach(function (c) {
      var okTag = !tag || c.dataset.tags.split('|').indexOf(tag) !== -1;
      var okQ = !term || norm(c.dataset.search).indexOf(term) !== -1;
      c.hidden = !(okTag && okQ);
      if (!c.hidden) shown++;
    });
    empty.hidden = shown !== 0;
    chips.forEach(function (b) { b.classList.toggle('active', b.dataset.tag === tag); });
  }

  function reorder() {
    var key = sort.value;
    cards.sort(function (a, b) {
      if (key === 'amb') return b.dataset.amb - a.dataset.amb;
      if (key === 'mis') return b.dataset.mis - a.dataset.mis;
      if (key === 'date') return b.dataset.date.localeCompare(a.dataset.date);
      return a.dataset.kana.localeCompare(b.dataset.kana, 'ja');
    });
    cards.forEach(function (c) { grid.appendChild(c); });
  }

  chips.forEach(function (b) {
    b.addEventListener('click', function () {
      tag = b.dataset.tag;
      var url = new URL(location.href);
      if (tag) url.searchParams.set('tag', tag); else url.searchParams.delete('tag');
      history.replaceState(null, '', url);
      apply();
    });
  });
  q.addEventListener('input', apply);
  sort.addEventListener('change', reorder);
  apply();
})();
