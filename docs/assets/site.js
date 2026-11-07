(function () {
  'use strict';
  var HASHTAG = '現代曖昧単語辞典';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  function toast(msg) {
    var t = $('.toast');
    if (!t) { t = document.createElement('div'); t.className = 'toast'; t.setAttribute('role', 'status'); document.body.appendChild(t); }
    t.textContent = msg; t.classList.add('show');
    clearTimeout(t._h); t._h = setTimeout(function () { t.classList.remove('show'); }, 2200);
  }

  function share(kind, text, url) {
    if (kind === 'x') {
      var u = 'https://x.com/intent/post?text=' + encodeURIComponent(text) + '&url=' + encodeURIComponent(url) + '&hashtags=' + encodeURIComponent(HASHTAG);
      window.open(u, '_blank', 'noopener,width=600,height=500');
    } else if (kind === 'facebook') {
      window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(url), '_blank', 'noopener,width=600,height=600');
    } else if (kind === 'threads') {
      window.open('https://www.threads.net/intent/post?text=' + encodeURIComponent(text + ' ' + url + ' #' + HASHTAG), '_blank', 'noopener,width=600,height=600');
    } else {
      var s = text + ' ' + url + ' #' + HASHTAG;
      var done = function () { toast('リンクをコピーしました'); };
      if (navigator.clipboard) navigator.clipboard.writeText(s).then(done, function () { prompt('コピーしてください', s); });
      else prompt('コピーしてください', s);
    }
  }

  // シェアボタン（あとから差し込んだものにも効くよう委譲）
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-share]');
    if (!b) return;
    var box = b.closest('.share');
    share(b.dataset.share, box.dataset.text, box.dataset.url);
  });

  // ランダムに1語
  $$('[data-random]').forEach(function (b) {
    b.addEventListener('click', function () {
      fetch('/words.json').then(function (r) { return r.json(); }).then(function (list) {
        var here = location.pathname;
        var c = list.filter(function (w) { return here.indexOf('/words/' + w.slug + '/') === -1; });
        var w = c[Math.floor(Math.random() * c.length)];
        if (w) location.href = '/words/' + w.slug + '/';
      });
    });
  });

  // 収録語の並び替え
  var list = $('#wordlist');
  if (list) {
    var SORTS = {
      added: function (a, b) { return b.dataset.added.localeCompare(a.dataset.added) || b.dataset.amb - a.dataset.amb; },
      amb: function (a, b) { return b.dataset.amb - a.dataset.amb || b.dataset.mis - a.dataset.mis; },
      kana: function (a, b) { return a.dataset.kana.localeCompare(b.dataset.kana, 'ja'); }
    };
    $$('.sort-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        $$('.sort-btn').forEach(function (x) { x.classList.toggle('on', x === btn); x.setAttribute('aria-pressed', x === btn); });
        $$('.wc', list).sort(SORTS[btn.dataset.sort]).forEach(function (c) { list.appendChild(c); });
      });
    });
  }

  // 検索とタグの絞り込み
  var q = $('#q');
  if (q && list) {
    var tag = new URLSearchParams(location.search).get('tag') || '';
    var norm = function (s) {
      return (s || '').toLowerCase().replace(/[\u30a1-\u30f6]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0x60); });
    };
    // 一度に出すのは24語まで。「もっと見る」で24語ずつ足す
    var PAGE = 24, limit = PAGE;
    var more = $('#more');
    var filter = function (keepLimit) {
      if (keepLimit !== true) limit = PAGE;
      var term = norm(q.value.trim()), shown = 0;
      $$('.wc', list).forEach(function (c) {
        var ok = (!tag || c.dataset.tags.split('|').indexOf(tag) !== -1) && (!term || norm(c.dataset.search).indexOf(term) !== -1);
        if (ok) shown++;
        c.hidden = !ok || shown > limit;
      });
      if (more) {
        more.hidden = shown <= limit;
        more.textContent = 'もっと見る（残り' + (shown - limit) + '語）';
      }
      $$('.chip').forEach(function (b) { var on = b.dataset.tag === tag; b.classList.toggle('on', on); b.setAttribute('aria-pressed', on); });
      $('#empty').hidden = shown !== 0;
      $('#result-count').textContent = (tag || term) ? shown + '語が見つかりました' : '';
    };
    $$('.chip').forEach(function (b) {
      b.addEventListener('click', function () {
        tag = b.dataset.tag;
        var url = new URL(location.href);
        if (tag) url.searchParams.set('tag', tag); else url.searchParams.delete('tag');
        history.replaceState(null, '', url);
        filter();
      });
    });
    q.addEventListener('input', filter);
    if (more) more.addEventListener('click', function () { limit += PAGE; filter(true); });
    // 並び替えたあとも、表示する語数を保ったまま出し直す
    $$('.sort-btn').forEach(function (btn) { btn.addEventListener('click', function () { filter(true); }); });
    filter();
  }

  // 数の数え上げ
  if (!reduce) {
    $$('[data-count]').forEach(function (el) {
      var to = +el.dataset.count, t0 = null;
      el.textContent = '0';
      function step(t) {
        if (!t0) t0 = t;
        var p = Math.min(1, (t - t0) / 900);
        el.textContent = Math.round(to * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
      setTimeout(function () { el.textContent = to; }, 1200); // 描画が止まっている環境でも最後の数にする
    });
  }

  // ふわっと出す
  // 画面の下にあるものだけ隠し、スクロールで位置に来たら出す
  if (!reduce) {
    var fades = $$('.wc, .panel, .umap-item, .mis');
    fades.forEach(function (el) { if (el.getBoundingClientRect().top > innerHeight) el.classList.add('fade'); });
    var check = function () {
      fades.forEach(function (el) {
        if (el.classList.contains('fade') && el.getBoundingClientRect().top < innerHeight * 0.95) el.classList.add('in');
      });
    };
    addEventListener('scroll', check, { passive: true });
    addEventListener('resize', check);
    addEventListener('hashchange', function () { setTimeout(check, 50); });
  }

  // あなたはどの意味派？
  var POLL_MSG = {
    '原義': ['もともとの意味派', 'この言葉が生まれたときの意味で使っています。いまは少数派かもしれませんが、出典に一番近い使い方です。'],
    '拡張': ['広がった使い方派', '流行の中で広がった意味で使っています。いまはこちらで使う人が多い一方、もとの意味を知る人とは話がずれることがあります。'],
    '誤用寄り': ['自由に使う派', '出典からはだいぶ離れた使い方です。通じる相手も多いですが、意味の芯からは外れています。'],
    'none': ['はじめまして派', 'このページで知った言葉ですね。まずは下の「意味の地図」から読んでみてください。']
  };
  $$('.poll').forEach(function (poll) {
    var res = $('.poll-result', poll);
    $$('.poll-opt', poll).forEach(function (b) {
      b.addEventListener('click', function () {
        $$('.poll-opt', poll).forEach(function (x) { x.classList.toggle('picked', x === b); x.setAttribute('aria-pressed', x === b); });
        var m = POLL_MSG[b.dataset.type];
        var word = poll.dataset.word;
        var text = b.dataset.type === 'none'
          ? '「' + word + '」、知らなかった。どういう意味か調べてみた'
          : '私の「' + word + '」は「' + b.dataset.label + '」派でした。あなたはどの意味で使ってる？';
        res.innerHTML = '<p class="pr-badge">' + m[0] + '</p><p class="pr-text">' + m[1] + '</p>';
        var sh = document.createElement('div');
        sh.className = 'share'; sh.dataset.text = text; sh.dataset.url = poll.dataset.url;
        // ページ内のシェアボタンと同じ並びを写す
        var tpl = $('.share');
        sh.innerHTML = '<span class="share-label">結果をシェア</span>' + (tpl ? $$('.sbtn', tpl).map(function (x) { return x.outerHTML; }).join('') : '');
        res.appendChild(sh);
        res.hidden = false;
      });
    });
  });

  // 観点のタブ
  $$('.ptabs').forEach(function (tabs) {
    var panels = $$('.ppanel', tabs.nextElementSibling);
    $$('.ptab', tabs).forEach(function (t) {
      t.addEventListener('click', function () {
        $$('.ptab', tabs).forEach(function (x) { x.classList.toggle('on', x === t); x.setAttribute('aria-selected', x === t); });
        panels.forEach(function (p) { p.hidden = p.dataset.i !== t.dataset.i; });
      });
    });
  });

})();
