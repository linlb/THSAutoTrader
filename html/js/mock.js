// 模拟推送注册
function registerPushMock(codes, callback) {
  // 模拟数据
  const mockData = {};
  codes.forEach((code) => {
    mockData[code] = {
      NEW: Math.random() * 100,
      ZHANGDIEFU: (Math.random() * 20 - 10).toFixed(2),
      ZHANGSHU: (Math.random() * 10 - 5).toFixed(2),
    };
  });

  // 模拟定时推送
  const intervalId = setInterval(() => {
    codes.forEach((code) => {
      // 随机更新数据
      mockData[code].NEW = Math.random() * 100;
      mockData[code].ZHANGDIEFU = (Math.random() * 20 - 10).toFixed(2);
      mockData[code].ZHANGSHU = (Math.random() * 10 - 5).toFixed(2);
    });

    if (callback) {
      callback(mockData);
    }
  }, 3000); // 每3秒推送一次

  // 返回intervalId作为sessionId,用于后续清除定时器
  return intervalId;
}
