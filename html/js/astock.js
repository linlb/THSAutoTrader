// 从localStorage中获取股票池，如果没有则初始化为空数组
let stockPool = JSON.parse(localStorage.getItem('stockPool')) || [];

// 在文件顶部添加一个全局变量来记录已下单的股票
let orderedStocksSell = new Set();
let orderedStocksBuy = new Set(); // 新增：记录已触发买入的股票

// 保存股票池到localStorage
function saveStockPool() {
  localStorage.setItem('stockPool', JSON.stringify(stockPool));
}

function addStock() {
  const code = document.getElementById('new-stock-code').value;

  if (code) {
    stockPool.push({ code });
    renderStockPool();
    document.getElementById('new-stock-code').value = '';
    saveStockPool(); // 保存到localStorage
  }
}

function deleteStock(index) {
  stockPool.splice(index, 1);
  renderStockPool();
  saveStockPool(); // 保存到localStorage
}

function renderStockPool() {
  const tbody = document.querySelector('#stock-pool-table tbody');
  tbody.innerHTML = stockPool
    .map(
      (stock, index) => `
    <tr id="stock-row-${stock.code}">
      <td onclick="clickStock('${stock.code}')">${stock.code}<br>${
        stock.name || '--'
      }</td>
      <td class="zhangdiefu">--</td>
      <td class="zhangshu">--</td>
      <td class="action-buttons">
        <button class="delete-btn" onclick="deleteStock(${index})">删除</button>
      </td>
    </tr>
  `
    )
    .join('');
}

// 更新股票数据
function updateStockData(stockData) {
  for (const code in stockData) {
    const row = document.querySelector(`#stock-row-${code}`);
    if (row) {
      const data = stockData[code];
      const zhangdiefuCell = row.querySelector('.zhangdiefu');
      const zhangshuCell = row.querySelector('.zhangshu');

      // 更新涨跌幅
      if (data.ZHANGDIEFU) {
        zhangdiefuCell.textContent = data.ZHANGDIEFU;
        zhangdiefuCell.style.color = data.ZHANGDIEFU >= 0 ? 'red' : 'green';
      } else {
        zhangdiefuCell.textContent = '--';
        zhangdiefuCell.style.color = 'black';
      }

      // 更新涨速
      if (data.ZHANGSHU) {
        zhangshuCell.textContent = data.ZHANGSHU;
        zhangshuCell.style.color = data.ZHANGSHU >= 0 ? 'red' : 'green';
      } else {
        zhangshuCell.textContent = '--';
        zhangshuCell.style.color = 'black';
      }
    }
  }
}

/**
 * 买入策略
 * @param {Object} stockData 股票数据
 */
function executeStrategy(stockData) {
  // 获取设置的时间
  const startTime = document.getElementById('buy-start-time').value;
  const endTime = document.getElementById('buy-end-time').value;
  // 获取设置的涨速
  const minRiseSpeed =
    parseFloat(document.getElementById('min-rise-speed').value) || 2;
  // 获取设置的当前涨幅
  const minCurrentRise =
    parseFloat(document.getElementById('min-current-rise').value) || 9;

  // 获取当前时间
  const now = new Date();
  const currentTime = now.toTimeString().slice(0, 5); // 格式化为HH:MM

  // 判断是否在设置的时间范围内
  if (
    startTime &&
    endTime &&
    (currentTime < startTime || currentTime > endTime)
  ) {
    return;
  }
  let orderIndex = 0;

  // 遍历股票数据
  for (const code in stockData) {
    const data = stockData[code];
    if (data.ZHANGSHU > minRiseSpeed) {
      clickStock(code);
    }
    // 涨速大于等于设置值且当前涨幅大于等于设置值时执行买入
    if (
      data.ZHANGSHU >= minRiseSpeed &&
      data.ZHANGDIEFU >= minCurrentRise &&
      !orderedStocksBuy.has(code)
    ) {
      // 调用买入协议
      placeOrder(0, code, (res) => {
        // 调用通知接口
        res && notifyOrder(code, 0);
      });
      orderedStocksBuy.add(code); // 新增：将股票代码加入已买入集合
    }
  }
}

/**
 * 卖出策略
 * @param {Array} stockData 股票数据
 */
async function sellStrategy(codes) {
  // 获取分时数据
  const timeData = await getTimeData(codes);
  codes.forEach((code, index) => {
    console.log('debug', code);
    // 检查是否已经下过单
    if (
      !orderedStocksSell.has(code) &&
      (isSellPoint(timeData[code]) || isTopSellPoint(timeData[code]))
    ) {
      setTimeout(() => {
        placeOrder(1, code);
        // 调用通知接口
        notifyOrder(code, 1);
        // 将股票代码加入已下单集合
        orderedStocksSell.add(code);
      }, index * 3000); // 每个操作间隔3秒
    }
  });
}
/**
 * 当涨速达到要求时，先点击对应的股票，进入分时
 */
function clickStock(code) {
  jumpToQuote(
    code,
    stockPool.map((s) => s.code)
  );
}

async function run() {
  // 清空已下单记录
  orderedStocksSell.clear();
  orderedStocksBuy.clear(); // 新增：清空已买入记录
  if (window['sessionId']) {
    unregisterPush();
  }
  clearLog();
  // 获取股票代码数组
  const codes = stockPool.map((stock) => stock.code);
  // 获取当前持仓股票代码
  // const holdStocks = await getHoldStocks();
  customLog('监控中的股票: ' + codes.join(', '));
  // 调用registerPush方法并保存sessionId
  if (codes.length > 0) {
    window['sessionId'] = registerPush(codes, (res) => {
      // 更新表格数据
      updateStockData(res);
      // 执行买入策略
      executeStrategy(res);
    });
  } else {
    customLog('股票池为空，无法执行推送注册');
  }
  // if (holdStocks.length > 0) {
  //   sellStrategy(holdStocks);
  // }
}

/**
 * 判断当前分时是否为卖点（改进版）
 * @param {Object} timeData 分时数据
 * @returns {Boolean} 是否为卖点
 */
function isSellPoint(timeData) {
  const timeKeys = Object.keys(timeData).sort();
  const last15Minutes = timeKeys.slice(-15); // 获取最近15分钟数据

  // 初始化统计变量
  let priceTrend = 0;
  let volumeTrend = 0;
  let belowAvgCount = 0;
  let maxPrice = -Infinity;
  let minPrice = Infinity;

  for (let i = 1; i < last15Minutes.length; i++) {
    const prev = timeData[last15Minutes[i - 1]];
    const curr = timeData[last15Minutes[i]];

    // 价格趋势
    priceTrend += curr.NEW - prev.NEW;

    // 成交量趋势
    volumeTrend += curr.VOL - prev.VOL;

    // 价格与均价关系
    if (curr.NEW < curr.JUNJIA) {
      belowAvgCount++;
    }

    // 记录最高最低价
    maxPrice = Math.max(maxPrice, curr.NEW);
    minPrice = Math.min(minPrice, curr.NEW);
  }

  // 计算技术指标
  const priceRange = maxPrice - minPrice;
  const currentPrice = timeData[last15Minutes[last15Minutes.length - 1]].NEW;
  const avgPrice = timeData[last15Minutes[last15Minutes.length - 1]].JUNJIA;

  // console.log(priceTrend, volumeTrend, belowAvgCount, maxPrice, minPrice);
  // 卖点判断条件（改进版）：
  // 1. 价格趋势：15分钟内总体呈下跌趋势
  // 2. 成交量趋势：15分钟内成交量总体放大
  // 3. 价格位置：当前价格低于均价
  // 4. 价格波动：当前价格接近15分钟最低价
  // 5. 持续时间：价格低于均价的时间超过50%
  return (
    priceTrend < 0 &&
    volumeTrend > 0 &&
    currentPrice < avgPrice &&
    currentPrice - minPrice < priceRange * 0.3 &&
    belowAvgCount > last15Minutes.length * 0.5
  );
}

/**
 * 逃顶卖点判断
 * @param {Object} timeData 分时数据
 * @returns {Boolean} 是否为逃顶卖点
 */
function isTopSellPoint(timeData) {
  const timeKeys = Object.keys(timeData).sort();

  let maxPrice = -Infinity;
  let maxVolume = -Infinity;

  // 遍历全部数据，记录最高价和最大成交量
  for (let i = 0; i < timeKeys.length; i++) {
    const curr = timeData[timeKeys[i]];
    maxPrice = Math.max(maxPrice, curr.NEW);
    maxVolume = Math.max(maxVolume, curr.VOL);
  }

  // 获取当前价格和成交量
  const currentPrice = timeData[timeKeys[timeKeys.length - 1]].NEW;
  const currentVolume = timeData[timeKeys[timeKeys.length - 1]].VOL;

  // 量价背离判断条件：
  // 1. 当前价格接近或达到最高价
  // 2. 当前成交量未达到最大成交量
  return currentPrice >= maxPrice && currentVolume < maxVolume;
}

/**
 * 打印卖点信息
 * 调试使用
 * @param {Object} timeData 分时数据
 */
function printSellPoints(timeData) {
  console.log('开始打印卖点信息');
  const timeKeys = Object.keys(timeData).sort();

  // 遍历所有时间点，每次取15分钟窗口
  for (let i = 14; i < timeKeys.length; i++) {
    const startIndex = i - 14;
    const endIndex = i;

    // 获取15分钟窗口数据
    const windowData = {};
    for (let j = startIndex; j <= endIndex; j++) {
      const time = timeKeys[j];
      windowData[time] = timeData[time];
    }

    // 判断是否为止损卖点
    if (isSellPoint(windowData)) {
      const currentTime = timeKeys[endIndex];
      console.log(
        `止损卖点 - 时间: ${currentTime}, 价格: ${timeData[currentTime].NEW}`
      );
    }

    // 判断是否为逃顶卖点
    if (isTopSellPoint(windowData)) {
      const currentTime = timeKeys[endIndex];
      console.log(
        `逃顶卖点 - 时间: ${currentTime}, 价格: ${timeData[currentTime].NEW}`
      );
    }
  }
}

// 页面加载时读取保存的接口地址
window.addEventListener('load', () => {
  const savedUrl = localStorage.getItem('stockPoolUrl');
  if (savedUrl) {
    document.getElementById('stock-pool-url').value = savedUrl;
  }
});

async function updateStockPool() {
  const url = document.getElementById('stock-pool-url').value;
  if (!url) {
    alert('请输入股票池接口地址');
    return;
  }

  // 保存接口地址到localStorage
  localStorage.setItem('stockPoolUrl', url);

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result = await response.json();

    // 检查接口返回状态
    if (result.code === 0 && result.data && Array.isArray(result.data)) {
      // 从data字段中提取股票代码
      stockPool = result.data.map((item) => ({
        code: item.code,
        name: item.name,
      }));
      renderStockPool();
      saveStockPool();
      console.log('股票池更新成功');
    } else {
      throw new Error('接口返回数据格式不正确');
    }
  } catch (error) {
    console.error('更新股票池失败:', error);
  }
}
function clickStock(code) {
  jumpToQuote(
    code,
    stockPool.map((s) => s.code)
  );
}
// 页面加载时自动渲染股票池
renderStockPool();
