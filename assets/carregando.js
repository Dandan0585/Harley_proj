/*
 * Spinner de carregamento global (Harley Store).
 *
 * Ao clicar em qualquer botão ou link, se o clique disparar uma ação no
 * servidor, o botão mostra um círculo girando até a ação terminar. Se o
 * botão sumir da tela (ex.: diálogo que fecha, troca de página), aparece
 * um spinner redondo no centro da tela.
 *
 * Como sabe que "terminou"? O Reflex conversa com o servidor por websocket:
 * cada ação enviada é uma mensagem `42/_event,["event",...]` e o servidor responde
 * com `"final": true` quando acaba. Aqui só observamos essas mensagens —
 * nada precisa mudar nas telas, e botões novos já ganham o spinner.
 *
 * Carregado em harley_store.py (head_components), antes do app conectar.
 */
(function () {
  var JANELA_CLIQUE_MS = 1200; // ação precisa começar até 1,2 s após o clique
  var ATRASO_OVERLAY_MS = 250; // evita "piscar" em ações instantâneas
  var LIMITE_MS = 30000;       // trava de segurança

  // mensagem de evento do socket.io, com ou sem namespace (o Reflex usa
  // "/_event"): 42["event",...]  ou  42/_event,["event",...]
  var EH_EVENTO = /^42(\/[^,]*,)?\d*\["event"/;

  var pendentes = 0;
  var ultimoClique = { el: null, quando: 0 };
  var ativo = null;
  var timerOverlay = null;
  var timerLimite = null;

  var overlay = document.createElement("div");
  overlay.id = "hs-overlay-carregando";
  overlay.innerHTML = '<div class="hs-roda"></div>';

  function mostrar() {
    var el = ultimoClique.el;
    if (!el || Date.now() - ultimoClique.quando > JANELA_CLIQUE_MS) return;
    ultimoClique.el = null;
    ativo = el;
    if (el.tagName === "BUTTON") el.classList.add("hs-carregando");
    clearTimeout(timerOverlay);
    timerOverlay = setTimeout(function () {
      // botão saiu da tela (ou era link): usa o spinner central
      if (pendentes > 0 && (!ativo || !ativo.isConnected || ativo.tagName !== "BUTTON")) {
        if (!overlay.isConnected) document.body.appendChild(overlay);
        overlay.classList.add("hs-visivel");
      }
    }, ATRASO_OVERLAY_MS);
    clearTimeout(timerLimite);
    timerLimite = setTimeout(esconder, LIMITE_MS);
  }

  function esconder() {
    pendentes = 0;
    clearTimeout(timerOverlay);
    clearTimeout(timerLimite);
    if (ativo) ativo.classList.remove("hs-carregando");
    ativo = null;
    overlay.classList.remove("hs-visivel");
  }

  document.addEventListener(
    "click",
    function (e) {
      var el = e.target.closest && e.target.closest("button, a[href]");
      if (el && !el.disabled) ultimoClique = { el: el, quando: Date.now() };
    },
    true
  );

  var WS = window.WebSocket;
  function WSComSpinner(url, protocolos) {
    var ws = protocolos === undefined ? new WS(url) : new WS(url, protocolos);
    var enviar = ws.send;
    ws.send = function (dados) {
      if (typeof dados === "string" && EH_EVENTO.test(dados)) {
        pendentes++;
        mostrar();
      }
      return enviar.apply(ws, arguments);
    };
    ws.addEventListener("message", function (m) {
      if (typeof m.data !== "string" || !EH_EVENTO.test(m.data)) return;
      if (/\\?"final\\?"\s*:\s*true/.test(m.data)) {
        pendentes = Math.max(0, pendentes - 1);
        if (pendentes === 0) esconder();
      }
    });
    ws.addEventListener("close", esconder);
    return ws;
  }
  WSComSpinner.prototype = WS.prototype;
  ["CONNECTING", "OPEN", "CLOSING", "CLOSED"].forEach(function (k) {
    WSComSpinner[k] = WS[k];
  });
  window.WebSocket = WSComSpinner;
})();
