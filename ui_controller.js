 // ui_controller.js

document.addEventListener('DOMContentLoaded', () => {
    // 获取DOM元素
    const tickerInput = document.getElementById('tickerInput');
    const analyzeButton = document.getElementById('analyzeButton');

    const historicalAnalysisView = document.getElementById('historicalAnalysisView');
    const stockNameEl = document.getElementById('stockName');
    const stockTickerEl = document.getElementById('stockTicker');
    const expNameEl = document.getElementById('expName');
    const analysisPeriodEl = document.getElementById('analysisPeriod');
    const overallTrendSummaryEl = document.getElementById('overallTrendSummary');
    const dailyAnalysisTableBody = document.getElementById('dailyAnalysisTableBody');
    const totalDaysAnalyzedEl = document.getElementById('totalDaysAnalyzed');
    const bullishDaysEl = document.getElementById('bullishDays');
    const bearishDaysEl = document.getElementById('bearishDays');
    const neutralDaysEl = document.getElementById('neutralDays');
    const priceChartPlaceholder = document.getElementById('priceChartPlaceholder'); // 图表占位符

    const realtimeMonitoringView = document.getElementById('realtimeMonitoringView');
    const realtimeStockTickerEl = document.getElementById('realtimeStockTicker');
    const realtimeCurrentPriceEl = document.getElementById('realtimeCurrentPrice');
    const realtimeSignalArea = document.getElementById('realtimeSignalArea');
    const realtimeSignalTextEl = document.getElementById('realtimeSignalText');
    const realtimeSignalReasonEl = document.getElementById('realtimeSignalReason');

    const loadingMessage = document.getElementById('loadingMessage');
    const errorMessage = document.getElementById('errorMessage');
    const errorTextEl = document.getElementById('errorText');

    // --- 事件监听 --- 
    analyzeButton.addEventListener('click', handleAnalyzeClick);

    // --- 事件处理函数 --- 
    async function handleAnalyzeClick() {
        const ticker = tickerInput.value.trim();
        if (!ticker) {
            showError("请输入股票代码。");
            return;
        }

        // 临时的实验名称和日期，实际应用中可能需要用户输入或从其他地方获取
        const expName = "ollama-test"; // 或者您常用的实验名
        const startDate = "2023-01-01"; // 示例开始日期
        const endDate = "2023-03-31";   // 示例结束日期

        showLoading(true);
        hideError();
        historicalAnalysisView.style.display = 'none';
        realtimeMonitoringView.style.display = 'none';

        try {
            // 调用API客户端获取历史数据
            const analysisData = await fetchHistoricalAnalysis(ticker, expName, startDate, endDate);
            console.log("Received historical data:", analysisData);

            if (analysisData && !analysisData.error) {
                updateHistoricalView(analysisData);
                historicalAnalysisView.style.display = 'block';
                // 可以在这里添加启动实时监控的逻辑
                // startRealtimeMonitoring(ticker, expName);
            } else {
                showError(analysisData.error || "未能获取有效的分析数据。");
            }
        } catch (error) {
            console.error("Error in handleAnalyzeClick:", error);
            showError(error.message || "请求分析数据时发生未知错误。");
        } finally {
            showLoading(false);
        }
    }

    // --- UI 更新函数 --- 
    function updateHistoricalView(data) {
        // 填充股票基本信息
        // 假设后端返回的数据结构与 analysis_service.py 中的 get_historical_summary 对应
        stockTickerEl.textContent = data.ticker || '-';
        stockNameEl.textContent = data.ticker || '-'; // 实际应用中，股票名称可能需要另外查询或包含在数据中
        expNameEl.textContent = data.experiment_name || '-';
        analysisPeriodEl.textContent = `${data.analysis_period.start} 到 ${data.analysis_period.end}` || '-';

        // 填充总体趋势摘要
        overallTrendSummaryEl.textContent = data.overall_trend_summary || '无摘要信息。';

        // 填充每日分析明细表格
        dailyAnalysisTableBody.innerHTML = ''; // 清空旧数据
        if (data.daily_breakdown && data.daily_breakdown.length > 0) {
            data.daily_breakdown.forEach(day => {
                const row = dailyAnalysisTableBody.insertRow();
                row.insertCell().textContent = day.date;
                
                // 分析师信号 (简单展示)
                let signalsText = '无';
                if (day.analyst_signals && day.analyst_signals.length > 0) {
                    signalsText = day.analyst_signals.map(s => `${s.analyst}: ${s.signal} (${s.reason.substring(0,30)}...)`).join('; ');
                }
                row.insertCell().textContent = signalsText;

                // 基金经理决策
                let decisionText = '无';
                if (day.manager_decision) {
                    decisionText = `${day.manager_decision.action} (${day.manager_decision.reason.substring(0,30)}...)`;
                }
                row.insertCell().textContent = decisionText;
                row.insertCell().textContent = day.overall_sentiment_of_day || '-';
                row.insertCell().textContent = day.price_info ? (day.price_info.close_price || '-') : '-';
            });
        }

        // 填充统计数据
        if (data.statistics) {
            totalDaysAnalyzedEl.textContent = data.statistics.total_days_analyzed || '0';
            bullishDaysEl.textContent = data.statistics.bullish_sentiment_days || '0';
            bearishDaysEl.textContent = data.statistics.bearish_sentiment_days_approx || '0';
            neutralDaysEl.textContent = data.statistics.neutral_sentiment_days_approx || '0';
        }

        // TODO: 更新图表
        priceChartPlaceholder.textContent = `图表数据已接收，等待渲染 (${data.ticker})`;
        // 在这里可以使用Chart.js, ECharts等库根据 data.daily_breakdown 和 data.prices (如果提供) 来绘制图表
        // 例如: renderPriceChart(data.daily_breakdown, data.prices_raw_from_yfinance_if_any);
    }

    let realtimeIntervalId = null;
    function startRealtimeMonitoring(ticker, expName) {
        realtimeMonitoringView.style.display = 'block';
        realtimeStockTickerEl.textContent = ticker;
        if (realtimeIntervalId) clearInterval(realtimeIntervalId); // 清除之前的定时器

        const updateSignal = async () => {
            try {
                const signalData = await fetchRealtimeSignal(ticker, expName); // 使用api_client.js中的函数
                realtimeCurrentPriceEl.textContent = signalData.current_price || '-';
                realtimeSignalTextEl.textContent = `建议：${signalData.signal || '-'}`;
                realtimeSignalReasonEl.textContent = signalData.reason || '-';

                // 根据信号更新背景颜色
                realtimeSignalArea.className = 'signal-box'; // Reset classes
                if (signalData.signal) {
                    realtimeSignalArea.classList.add(`signal-${signalData.signal.toLowerCase()}`);
                }

            } catch (error) {
                realtimeSignalTextEl.textContent = "错误";
                realtimeSignalReasonEl.textContent = "获取实时信号失败: " + error.message;
                realtimeSignalArea.className = 'signal-box'; // Reset on error
            }
        };

        updateSignal(); // 立即获取一次
        realtimeIntervalId = setInterval(updateSignal, 5000); // 每5秒更新一次 (轮询)
    }

    function showLoading(isLoading) {
        loadingMessage.style.display = isLoading ? 'block' : 'none';
    }

    function showError(message) {
        errorTextEl.textContent = message;
        errorMessage.style.display = 'block';
    }
    function hideError() {
        errorMessage.style.display = 'none';
    }

    // (可选) 模拟启动实时监控，实际应用中应在历史数据加载后由用户触发或自动触发
    // analyzeButton.addEventListener('click', () => {
    //     const ticker = tickerInput.value.trim();
    //     if (ticker) {
    //         startRealtimeMonitoring(ticker, "ollama-test");
    //     }
    // });

});
