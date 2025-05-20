// api_client.js

const API_BASE_URL = "http://localhost:8000/api"; // 假设您的后端API基础URL

/**
 * 获取历史分析数据
 * @param {string} ticker 股票代码
 * @param {string} expName 实验配置名称
 * @param {string} startDate 开始日期 (YYYY-MM-DD)
 * @param {string} endDate 结束日期 (YYYY-MM-DD)
 * @returns {Promise<Object>} 后端返回的分析数据
 */
async function fetchHistoricalAnalysis(ticker, expName, startDate, endDate) {
    const endpoint = `${API_BASE_URL}/historical_analysis`;
    const requestBody = {
        ticker: ticker,
        exp_name: expName,
        start_date: startDate,
        end_date: endDate
    };

    console.log("Requesting historical analysis with:", requestBody);

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            // 如果HTTP状态码不是2xx，尝试解析错误信息
            let errorData;
            try {
                errorData = await response.json();
            } catch (e) {
                // 如果响应体不是JSON或为空
                errorData = { message: response.statusText };
            }
            throw new Error(`HTTP error ${response.status}: ${errorData.detail || errorData.message || 'Unknown error'}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch historical analysis:", error);
        throw error; // 将错误重新抛出，以便UI层可以捕获和处理
    }
}

/**
 * (占位符/示例) 获取实时信号数据 - 实际应用中可能使用WebSocket或SSE
 * @param {string} ticker 股票代码
 * @param {string} expName 实验配置名称
 * @returns {Promise<Object>} 后端返回的实时信号数据
 */
async function fetchRealtimeSignal(ticker, expName) {
    // 注意：这只是一个轮询的示例。对于真正的实时数据，WebSocket 或 Server-Sent Events (SSE) 更合适。
    // const endpoint = `${API_BASE_URL}/realtime_feed?ticker=${encodeURIComponent(ticker)}&exp_name=${encodeURIComponent(expName)}`;
    console.warn("fetchRealtimeSignal is a placeholder. For actual real-time, use WebSockets or SSE.");

    // 模拟一个API调用
    return new Promise(resolve => {
        setTimeout(() => {
            resolve({
                current_price: (Math.random() * 100 + 50).toFixed(2), // 模拟价格
                signal: ["Buy", "Sell", "Hold"][Math.floor(Math.random() * 3)],
                reason: "This is a mock real-time signal based on simulated data.",
                timestamp: new Date().toISOString()
            });
        }, 1000);
    });

    /*
    // 实际的 fetch 调用可能像这样:
    try {
        const response = await fetch(endpoint);
        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch (e) {
                errorData = { message: response.statusText };
            }
            throw new Error(`HTTP error ${response.status}: ${errorData.detail || errorData.message || 'Unknown error'}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch real-time signal:", error);
        throw error;
    }
    */
}

// 如果使用模块系统 (例如在React/Vue项目中，或者使用<script type="module">)
// export { fetchHistoricalAnalysis, fetchRealtimeSignal };
// 对于简单的HTML <script src="...">, 这些函数会自动成为全局可用 (或者附加到window对象) 