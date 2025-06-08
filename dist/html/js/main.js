function executeAnalysis() {
  const executeBtn = document.getElementById('execute-btn');
  const unregisterBtn = document.getElementById('unregister-btn');
  const cbCodeInput = document.getElementById('cb-code');
  const stockCodeInput = document.getElementById('stock-code');

  // 设置按钮状态
  executeBtn.disabled = true;
  unregisterBtn.disabled = false;

  // 保存输入值到 localStorage
  localStorage.setItem('cbCode', cbCodeInput.value);
  localStorage.setItem('stockCode', stockCodeInput.value);

  // 清空之前的日志
  const logOutput = document.getElementById('log-output');
  logOutput.textContent = '';

  // 这里可以添加你的分析逻辑
  customLog(`开始分析...`);
  customLog(`可转债代码: ${cbCodeInput.value}`);
  customLog(`正股代码: ${stockCodeInput.value}`);
  customLog(`分析完成！`);
  // 将输入的代码转换为数组
  const codes = [cbCodeInput.value, stockCodeInput.value].filter(
    (code) => code
  );

  // 注册推送
  if (codes.length > 0) {
    window['sessionId'] = registerPush(codes);
    customLog(`已注册推送，监听代码: ${codes.join(', ')}`);
  } else {
    customLog(`请输入至少一个有效的代码`);
  }
}

// 注册推送
function registerPush(codes, callback) {
  var quoteSessionId = window.API.createSessionId('Quote');
  window.API.use({
    method: 'Quote.registerPush',
    data: { code: codes.join(',') },
    sessionId: quoteSessionId,
    persistent: true,
    callbackName: 'onready',
    success: function (data) {
      window.API.use({
        method: 'Quote.getData2',
        data: {
          code: codes.join(','),
          type: ['NEW', 'ZHANGDIEFU', 'ZHANGSHU'],
          period: 'now',
          mode: 'after',
        },
        success: function (data) {
          const stockData = JSON.parse(data);
          callback(stockData);
        },
      });
    },
  });
  return quoteSessionId;
}

// 取消推送
function unregisterPush() {
  window.API.use({
    method: 'Quote.unregisterPush',
    sessionId: window['sessionId'],
    success: function (data) {
      window['sessionId'] = null;
      // 通知
      customLog('取消监听成功');
    },
  });
}

// 新增下单功能,cmd:XD_MAIRU,XD_MAICHU
function placeOrder(cmdStatus, stockCode, callback = null) {
  // 这两个参数好像失效了
  const price = '';
  const amount = '';
  const strInfo = `<?xml version="1.0" encoding="GB2312"?><RealTime StockCode="${stockCode}" Market="33"><Bid><Price Selected="1">${price}</Price><Amount>${amount}</Amount></Bid></RealTime>`;
  const info =
    'wt_startup=wt_startup=\r\nrealtime=' +
    window.btoa(unescape(encodeURIComponent(strInfo)));

  window.API.use({
    method: 'XdMgr.fastCallXiadan',
    data: {
      cmd: cmdStatus == 0 ? 'XD_MAIRU' : 'XD_MAICHU',
      code: stockCode,
      amount: amount,
      info: info,
      default: false,
      hide: false,
      select: true,
    },
    success: function (data) {
      console.log('下单结果:', data);
      callback && callback(data);
    },
  });
}

function showHoldStocks() {
  const table = document.getElementById('hold-stocks-table');
  if (!table) {
    console.error('未找到持仓表格');
    return;
  }

  // 清空表格（保留表头）
  const tbody = table.querySelector('tbody');
  tbody.innerHTML = '';

  getHoldStocks().then((stocks) => {
    if (stocks && stocks.length > 0) {
      // 生成表格行
      stocks.forEach((item) => {
        const row = document.createElement('tr');
        row.id = `hold-row-${item['证券代码']}`;
        row.innerHTML = `
          <td>${item['证券代码']}</td>
          <td>${item['证券名称']}</td>
          <td>${item['可用余额']}</td>
          <td>${item['成本价']}</td>
          <td>${item['盈亏']}</td>
          <td>${item['盈亏比例(%)']}</td>
          <td class="hold-zhangdiefu">--</td>
          <td class="hold-zhangshu">--</td>
          <td class="action-buttons">
            <button class="delete-btn" onclick="sellStock('${item['证券代码']}')">卖出</button>
          </td>
        `;
        tbody.appendChild(row);
      });

      // 添加实时数据更新（需要与股票池同步）
      setTimeout(() => updateHoldStockData(), 100);
    } else {
      // 显示无持仓提示
      const row = document.createElement('tr');
      row.innerHTML =
        '<td colspan="9" style="text-align:center">当前没有持仓</td>';
      tbody.appendChild(row);
    }
  });
}

// 新增持仓数据更新方法
function updateHoldStockData() {
  const codes = Array.from(
    document.querySelectorAll('#hold-stocks-table td:first-child')
  ).map((td) => td.textContent);

  if (codes.length > 0) {
    window.API.use({
      method: 'Quote.getData2',
      data: {
        code: codes.join(','),
        type: ['ZHANGDIEFU', 'ZHANGSHU'],
      },
      success: function (data) {
        const stockData = JSON.parse(data);
        for (const code in stockData) {
          const row = document.querySelector(`#hold-row-${code}`);
          if (row) {
            row.querySelector('.hold-zhangdiefu').textContent =
              stockData[code].ZHANGDIEFU || '--';
            row.querySelector('.hold-zhangshu').textContent =
              stockData[code].ZHANGSHU || '--';
          }
        }
      },
    });
  }
}

// 获取当前持仓股票代码（支持async/await）
async function getHoldStocks() {
  try {
    const response = await fetch('http://localhost:5000/position');
    const result = await response.json();

    if (result.status === 'success' && result.data) {
      // 提取所有证券代码
      return result.data;
    }
    return [];
  } catch (error) {
    console.error('获取持仓失败:', error);
    return [];
  }
}

/**
 * 通知订单接口
 * @param {string} code 股票代码
 * @param {number} status 订单状态 (0: 买入, 1: 卖出)
 */
function notifyOrder(code, status) {
  return fetch(
    `http://localhost:5000/notify_order?code=${code}&status=${status}`
  )
    .then((response) => response.json())
    .then((result) => {
      customLog(`订单${status === 0 ? '买入' : '卖出'}${code}结果:`, result);
    })
    .catch((error) => {
      customLog(`订单${status === 0 ? '买入' : '卖出'}${code}失败:`, error);
    });
}

// 自定义log函数
function customLog(message) {
  const logOutput = document.getElementById('log-output');
  if (logOutput) {
    const p = document.createElement('p');
    p.textContent = message;
    logOutput.appendChild(p);
  }
  console.log(message); // 保留原始console.log
}

// 清空日志框
function clearLog() {
  const logOutput = document.getElementById('log-output');
  if (logOutput) {
    logOutput.innerHTML = '';
  }
}

/**
 * 获取分时数据
 * @param {string} code 股票代码
 * @returns {Promise<Array>} 分时数据
 */
async function getTimeData(code) {
  // 创建Util对象
  window.external.createObject('Util');
  // 获取当前日期 20250207的格式
  // const today = new Date().toISOString().split('T')[0].replace(/-/g, '');
  const today = '20250207';
  // 获取分时数据
  const timeData = await new Promise((resolve, reject) => {
    window.API.use({
      method: 'Quote.request',
      data: {
        code: [code],
        type: ['NEW', 'VOL', 'JUNJIA'],
        period: 'min',
        begin: today,
        end: today,
        timeFmt: 1,
      },
      callbackName: 'onready',
      success: () => {
        window.API.use({
          method: 'Quote.getData2',
          data: {
            type: ['NEW', 'VOL', 'JUNJIA'],
            code: [code],
            period: 'min',
            time: { begin: today, end: today, timeFmt: 1 },
            mode: 'after',
            timeStamp: 0,
          },
          success: resolve,
          error: reject,
        });
      },
      error: reject,
    });
  });

  return JSON.parse(timeData);
}

/**
 * 跳转到分时图
 * @param {string} code 代码
 * @param {string} stockCode 跟踪代码
 */
function jumpToQuote(code, stockCode) {
  API.use({
    method: 'Quote.syncStockList',
    data: {
      id: 379, //379为分时图，65为k线
      code: code,
      // market: '33',
      period: '8192',
      stocklist: stockCode.join('|'),
    },
    success: function (result) {},
  });
}
