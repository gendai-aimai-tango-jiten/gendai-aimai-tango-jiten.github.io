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
    } else if (kind === 'line') {
      window.open('https://social-plugins.line.me/lineit/share?url=' + encodeURIComponent(url) + '&text=' + encodeURIComponent(text), '_blank', 'noopener');
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
    var fades = $$('.wc, .panel, .umap-item, .ex, .mis');
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
        sh.innerHTML = '<span class="share-label">結果をシェア</span><button type="button" class="sbtn sx" data-share="x">ポスト</button><button type="button" class="sbtn sl" data-share="line">LINE</button><button type="button" class="sbtn sc" data-share="copy">リンクをコピー</button>';
        res.appendChild(sh);
        res.hidden = false;
      });
    });
  });

  // 使用例のアリ・ナシ
  $$('.ex').forEach(function (li) {
    $$('.ex-btn', li).forEach(function (b) {
      b.addEventListener('click', function () {
        if (li.classList.contains('done')) return;
        li.classList.add('done', b.dataset.v === li.dataset.answer ? 'right' : 'wrong');
        b.classList.add('picked');
        $('.ex-ans', li).hidden = false;
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

  // クイズ
  var qd = $('#quiz-data');
  if (qd) {
    var all = JSON.parse(qd.textContent);
    var LABEL = { ok: 'アリ', warn: 'ビミョー', ng: 'ナシ' };
    var CLS = { ok: 'v-ok', warn: 'v-warn', ng: 'v-ng' };
    var base = $('.quiz').dataset.base;
    var qs = [], i = 0, score = 0, missed = {};
    var card = $('#qz-card');

    function shuffle(a) { for (var k = a.length - 1; k > 0; k--) { var j = Math.floor(Math.random() * (k + 1)); var t = a[k]; a[k] = a[j]; a[j] = t; } return a; }
    function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

    function start() {
      qs = shuffle(all.slice()).slice(0, Math.min(10, all.length));
      i = 0; score = 0; missed = {};
      $('#qz-total').textContent = qs.length;
      $('#qz-start').hidden = true; $('#qz-result').hidden = true; $('#qz-play').hidden = false;
      show();
    }
    function show() {
      var q = qs[i];
      $('#qz-n').textContent = i + 1;
      $('#qz-bar').style.width = (i / qs.length * 100) + '%';
      card.className = 'qz-card enter';
      card.innerHTML = '<p class="qz-word"><img class="inline-emo" src="/assets/emoji/' + q.emoji + '.png" alt="">' + esc(q.word) + '</p>' +
        '<p class="qz-text">「' + esc(q.text) + '」</p>' +
        '<div class="qz-btns">' + ['ok', 'warn', 'ng'].map(function (k) { return '<button type="button" class="qz-btn ' + CLS[k] + '" data-v="' + k + '">' + LABEL[k] + '</button>'; }).join('') + '</div>' +
        '<div class="qz-ans" hidden></div>';
      $$('.qz-btn', card).forEach(function (b) { b.addEventListener('click', answer); });
      void card.offsetWidth; // 位置を確定させてから外すと、入ってくる動きになる
      card.classList.remove('enter');
    }
    function answer(e) {
      var q = qs[i], v = e.currentTarget.dataset.v, ok = v === q.answer;
      if (ok) score++; else missed[q.slug] = q.word;
      $$('.qz-btn', card).forEach(function (b) { b.disabled = true; if (b.dataset.v === q.answer) b.classList.add('correct'); if (b.dataset.v === v) b.classList.add('picked'); });
      card.classList.add(ok ? 'right' : 'wrong');
      var a = $('.qz-ans', card);
      a.innerHTML = '<p class="qz-judge">' + (ok ? '正解！' : '残念…') + ' 答えは <b class="' + CLS[q.answer] + '">' + LABEL[q.answer] + '</b></p><p class="qz-note">' + esc(q.note) + '</p>' +
        '<button type="button" class="btn btn-main" id="qz-next">' + (i + 1 < qs.length ? '次の問題へ' : '結果を見る') + '</button>';
      a.hidden = false;
      $('#qz-next').addEventListener('click', function () { i++; if (i < qs.length) show(); else result(); });
      $('#qz-next').focus();
    }
    function result() {
      $('#qz-bar').style.width = '100%';
      var n = qs.length, r = score / n, t;
      if (r >= 0.9) t = ['1f3c6', '歩く現代曖昧単語辞典', '流行語のズレまで見抜いています。友だちの誤用に気づいても、そっとしておいてあげてください。'];
      else if (r >= 0.7) t = ['1f50d', '曖昧ハンター', 'ほとんどの言葉を正しくつかんでいます。あと少しで辞典レベルです。'];
      else if (r >= 0.4) t = ['1fae0', 'ノリで分かってる人', '雰囲気ではつかめていますが、ズレているところもありそうです。'];
      else t = ['1f438', '言葉に蛙化されがちな人', '流行語の意味は人によってばらばらです。ここから一語ずつ確かめていきましょう。'];
      var text = '「アリ？ナシ？曖昧語クイズ」で' + n + '問中' + score + '問正解、称号は「' + t[1] + '」でした。あなたは何点？';
      var miss = Object.keys(missed).map(function (s) { return '<a class="qz-miss" href="/words/' + s + '/">' + esc(missed[s]) + 'のページを読む</a>'; }).join('');
      var el = $('#qz-result');
      el.innerHTML = '<p class="qr-kicker">あなたの曖昧語力</p><img class="qr-emo" src="/assets/emoji/' + t[0] + '.png" alt="">' +
        '<p class="qr-score"><b>' + score + '</b><span>/ ' + n + '問正解</span></p>' +
        '<p class="qr-title"><span class="mk">' + t[1] + '</span></p><p class="qr-text">' + t[2] + '</p>' +
        '<div class="share share-big" data-text="' + esc(text) + '" data-url="' + base + '/quiz/"><span class="share-label">結果をシェア</span>' +
        '<button type="button" class="sbtn sx" data-share="x">ポスト</button><button type="button" class="sbtn sl" data-share="line">LINE</button><button type="button" class="sbtn sc" data-share="copy">リンクをコピー</button></div>' +
        (miss ? '<div class="qr-miss"><p>まちがえた言葉を確かめる</p>' + miss + '</div>' : '') +
        '<button type="button" class="btn btn-sub" id="qz-again">もう一度挑戦する</button>';
      $('#qz-play').hidden = true; el.hidden = false;
      $('#qz-again').addEventListener('click', start);
      window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
    }
    $('#qz-go').addEventListener('click', start);
  }
})();
