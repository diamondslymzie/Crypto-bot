// portfolio.js — Bitget Futures Portfolio
// Connects to Bitget Futures API via Railway backend

const BITGET_API = 'https://worker-production-49eb.up.railway.app';

async function loadPortfolio(){
  document.getElementById('positions-list').innerHTML = loading();
  try {
    const creds = APP.credentials;
    if(!creds.apiKey){
      document.getElementById('port-total').textContent = '$—';
      document.getElementById('port-margin').textContent = 'Connect API in Settings ⚙️';
      document.getElementById('positions-list').innerHTML = `
        <div style="text-align:center;padding:20px;color:var(--text2)">
          <div style="font-size:24px;margin-bottom:8px">🔑</div>
          <div style="font-size:13px;font-weight:700;margin-bottom:4px">API Not Connected</div>
          <div style="font-size:11px">Go to Settings ⚙️ and enter your Bitget API credentials</div>
        </div>`;
      updateStatusDot(false);
      return;
    }

    // Fetch futures account from Railway backend
    const res = await fetch(`${BITGET_API}/futures/account`, {
      headers: { 'X-API-KEY': creds.apiKey, 'X-API-SECRET': creds.apiSecret, 'X-PASSPHRASE': creds.passphrase }
    });
    const data = await res.json();

    if(!data.success){
      throw new Error(data.error||'Failed to load account');
    }

    const acc = data.account;
    const equity = parseFloat(acc.equity||0);
    const available = parseFloat(acc.available||0);
    const unrealized = parseFloat(acc.unrealizedPL||0);
    const realized = parseFloat(acc.realizedPL||0);
    const marginRatio = parseFloat(acc.marginRatio||0);

    document.getElementById('port-total').textContent = '$'+equity.toFixed(2);
    document.getElementById('port-margin').textContent = `Available Margin: $${available.toFixed(2)} USDT`;
    document.getElementById('port-pnl').textContent = `P&L: ${unrealized>=0?'+':''}$${unrealized.toFixed(2)}`;
    document.getElementById('port-pnl').style.color = unrealized>=0?'var(--green)':'var(--red)';
    document.getElementById('stat-equity').textContent = '$'+equity.toFixed(2);
    document.getElementById('stat-margin-ratio').textContent = marginRatio.toFixed(1)+'%';
    document.getElementById('stat-unrealized').textContent = (unrealized>=0?'+':'')+'$'+unrealized.toFixed(2);
    document.getElementById('stat-unrealized').style.color = unrealized>=0?'var(--green)':'var(--red)';
    document.getElementById('stat-realized').textContent = (realized>=0?'+':'')+'$'+realized.toFixed(2);
    document.getElementById('stat-realized').style.color = realized>=0?'var(--green)':'var(--red)';

    // Load open positions
    await loadPositions(creds);
    updateStatusDot(true);

  } catch(e){
    document.getElementById('port-total').textContent = '$—';
    document.getElementById('port-margin').textContent = 'Error loading account';
    document.getElementById('positions-list').innerHTML = `<div style="color:var(--red);text-align:center;padding:16px;font-size:12px">❌ ${e.message}</div>`;
    updateStatusDot(false);
  }
}

async function loadPositions(creds){
  try {
    const res = await fetch(`${BITGET_API}/futures/positions`, {
      headers: { 'X-API-KEY': creds.apiKey, 'X-API-SECRET': creds.apiSecret, 'X-PASSPHRASE': creds.passphrase }
    });
    const data = await res.json();

    if(!data.success || !data.positions.length){
      document.getElementById('positions-list').innerHTML = `
        <div style="text-align:center;padding:20px;color:var(--text2)">
          <div style="font-size:20px;margin-bottom:6px">📭</div>
          <div style="font-size:12px">No open positions</div>
        </div>`;
      return;
    }

    let html = '';
    data.positions.forEach(pos => {
      const side = pos.holdSide||pos.side||'long';
      const isLong = side.toLowerCase()==='long';
      const pnl = parseFloat(pos.unrealizedPL||pos.unrealizedPnl||0);
      const pnlColor = pnl>=0?'var(--green)':'var(--red)';
      const entryPrice = parseFloat(pos.openPriceAvg||pos.entryPrice||0);
      const markPrice = parseFloat(pos.markPrice||0);
      const size = parseFloat(pos.total||pos.positionAmt||0);
      const leverage = pos.leverage||'—';
      const margin = parseFloat(pos.margin||pos.isolatedMargin||0);
      const liqPrice = parseFloat(pos.liquidationPrice||0);

      html += `<div class="position-card">
        <div class="position-header">
          <div>
            <div class="position-pair">${pos.symbol||pos.instId}</div>
            <span class="badge ${isLong?'badge-green':'badge-red'}">${isLong?'📈 LONG':'📉 SHORT'}</span>
            <span class="badge badge-accent" style="margin-left:4px">${leverage}x</span>
          </div>
          <div style="text-align:right">
            <div style="font-size:14px;font-weight:800;font-family:var(--mono);color:${pnlColor}">${pnl>=0?'+':''}$${pnl.toFixed(2)}</div>
            <div style="font-size:9px;color:var(--text2)">Unrealized P&L</div>
          </div>
        </div>
        <div class="position-grid">
          <div class="position-item">
            <div class="position-val">${fmtPrice(entryPrice)}</div>
            <div class="position-lbl">ENTRY PRICE</div>
          </div>
          <div class="position-item">
            <div class="position-val">${fmtPrice(markPrice)}</div>
            <div class="position-lbl">MARK PRICE</div>
          </div>
          <div class="position-item">
            <div class="position-val">${size.toFixed(4)}</div>
            <div class="position-lbl">SIZE</div>
          </div>
          <div class="position-item">
            <div class="position-val">$${margin.toFixed(2)}</div>
            <div class="position-lbl">MARGIN</div>
          </div>
          <div class="position-item">
            <div class="position-val" style="color:var(--red)">${fmtPrice(liqPrice)}</div>
            <div class="position-lbl">LIQ PRICE</div>
          </div>
          <div class="position-item">
            <div class="position-val">${pnl>=0?'+':''}${((pnl/margin)*100).toFixed(1)}%</div>
            <div class="position-lbl">ROE</div>
          </div>
        </div>
        <button class="close-position-btn" onclick="closePosition('${pos.symbol||pos.instId}','${side}')">
          Close Position
        </button>
      </div>`;
    });
    document.getElementById('positions-list').innerHTML = html;

  } catch(e){
    document.getElementById('positions-list').innerHTML = `<div style="color:var(--text2);text-align:center;padding:16px;font-size:12px">Unable to load positions</div>`;
  }
}

async function closePosition(symbol, side){
  showConfirm(
    'Close Position',
    `Close your ${side.toUpperCase()} position on ${symbol}? This will execute a market order.`,
    async () => {
      try {
        const creds = APP.credentials;
        const res = await fetch(`${BITGET_API}/futures/close`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-KEY': creds.apiKey,
            'X-API-SECRET': creds.apiSecret,
            'X-PASSPHRASE': creds.passphrase
          },
          body: JSON.stringify({ symbol, side })
        });
        const data = await res.json();
        if(data.success){
          showToast(`✅ Position closed: ${symbol}`, 'var(--green)');
          setTimeout(loadPortfolio, 1500);
        } else {
          showToast(`❌ ${data.error}`, 'var(--red)');
        }
      } catch(e){
        showToast(`❌ Error: ${e.message}`, 'var(--red)');
      }
    }
  );
}
