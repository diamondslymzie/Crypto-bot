// trade.js — Bitget Futures Trading
// Handles long/short futures orders with leverage

const POPULAR_PAIRS = [
  'BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BNBUSDT',
  'TONUSDT','DOGEUSDT','AVAXUSDT','ADAUSDT','DOTUSDT',
  'MATICUSDT','LINKUSDT','UNIUSDT','ATOMUSDT','LTCUSDT',
  'NEARUSDT','FILUSDT','AAVEUSDT','APTUSDT','ARBUSDT',
  'OPUSDT','INJUSDT','SUIUSDT','SEIUSDT','TIAUSDT'
];

let tradingViewWidget = null;
let priceSocket = null;
let currentLivePrice = 0;

function initTrade(){
  const pair = APP.currentPair || 'BTCUSDT';
  document.getElementById('trade-pair').value = pair;
  document.getElementById('order-pair').textContent = pair;
  loadTradingView(pair);
  subscribePrice(pair);
  updateOrderSummary();
}

// ── TRADINGVIEW CHART ─────────────────────────────────────────────────
function loadTradingView(symbol){
  const container = document.getElementById('tradingview-container');
  const tvSymbol = 'BITGET:'+symbol.replace('USDT','')+'USDT.P';
  container.innerHTML = `
    <iframe
      src="https://s.tradingview.com/widgetembed/?frameElementId=tv_chart&symbol=${tvSymbol}&interval=15&theme=dark&style=1&locale=en&toolbar_bg=%23080a0f&enable_publishing=false&hide_top_toolbar=false&hide_legend=false&save_image=false&backgroundColor=%23080a0f&gridColor=%231e2535&hide_volume=false"
      style="width:100%;height:220px;border:none;border-radius:8px"
      allowtransparency="true"
      scrolling="no"
      allowfullscreen>
    </iframe>`;
}

// ── LIVE PRICE VIA BITGET WEBSOCKET ───────────────────────────────────
function subscribePrice(symbol){
  if(priceSocket) priceSocket.close();
  try {
    priceSocket = new WebSocket('wss://ws.bitget.com/v2/ws/public');
    priceSocket.onopen = () => {
      priceSocket.send(JSON.stringify({
        op: 'subscribe',
        args: [{ instType: 'USDT-FUTURES', channel: 'ticker', instId: symbol }]
      }));
    };
    priceSocket.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if(msg.data && msg.data[0]){
        const price = parseFloat(msg.data[0].lastPr||msg.data[0].last||0);
        if(price > 0){
          currentLivePrice = price;
          document.getElementById('trade-live-price').textContent = fmtPrice(price);
          document.getElementById('order-price').textContent = fmtPrice(price);
          updatePositionSize();
        }
      }
    };
    priceSocket.onerror = () => {
      fetchPriceFallback(symbol);
    };
  } catch(e){
    fetchPriceFallback(symbol);
  }
}

async function fetchPriceFallback(symbol){
  try {
    const base = symbol.replace('USDT','').toLowerCase();
    const coinIds = {
      btc:'bitcoin',eth:'ethereum',sol:'solana',xrp:'ripple',
      bnb:'binancecoin',doge:'dogecoin',avax:'avalanche-2',
      ada:'cardano',dot:'polkadot',matic:'matic-network',ton:'the-open-network'
    };
    const id = coinIds[base]||base;
    const res = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${id}&vs_currencies=usd`);
    const data = await res.json();
    const price = data[id]?.usd||0;
    if(price > 0){
      currentLivePrice = price;
      document.getElementById('trade-live-price').textContent = fmtPrice(price);
      document.getElementById('order-price').textContent = fmtPrice(price);
      updatePositionSize();
    }
  } catch(e){}
}

// ── PAIR SEARCH ───────────────────────────────────────────────────────
function searchPair(query){
  const q = query.toUpperCase().replace('/','').replace('-','');
  if(!q){
    document.getElementById('pair-suggestions').style.display = 'none';
    return;
  }
  const matches = POPULAR_PAIRS.filter(p=>p.includes(q)).slice(0,6);
  if(!matches.length){
    document.getElementById('pair-suggestions').style.display = 'none';
    return;
  }
  const html = matches.map(p=>`
    <div onclick="selectPair('${p}')" style="padding:10px 14px;cursor:pointer;font-family:var(--mono);font-size:13px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center">
      <span style="font-weight:700">${p.replace('USDT','')}<span style="color:var(--text2);font-size:10px">/USDT</span></span>
      <span class="badge badge-accent">FUTURES</span>
    </div>`).join('');
  document.getElementById('pair-suggestions').innerHTML = html;
  document.getElementById('pair-suggestions').style.display = 'block';
}

function selectPair(pair){
  APP.currentPair = pair;
  document.getElementById('trade-pair').value = pair;
  document.getElementById('order-pair').textContent = pair;
  document.getElementById('pair-suggestions').style.display = 'none';
  loadTradingView(pair);
  subscribePrice(pair);
  updateExecuteBtn();
}

// ── DIRECTION ─────────────────────────────────────────────────────────
function setDirection(dir){
  APP.direction = dir;
  const longBtn = document.getElementById('long-tab');
  const shortBtn = document.getElementById('short-tab');
  const execBtn = document.getElementById('execute-btn');
  if(dir === 'long'){
    longBtn.className = 'btn-primary btn-long';
    longBtn.style = 'flex:1;padding:10px;font-size:13px';
    shortBtn.className = 'btn-primary';
    shortBtn.style = 'flex:1;padding:10px;font-size:13px;background:var(--card2);color:var(--text2);border:1px solid var(--border)';
    execBtn.className = 'btn-primary btn-long';
    execBtn.textContent = '📈 OPEN LONG';
    document.getElementById('order-direction').textContent = 'LONG';
    document.getElementById('order-direction').style.color = 'var(--green)';
  } else {
    shortBtn.className = 'btn-primary btn-short';
    shortBtn.style = 'flex:1;padding:10px;font-size:13px';
    longBtn.className = 'btn-primary';
    longBtn.style = 'flex:1;padding:10px;font-size:13px;background:var(--card2);color:var(--text2);border:1px solid var(--border)';
    execBtn.className = 'btn-primary btn-short';
    execBtn.textContent = '📉 OPEN SHORT';
    document.getElementById('order-direction').textContent = 'SHORT';
    document.getElementById('order-direction').style.color = 'var(--red)';
  }
}

// ── LEVERAGE ──────────────────────────────────────────────────────────
function updateLeverage(val){
  APP.leverage = parseInt(val);
  document.getElementById('leverage-display').textContent = val+'x';
  document.getElementById('order-leverage').textContent = val+'x';
  updatePositionSize();
}

// ── AMOUNT PRESETS ────────────────────────────────────────────────────
function setTradeAmount(val){
  document.getElementById('trade-amount').value = val;
  updatePositionSize();
}

// ── POSITION SIZE CALC ────────────────────────────────────────────────
function updatePositionSize(){
  const amount = parseFloat(document.getElementById('trade-amount').value)||0;
  const leverage = APP.leverage||10;
  const price = currentLivePrice||0;
  if(price > 0 && amount > 0){
    const notional = amount * leverage;
    const qty = notional / price;
    document.getElementById('order-size').textContent = `${qty.toFixed(4)} (${fmt(notional)} notional)`;
  }
}

document.getElementById('trade-amount').addEventListener('input', updatePositionSize);

function updateOrderSummary(){
  document.getElementById('order-pair').textContent = APP.currentPair||'—';
  document.getElementById('order-leverage').textContent = (APP.leverage||10)+'x';
}

function updateExecuteBtn(){
  const btn = document.getElementById('execute-btn');
  const dir = APP.direction||'long';
  btn.textContent = dir==='long'?'📈 OPEN LONG':'📉 OPEN SHORT';
}

// ── CONFIRM TRADE ─────────────────────────────────────────────────────
function confirmTrade(){
  const creds = APP.credentials;
  if(!creds.apiKey){
    showToast('⚠️ Connect Bitget API in Settings first','var(--yellow)');
    return;
  }
  const pair = APP.currentPair||'BTCUSDT';
  const dir = APP.direction||'long';
  const lev = APP.leverage||10;
  const amount = parseFloat(document.getElementById('trade-amount').value)||0;
  if(amount < 1){
    showToast('⚠️ Minimum $1 USDT','var(--yellow)');
    return;
  }
  const notional = amount * lev;
  showConfirm(
    `${dir==='long'?'📈 LONG':'📉 SHORT'} ${pair}`,
    `Open a ${dir.toUpperCase()} position on ${pair}\n\nMargin: $${amount} USDT\nLeverage: ${lev}x\nNotional: $${notional.toFixed(2)}\n\n⚠️ This uses real USDT from your Bitget account.`,
    executeTrade
  );
}

// ── EXECUTE TRADE ─────────────────────────────────────────────────────
async function executeTrade(){
  const creds = APP.credentials;
  const pair = APP.currentPair||'BTCUSDT';
  const dir = APP.direction||'long';
  const lev = APP.leverage||10;
  const amount = parseFloat(document.getElementById('trade-amount').value)||0;

  showToast('⏳ Placing order...','var(--accent)');

  try {
    const res = await fetch(`${BITGET_API}/futures/order`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': creds.apiKey,
        'X-API-SECRET': creds.apiSecret,
        'X-PASSPHRASE': creds.passphrase
      },
      body: JSON.stringify({
        symbol: pair,
        side: dir,
        leverage: lev,
        amount: amount,
        orderType: 'market'
      })
    });
    const data = await res.json();
    if(data.success){
      showToast(`✅ ${dir.toUpperCase()} opened on ${pair}`,'var(--green)');
      if(tg) tg.sendData(JSON.stringify({action:'futures_order',pair,dir,lev,amount}));
    } else {
      showToast(`❌ ${data.error}`,'var(--red)');
    }
  } catch(e){
    showToast(`❌ Error: ${e.message}`,'var(--red)');
  }
}
