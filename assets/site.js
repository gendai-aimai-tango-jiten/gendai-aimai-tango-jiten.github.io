(function () {
  'use strict';
  var HASHTAG = '現代曖昧単語辞典';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  // アクセス解析（GoatCounter）に出来事を1件送る。読み込まれていなければ何もしない
  function track(path, title) {
    try {
      if (window.goatcounter && goatcounter.count) goatcounter.count({ path: path, title: title || path, event: true });
    } catch (e) { /* 数えられなくても画面は止めない */ }
  }

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
    track('share/' + b.dataset.share + location.pathname, 'シェア：' + b.dataset.share);
  });

  // ダーク表示とライト表示の切り替え（ふだんはライト。選んだほうをこのブラウザに覚えておく）
  var root = document.documentElement;
  var current = function () { return root.dataset.theme === 'dark' ? 'dark' : 'light'; };
  var labelTheme = function () {
    var l = current() === 'dark' ? 'ライト表示にする' : 'ダーク表示にする';
    $$('[data-theme-toggle]').forEach(function (b) { b.setAttribute('aria-label', l); b.title = l; });
  };
  $$('[data-theme-toggle]').forEach(function (b) {
    b.addEventListener('click', function () {
      var next = current() === 'dark' ? 'light' : 'dark';
      root.dataset.theme = next;
      try { localStorage.setItem('theme', next); } catch (e) { /* 覚えられなくても切り替えはできる */ }
      labelTheme();
      track('theme/' + next, '表示：' + next);
    });
  });
  labelTheme();

  // ランダムに1語
  $$('[data-random]').forEach(function (b) {
    b.addEventListener('click', function () {
      track('random', 'ランダムに1つ見てみる');
      fetch('/words.json').then(function (r) { return r.json(); }).then(function (list) {
        var here = location.pathname;
        var c = list.filter(function (w) { return here.indexOf('/words/' + w.slug + '/') === -1; });
        var w = c[Math.floor(Math.random() * c.length)];
        if (w) location.href = '/words/' + w.slug + '/';
      });
    });
  });

  // 収録語の一覧
  // ページには推奨度順の最初の24語だけを入れ、残りは並び替え・検索・タグ・「もっと見る」を使ったときに
  // /cards.json から読み込む（語が増えてもトップを軽く保つため）
  var list = $('#wordlist');
  var q = $('#q');
  if (list && q) {
    var SORTS = {
      rec: function (a, b) { return a.dataset.rec - b.dataset.rec; },
      now: function (a, b) { return b.dataset.now - a.dataset.now || b.dataset.rich - a.dataset.rich; },
      amb: function (a, b) { return b.dataset.amb - a.dataset.amb || b.dataset.mis - a.dataset.mis; },
      kana: function (a, b) { return a.dataset.kana.localeCompare(b.dataset.kana, 'ja'); }
    };
    var total = +list.dataset.total || 0;
    var loaded = $$('.wc', list).length >= total;
    var waiting = [];
    var ensureAll = function (cb) {
      if (loaded) { cb(); return; }
      waiting.push(cb);
      if (waiting.length > 1) return;
      fetch(list.dataset.src).then(function (r) { return r.json(); }).then(function (cards) {
        list.innerHTML = cards.join('');
        loaded = true;
      }).catch(function () { /* 読み込めなくても、いまある語で続ける */ }).then(function () {
        var w = waiting; waiting = [];
        w.forEach(function (f) { f(); });
      });
    };
    var sortKey = 'rec';
    var applySort = function () { $$('.wc', list).sort(SORTS[sortKey]).forEach(function (c) { list.appendChild(c); }); };

    var tag = new URLSearchParams(location.search).get('tag') || '';
    var norm = function (s) {
      return (s || '').toLowerCase().replace(/[ァ-ヶ]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0x60); });
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
      // まだ全部を読み込んでいないときは、絞り込みなしの総数で「もっと見る」を出す
      if (!loaded && !tag && !term) shown = total;
      if (more) {
        more.hidden = shown <= limit;
        if (shown > limit) more.textContent = 'もっと見る（残り' + (shown - limit) + '語）';
      }
      $$('.chip').forEach(function (b) { var on = b.dataset.tag === tag; b.classList.toggle('on', on); b.setAttribute('aria-pressed', on); });
      // 0語のときは下の箱で伝えるので、数は出さない
      $('#result-count').textContent = (tag || term) && shown ? shown + '語が見つかりました' : '';
      if (shown === 0) showMiss(q.value.trim(), term); else { $('#empty').hidden = true; $('#empty').classList.remove('show'); }
      paintHits(term);
    };

    // 見つけた文字に印を付ける（CSS Custom Highlight API。対応していないブラウザでは印が出ないだけ）
    var canHL = window.CSS && CSS.highlights && typeof Highlight === 'function';
    var paintHits = function (term) {
      if (!canHL) return;
      if (!term) { CSS.highlights.delete('hit'); return; }
      var hl = new Highlight();
      $$('.wc:not([hidden])', list).forEach(function (c) {
        $$('.wc-reading, .wc-word, .wc-catch, .wc-tags i', c).forEach(function (el) {
          var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), node;
          while ((node = walker.nextNode())) {
            var t = norm(node.data), from = 0, k;
            while ((k = t.indexOf(term, from)) !== -1) {
              var r = new Range(); r.setStart(node, k); r.setEnd(node, k + term.length); hl.add(r); from = k + term.length;
            }
          }
        });
      });
      CSS.highlights.set('hit', hl);
    };
    // 見つからないとき：取り上げてほしい言葉としてフォームで送る導線と、読みが近い言葉
    var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
    var bigrams = function (s) { var a = []; for (var i = 0; i < s.length - 1; i++) a.push(s.substr(i, 2)); return a; };
    var dice = function (a, b) {
      if (!a.length || !b.length) return 0;
      var m = 0, bb = b.slice();
      a.forEach(function (x) { var k = bb.indexOf(x); if (k >= 0) { m++; bb.splice(k, 1); } });
      return 2 * m / (a.length + b.length);
    };
    var showMiss = function (raw, term) {
      var box = $('#empty');
      var lead = $('.nofind-lead', box), act = $('.nofind-act', box), title = $('.nofind-near-title', box);
      var near = [];
      if (tag) {
        // タグで絞り込んだ中で見つからないとき
        lead.textContent = '「' + raw + '」は、このタグの中には見つかりませんでした。';
        act.hidden = true; title.textContent = 'タグを外して探す';
        $('.nofind-near', box).innerHTML = '<a href="/#words" data-untag>すべての言葉から探す</a>';
      } else {
        lead.textContent = '「' + raw + '」は、まだ収録していません。取り上げてほしい言葉として送れます。';
        act.hidden = false; title.textContent = '読みが近い言葉';
        $('.nofind-form', box).href = box.dataset.form + encodeURIComponent('収録の希望：' + raw);
        var all = $$('.wc', list).map(function (c) { return { word: $('.wc-word', c).textContent, kana: c.dataset.kana, href: c.getAttribute('href') }; })
          .sort(function (a, b) { return a.kana.localeCompare(b.kana, 'ja'); });
        var qa = bigrams(term);
        near = all.map(function (w) {
          var r = w.kana, sc = Math.max(dice(qa, bigrams(r)), dice(qa, bigrams(norm(w.word))));
          var p = 0; while (p < term.length && p < r.length && term[p] === r[p]) p++;
          return { w: w, s: sc + p * 0.2 };
        }).filter(function (x) { return x.s >= 0.2; }).sort(function (a, b) { return b.s - a.s; }).slice(0, 3).map(function (x) { return x.w; });
        if (near.length < 2) {
          var pos = 0; while (pos < all.length && all[pos].kana.localeCompare(term, 'ja') < 0) pos++;
          [all[pos - 1], all[pos], all[pos - 2], all[pos + 1]].forEach(function (w) { if (w && near.length < 3 && near.indexOf(w) === -1) near.push(w); });
        }
        $('.nofind-near', box).innerHTML = near.map(function (w) {
          return '<a href="' + esc(w.href) + '">' + esc(w.word) + (norm(w.word) === w.kana ? '' : '<span>' + esc(w.kana) + '</span>') + '</a>';
        }).join('');
      }
      var wasHidden = box.hidden;
      box.hidden = false;
      if (wasHidden) { box.classList.remove('show'); void box.offsetWidth; box.classList.add('show'); }
    };
    document.addEventListener('click', function (e) {
      var a = e.target.closest('[data-untag]');
      if (!a) return;
      e.preventDefault();
      var allChip = $('.chip[data-tag=""]'); if (allChip) allChip.click();
    });
    // 「/」キーで検索窓へ（入力欄に文字を打っているときと、修飾キーを押しているときは効かせない）
    document.addEventListener('keydown', function (e) {
      if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return;
      var t = e.target;
      if (t.closest && t.closest('input, textarea, select, [contenteditable="true"]')) return;
      e.preventDefault(); q.focus(); q.select();
    });
    q.addEventListener('keydown', function (e) { if (e.key === 'Escape' && q.value) { q.value = ''; ensureAll(function () { applySort(); filter(); }); } });

    $$('.sort-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        $$('.sort-btn').forEach(function (x) { x.classList.toggle('on', x === btn); x.setAttribute('aria-pressed', x === btn); });
        sortKey = btn.dataset.sort;
        // 並び替えたあとも、表示する語数を保ったまま出し直す
        ensureAll(function () { applySort(); filter(true); });
      });
    });
    $$('.chip').forEach(function (b) {
      b.addEventListener('click', function () {
        tag = b.dataset.tag;
        if (tag) track('tag/' + tag, 'タグ：' + tag);
        var url = new URL(location.href);
        if (tag) url.searchParams.set('tag', tag); else url.searchParams.delete('tag');
        history.replaceState(null, '', url);
        ensureAll(function () { applySort(); filter(); });
      });
    });
    q.addEventListener('focus', function () { ensureAll(function () { applySort(); filter(true); }); });
    q.addEventListener('input', function () { ensureAll(function () { applySort(); filter(); }); });
    // 入力が1.5秒止まったら、検索された言葉として数える
    var qTimer;
    q.addEventListener('input', function () {
      clearTimeout(qTimer);
      qTimer = setTimeout(function () {
        var v = q.value.trim();
        if (v.length >= 2) track('search/' + v, '検索：' + v);
      }, 1500);
    });
    if (more) more.addEventListener('click', function () { ensureAll(function () { applySort(); limit += PAGE; filter(true); }); });

    var afterFirst = function () {
      // 単語ページのタグから来たときは、選ばれたタグが横に隠れないよう見える位置まで送る
      var onChip = tag && $('.chip.on');
      if (onChip) { var box = onChip.parentNode; box.scrollLeft += onChip.getBoundingClientRect().left - box.getBoundingClientRect().left - 16; }
      // 絞り込んで一覧の高さが変わったあとに、一覧の位置へ移る
      if (location.hash === '#words' && $('#words')) $('#words').scrollIntoView();
    };
    if (tag) ensureAll(function () { filter(); afterFirst(); });
    else { filter(); afterFirst(); }
  }

  // 数の数え上げ
  if (!reduce) {
    $$('[data-count]').forEach(function (el) {
      var to = +el.dataset.count, t0 = null;
      // 数えている間も、最後の数の幅のままにする（横の「語収録」やボタンが動かないように。右にそろえて数える）
      var lock = function () { el.style.minWidth = ''; el.style.minWidth = Math.ceil(el.getBoundingClientRect().width) + 'px'; };
      lock();
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { var t = el.textContent; el.textContent = to; lock(); el.textContent = t; });
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

  // あなたはどの意味派？
  var POLL_MSG = {
    '原義': ['もともとの意味派', 'この言葉が生まれたときの意味で使っています。いまは少数派かもしれませんが、出典に一番近い使い方です。'],
    '拡張': ['広がった使い方派', '流行の中で広がった意味で使っています。いまはこちらで使う人が多い一方、もとの意味を知る人とは話がずれることがあります。'],
    '誤用寄り': ['自由に使う派', '出典からはだいぶ離れた使い方です。通じる相手も多いですが、意味の芯からは外れています。'],
    'none': ['はじめまして派', 'このページで知った言葉ですね。まずは下の「意味の変遷」から読んでみてください。']
  };
  $$('.poll').forEach(function (poll) {
    var res = $('.poll-result', poll);
    $$('.poll-opt', poll).forEach(function (b) {
      b.addEventListener('click', function () {
        $$('.poll-opt', poll).forEach(function (x) { x.classList.toggle('picked', x === b); x.setAttribute('aria-pressed', x === b); });
        var m = POLL_MSG[b.dataset.type];
        track('poll' + location.pathname + b.dataset.i, '意味派：' + b.dataset.label);
        var word = poll.dataset.word;
        var text = b.dataset.type === 'none'
          ? '「' + word + '」、知らなかった。どういう意味か調べてみた'
          : '私の「' + word + '」は「' + b.dataset.label + '」派でした。あなたはどの意味で使ってる？';
        res.innerHTML = '<p class="pr-pre">あなたは</p><p class="pr-badge">' + m[0] + '</p><p class="pr-text">' + m[1] + '</p>';
        // みんなの意味派：集計がたまっている語だけ、自分の1票を足して割合を出す
        var opts = $$('.poll-opt', poll);
        var total = opts.reduce(function (s, x) { return s + (+x.dataset.votes || 0); }, 0);
        if (total >= (+poll.dataset.min || 10)) {
          var all = total + 1;
          var rows = opts.map(function (x) {
            var n = (+x.dataset.votes || 0) + (x === b ? 1 : 0);
            var pct = Math.round(n * 100 / all);
            return '<li class="' + (x === b ? 'me' : '') + '"><span class="pd-label">' + $('.poll-label', x).textContent +
              '</span><span class="pd-bar"><i style="width:' + pct + '%"></i></span><b>' + pct + '%</b></li>';
          }).join('');
          var mine = Math.round(((+b.dataset.votes || 0) + 1) * 100 / all);
          res.innerHTML += '<p class="pd-title">みんなの意味派（' + all + '人が回答）</p><ol class="pd">' + rows + '</ol>';
          text = b.dataset.type === 'none'
            ? '「' + word + '」、知らなかった。回答した人の' + mine + '%も知らなかったらしい'
            : '私の「' + word + '」は「' + b.dataset.label + '」派。回答した人の' + mine + '%が同じでした。あなたはどの意味で使ってる？';
        }
        // シェアすると出る画像を、写真のように見せる（選んだときに1枚だけ読み込む。読み込めなければ出さない）
        if (b.dataset.og) {
          var fig = document.createElement('figure');
          fig.className = 'pr-og';
          fig.innerHTML = '<figcaption>この画像つきでシェアされます</figcaption>';
          var img = document.createElement('img');
          img.className = 'pr-photo'; img.width = 1200; img.height = 630; img.decoding = 'async';
          img.alt = 'シェアされる画像：' + (b.dataset.type === 'none' ? '「' + word + '」を知らなかった派' : '私の「' + word + '」は「' + b.dataset.label + '」派');
          img.addEventListener('error', function () { fig.remove(); });
          img.src = b.dataset.og;
          fig.appendChild(img);
          res.appendChild(fig);
        }
        var sh = document.createElement('div');
        // シェアするURLは、結果の画像が出る専用ページにする
        sh.className = 'share'; sh.dataset.text = text; sh.dataset.url = poll.dataset.url + 'ha/' + b.dataset.i + '/';
        // ページ内のシェアボタンと同じ並びを写す
        var tpl = $('.share');
        sh.innerHTML = '<span class="share-label">結果をシェア</span>' + (tpl ? $$('.sbtn', tpl).map(function (x) { return x.outerHTML; }).join('') : '');
        res.appendChild(sh);
        res.hidden = false;
        // チェックが描かれ、判子が押される動きを、押すたびに最初から
        [b, res].forEach(function (el) { el.classList.remove('go'); void el.offsetWidth; el.classList.add('go'); });
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


  // ===== 2026-11-15 レベルアップ =====

  // 曖昧メーター：画面に入ったら目盛りを点け、数字を0から数え上げる
  var meters = $('.mbars');
  if (meters && !reduce && 'IntersectionObserver' in window) {
    var mio = new IntersectionObserver(function (es) {
      if (!es[0].isIntersecting) return;
      mio.disconnect();
      $$('.mbar', meters).forEach(function (bar) {
        var v = $('.mbar-v', bar), cells = $$('.mbar-cells i.on', bar);
        if (!v || !cells.length) return;
        v.textContent = '0';
        cells.forEach(function (cell, i) {
          cell.addEventListener('animationstart', function on(e) {
            if (e.animationName !== 'cell-on') return;
            cell.removeEventListener('animationstart', on);
            v.textContent = String(i + 1);
          });
        });
      });
      meters.classList.add('play');
      // 動きが止まる環境でも、最後の数字にそろえる
      setTimeout(function () { $$('.mbar-v', meters).forEach(function (v) { v.textContent = v.dataset.v; }); }, 2000);
    }, { threshold: 0.4 });
    mio.observe(meters);
  }

  // トップの絵：数秒ごとに別の言葉へ。いまの点が満ちたら次へ進み、点を押せばその言葉へ切り替わる
  // 見えている間だけ進め、マウスを乗せている間は止める。動きを減らす設定の人には自動で進めない（押せば切り替わる）
  var scene = $('.scene');
  if (scene) {
    var pairs = [];
    try { pairs = JSON.parse(scene.dataset.pairs || '[]'); } catch (e) { pairs = []; }
    var pager = $('.scene-pager', scene);
    if (pairs.length > 1 && pager) {
      pager.hidden = false;
      var si = 0, svisible = false, shover = false;
      var dots = $$('.scene-dot', scene);
      var fillSide = function (side, u) {
        var t = $('.scene-' + side + ' .poll-tag', scene);
        t.className = 'poll-tag ' + u[0]; t.textContent = u[1];
        $('.scene-' + side + ' .scene-label', scene).textContent = u[2];
      };
      var renderPair = function (i) {
        var pr = pairs[i];
        fillSide('l', pr.a); fillSide('r', pr.b);
        $('.scene-say b', scene).textContent = pr.say;
        $('.scene-word', scene).textContent = pr.word;
        $('.scene-go', scene).href = '/words/' + pr.slug + '/';
        $('.scene-mini-emo', scene).src = '/assets/emoji/' + pr.emoji + '.png';
        dots.forEach(function (d, k) { d.classList.toggle('on', k === i); d.setAttribute('aria-pressed', String(k === i)); });
      };
      var syncPause = function () { scene.classList.toggle('paused', shover || !svisible || document.hidden); };
      var goPair = function (i) {
        if (i === si) return;
        scene.classList.remove('enter'); scene.classList.add('leave');
        setTimeout(function () {
          si = i;
          renderPair(si);
          scene.classList.remove('leave'); void scene.offsetWidth; scene.classList.add('enter');
        }, reduce ? 0 : 170);
      };
      dots.forEach(function (d, k) { d.addEventListener('click', function () { goPair(k); }); });
      if (!reduce) {
        scene.classList.add('timing');
        // いまの点が満ちきったら次の言葉へ
        scene.addEventListener('animationend', function (e) {
          if (e.animationName === 'scene-timer') goPair((si + 1) % pairs.length);
        });
        if ('IntersectionObserver' in window) {
          new IntersectionObserver(function (es) { svisible = es[0].isIntersecting; syncPause(); }, { threshold: 0.4 }).observe(scene);
        } else { svisible = true; }
        scene.addEventListener('mouseenter', function () { shover = true; syncPause(); });
        scene.addEventListener('mouseleave', function () { shover = false; syncPause(); });
        scene.addEventListener('focusin', function () { shover = true; syncPause(); });
        scene.addEventListener('focusout', function () { shover = false; syncPause(); });
        document.addEventListener('visibilitychange', syncPause);
        syncPause();
      }
    }
  }

  // カードから単語ページへ、見出し語がつながって移る（View Transitions。名前は押したカードの語にだけ付ける）
  var vtName = function (el) { if (el) el.style.viewTransitionName = 'vt-word'; };
  var wordOf = function (path) { var m = /^\/words\/([^/]+)\/$/.exec(path); return m && m[1]; };
  window.addEventListener('pageswap', function (e) {
    if (!e.viewTransition || !e.activation || !e.activation.entry) return;
    var to = new URL(e.activation.entry.url);
    var slug = wordOf(to.pathname);
    var here = wordOf(location.pathname);
    if (here && !slug) vtName($('.whero-word .fit'));                     // 単語ページ → 一覧
    else if (slug) vtName($('.wc[href="/words/' + slug + '/"] .fit'));   // 一覧 → 単語ページ
  });
  window.addEventListener('pagereveal', function (e) {
    if (!e.viewTransition) return;
    var from = window.navigation && navigation.activation && navigation.activation.from;
    var fromSlug = from && from.url ? wordOf(new URL(from.url).pathname) : null;
    var el = wordOf(location.pathname) ? $('.whero-word .fit') : (fromSlug && $('.wc[href="/words/' + fromSlug + '/"] .fit'));
    if (!el) return;
    vtName(el);
    e.viewTransition.finished.then(function () { el.style.viewTransitionName = ''; }, function () { el.style.viewTransitionName = ''; });
  });

  // 本文に出てくる収録語：指を乗せる（タップ・フォーカス）と、意味のカードを出す
  var terms = $$('.term');
  if (terms.length && typeof HTMLElement.prototype.showPopover === 'function') {
    var pop = document.createElement('div');
    pop.className = 'term-pop';
    pop.setAttribute('popover', 'manual');
    pop.setAttribute('role', 'dialog');
    document.body.appendChild(pop);
    var cur = null, showT = 0, hideT = 0, wasOpen = false, lastType = 'mouse', skipFocus = false;
    var isOpen = function () { return pop.matches(':popover-open'); };
    var escT = function (x) { return String(x).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
    var fillPop = function (t) {
      var d = t.dataset;
      pop.setAttribute('aria-label', d.word + 'の要約');
      pop.innerHTML = '<div class="term-card"><div class="term-top"><span class="term-circle"><img src="/assets/emoji/' + escT(d.emoji) + '.png" alt="" width="32" height="32"></span>' +
        '<div><p class="term-yomi">' + escT(d.yomi) + '</p><p class="term-word">' + escT(d.word) + '</p></div></div>' +
        '<p class="term-catch">『' + escT(d.catch) + '』</p>' +
        '<p class="term-amb"><span>曖昧度</span><b style="--v:' + escT(d.amb) + '"></b><em>' + escT(d.amb) + '</em></p>' +
        '<a class="term-go" href="' + escT(t.getAttribute('href')) + '">ページを読む →</a></div>';
    };
    var place = function (t) {
      var r = t.getBoundingClientRect(), w = pop.offsetWidth, h = pop.offsetHeight;
      var x = Math.max(8, Math.min(r.left + r.width / 2 - w / 2, innerWidth - w - 8));
      var y = r.bottom + 8;
      if (y + h > innerHeight - 8 && r.top - h - 8 > 8) y = r.top - h - 8;
      pop.style.left = Math.round(x) + 'px'; pop.style.top = Math.round(y) + 'px';
    };
    var showPop = function (t) {
      clearTimeout(hideT);
      if (cur === t && isOpen()) return;
      if (cur) cur.setAttribute('aria-expanded', 'false');
      cur = t; fillPop(t);
      t.setAttribute('aria-expanded', 'true');
      pop.classList.remove('in');
      if (!isOpen()) pop.showPopover();
      place(t);
      void pop.offsetWidth; pop.classList.add('in');
    };
    var hidePop = function () {
      clearTimeout(showT); clearTimeout(hideT);
      if (isOpen()) pop.hidePopover();
      if (cur) cur.setAttribute('aria-expanded', 'false');
      cur = null;
    };
    terms.forEach(function (t) {
      t.setAttribute('aria-haspopup', 'dialog');
      t.setAttribute('aria-expanded', 'false');
      t.addEventListener('pointerdown', function (e) { lastType = e.pointerType || 'mouse'; wasOpen = cur === t && isOpen(); });
      t.addEventListener('pointerenter', function (e) { if (e.pointerType !== 'mouse') return; clearTimeout(hideT); showT = setTimeout(function () { showPop(t); }, 120); });
      t.addEventListener('pointerleave', function (e) { if (e.pointerType !== 'mouse') return; clearTimeout(showT); hideT = setTimeout(hidePop, 250); });
      t.addEventListener('focus', function () { if (!skipFocus) showPop(t); });
      t.addEventListener('blur', function () { hideT = setTimeout(function () { if (!pop.contains(document.activeElement)) hidePop(); }, 150); });
      // スマホ：1回目のタップでカード、もう一度タップでページへ
      t.addEventListener('click', function (e) {
        var touch = e.detail !== 0 && lastType !== 'mouse';
        if (touch && !wasOpen) { e.preventDefault(); showPop(t); }
        wasOpen = false;
      });
    });
    pop.addEventListener('pointerenter', function () { clearTimeout(hideT); });
    pop.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse') hideT = setTimeout(hidePop, 250); });
    pop.addEventListener('focusout', function () { hideT = setTimeout(function () { if (!pop.contains(document.activeElement) && terms.indexOf(document.activeElement) < 0) hidePop(); }, 150); });
    document.addEventListener('pointerdown', function (e) { if (isOpen() && !pop.contains(e.target) && terms.indexOf(e.target) < 0) hidePop(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && isOpen()) { var t = cur; hidePop(); if (t) { skipFocus = true; t.focus({ preventScroll: true }); skipFocus = false; } } });
    addEventListener('scroll', function () { if (cur && isOpen()) place(cur); }, { passive: true, capture: true });
    addEventListener('resize', function () { if (cur && isOpen()) place(cur); });
  }

  // 辞書をめくるように：← → キーで前後の言葉へ（入力欄・タブにいるときと、修飾キーを押しているときは効かせない）
  var hs = $('.hashira');
  if (hs) {
    document.addEventListener('keydown', function (e) {
      if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      var t = e.target;
      if (t.closest && t.closest('input, textarea, select, [contenteditable="true"], [role="tab"], .mtoc')) return;
      var a = $(e.key === 'ArrowLeft' ? '.hs-prev' : '.hs-next', hs);
      if (a) location.href = a.href;
    });
  }

  // 気になった一文を選ぶと、その文ごとシェアできる（URL にテキストフラグメントを付け、開いた人にその文の印が出る）
  var article = $('article.word');
  if (article) {
    var bodyParas = function (p) { return p && p.closest('.wmain') && p.closest('.wsec, .tldr, .gloss') && !p.closest('.wsec-poll, .srcs, .fixlink, .endcta'); };
    var bar = document.createElement('div');
    bar.className = 'pickbar'; bar.hidden = true;
    bar.innerHTML = '<button type="button" class="sbtn sx" data-pick="x"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>この一文をポスト</button>' +
      '<button type="button" class="sbtn sc" data-pick="copy">コピー</button>';
    document.body.appendChild(bar);
    var canPickHL = window.CSS && CSS.highlights && typeof Highlight === 'function';
    var coarse = matchMedia('(pointer: coarse)').matches;
    var picked = null, ptimer = 0, phide = 0;
    var offsetIn = function (p, node, off) { var r = document.createRange(); r.selectNodeContents(p); r.setEnd(node, off); return r.toString().length; };
    var rangeOf = function (p, a, b2) {
      var r = document.createRange(), walk = document.createTreeWalker(p, NodeFilter.SHOW_TEXT), n, pos = 0, setA = false;
      while ((n = walk.nextNode())) {
        var len = n.data.length;
        if (!setA && a <= pos + len) { r.setStart(n, a - pos); setA = true; }
        if (setA && b2 <= pos + len) { r.setEnd(n, b2 - pos); return r; }
        pos += len;
      }
      r.setEnd(p, p.childNodes.length); return r;
    };
    // 途中までしか選んでいなくても、句点から句点までの一文に広げる
    var sentence = function (p, st, en) {
      var t = p.textContent, END = '。！？', CLOSE = '」』）';
      var a = st; while (a > 0 && END.indexOf(t[a - 1]) < 0) a--;
      while (a < t.length && /\s/.test(t[a])) a++;
      var b2 = Math.max(en, a + 1);
      if (END.indexOf(t[b2 - 1]) < 0) { while (b2 < t.length && END.indexOf(t[b2 - 1]) < 0) b2++; }
      while (b2 < t.length && CLOSE.indexOf(t[b2]) >= 0) b2++;
      return { p: p, a: a, b: b2, text: t.slice(a, b2).trim() };
    };
    var encF = function (x) { return encodeURIComponent(x).replace(/-/g, '%2D'); };
    var fragment = function (text) {
      if (text.length > 80) {
        var i = text.indexOf('、'), j = text.lastIndexOf('、');
        if (i > 0 && j > i) return '#:~:text=' + encF(text.slice(0, i)) + ',' + encF(text.slice(j + 1));
      }
      return '#:~:text=' + encF(text);
    };
    var hideBar = function () { bar.hidden = true; bar.classList.remove('in'); if (canPickHL) CSS.highlights.delete('pick'); };
    var placeBar = function (range) {
      var rs = range.getClientRects(), first = rs[0] || range.getBoundingClientRect(), last = rs[rs.length - 1] || first;
      var wasHidden = bar.hidden;
      bar.hidden = false;
      var w = bar.offsetWidth, h = bar.offsetHeight;
      // iPhone などでは選んだ文の上に OS のメニューが出るので、下に出す
      var down = coarse || first.top < h + 80;
      var anchor = down ? last : first;
      var cx = anchor.left + anchor.width / 2;
      var x = Math.max(8, Math.min(cx - w / 2, document.documentElement.clientWidth - w - 8));
      var y = down ? anchor.bottom + 12 : first.top - h - 12;
      bar.style.left = Math.round(x + scrollX) + 'px';
      bar.style.top = Math.round(y + scrollY) + 'px';
      bar.style.setProperty('--tip', Math.round(Math.max(20, Math.min(cx - x, w - 20))) + 'px');
      bar.classList.toggle('down', down); bar.classList.toggle('up', !down);
      if (wasHidden) { bar.classList.remove('in'); void bar.offsetWidth; bar.classList.add('in'); }
    };
    var checkSel = function () {
      var sel = getSelection();
      if (!sel || !sel.rangeCount || sel.isCollapsed) { clearTimeout(phide); phide = setTimeout(hideBar, 250); return; }
      var r = sel.getRangeAt(0);
      var sp = r.startContainer.nodeType === 1 ? r.startContainer : r.startContainer.parentNode;
      var p = sp.closest && sp.closest('p, li');
      if (!bodyParas(p)) { hideBar(); return; }
      clearTimeout(phide);
      var st = offsetIn(p, r.startContainer, r.startOffset);
      var en = p.contains(r.endContainer) ? offsetIn(p, r.endContainer, r.endOffset) : p.textContent.length;
      if (en - st < 2) { hideBar(); return; }
      picked = sentence(p, st, en);
      var whole = rangeOf(p, picked.a, picked.b);
      if (canPickHL) CSS.highlights.set('pick', new Highlight(whole));
      placeBar(whole);
    };
    document.addEventListener('selectionchange', function () { clearTimeout(ptimer); ptimer = setTimeout(checkSel, 180); });
    bar.addEventListener('mousedown', function (e) { e.preventDefault(); });
    var compose = function () {
      if (!picked) return null;
      var text = picked.text.length > 100 ? picked.text.slice(0, 99) + '…' : picked.text;
      var site = document.title.split('｜').pop();
      return { post: '『' + text + '』— ' + article.dataset.word + '｜' + site, url: article.dataset.url + fragment(picked.text) };
    };
    bar.addEventListener('click', function (e) {
      var b = e.target.closest('[data-pick]');
      var c = b && compose();
      if (!c) return;
      if (b.dataset.pick === 'x') {
        window.open('https://x.com/intent/post?text=' + encodeURIComponent(c.post) + '&url=' + encodeURIComponent(c.url), '_blank', 'noopener,width=600,height=500');
        track('share/quote' + location.pathname, '一文シェア：x');
      } else {
        var s2 = c.post + ' ' + c.url;
        var done = function () { toast('この一文をコピーしました'); };
        if (navigator.clipboard) navigator.clipboard.writeText(s2).then(done, function () { prompt('コピーしてください', s2); });
        else prompt('コピーしてください', s2);
        track('share/quote-copy' + location.pathname, '一文シェア：コピー');
      }
    });
  }

  // 単語ページの目次：いま読んでいる項目に印。右の目次は印がすべり、スマホの横の目次は自動で横に送る
  var wtoc = $('.wtoc'), mtoc = $('.mtoc');
  if (wtoc || mtoc) {
    var ids = $$('a', wtoc || mtoc).map(function (a) { return a.getAttribute('href').slice(1); });
    var secs = ids.map(function (id) { return document.getElementById(id); }).filter(Boolean);
    var ind = null;
    if (wtoc) {
      ind = document.createElement('i'); ind.className = 'wtoc-ind'; ind.setAttribute('aria-hidden', 'true');
      wtoc.appendChild(ind); wtoc.classList.add('live');
    }
    var curId = null;
    var moveInd = function () {
      var a = wtoc && $('a.on', wtoc);
      if (a && ind) ind.style.transform = 'translateY(' + a.offsetTop + 'px) scaleY(' + a.offsetHeight + ')';
    };
    var pickSec = function () {
      var y = innerHeight * 0.3, id = secs[0].id;
      secs.forEach(function (s3) { if (s3.getBoundingClientRect().top <= y) id = s3.id; });
      if (innerHeight + scrollY >= document.documentElement.scrollHeight - 4) id = secs[secs.length - 1].id;
      return id;
    };
    var updateToc = function (force) {
      if (!secs.length) return;
      var id = pickSec();
      if (id === curId && !force) return;
      curId = id;
      $$('.wtoc a, .mtoc a').forEach(function (a) {
        var on = a.getAttribute('href') === '#' + id;
        a.classList.toggle('on', on);
        if (on) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
      });
      moveInd();
      if (mtoc && mtoc.offsetParent) {
        var m = $('a.on', mtoc);
        if (m) mtoc.scrollTo({ left: m.offsetLeft - (mtoc.clientWidth - m.offsetWidth) / 2, behavior: reduce ? 'auto' : 'smooth' });
      }
    };
    var tick = false;
    addEventListener('scroll', function () { if (!tick) { tick = true; requestAnimationFrame(function () { tick = false; updateToc(); }); } }, { passive: true });
    addEventListener('resize', function () { updateToc(true); });
    updateToc(true);
  }

})();
