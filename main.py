from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import random

app = Flask(__name__)
CORS(app)  # 这将允许来自所有源的跨域请求，对于开发来说很方便

@app.route('/api/historical_analysis', methods=['POST'])
def historical_analysis():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        ticker = data.get('ticker')
        exp_name = data.get('exp_name')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        if not all([ticker, exp_name, start_date_str, end_date_str]):
            return jsonify({"error": "Missing required fields: ticker, exp_name, start_date, end_date"}), 400

        # 简单验证日期格式 (可选, 但推荐)
        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if start_date > end_date:
                return jsonify({"error": "start_date cannot be after end_date"}), 400
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        print(f"Received historical analysis request for {ticker} from {start_date_str} to {end_date_str} with exp_name: {exp_name}")

        # --- 模拟后端处理和数据生成 ---
        # 在实际应用中，这里你会连接数据库、调用模型、进行计算等

        # 生成模拟的每日分析数据
        daily_data = []
        current_date = start_date
        while current_date <= end_date:
            daily_data.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "analyst_signal": random.choice(["强烈买入", "买入", "持有", "卖出", "强烈卖出"]),
                "manager_decision": random.choice(["增持", "持有", "减持"]),
                "sentiment": random.choice(["乐观", "中性", "悲观"]),
                "price_close": round(random.uniform(50, 200), 2)
            })
            current_date += datetime.timedelta(days=1)

        # 模拟总体趋势和统计
        overall_trend = "根据历史数据和模拟分析，股票 {} 呈现 {} 趋势。".format(
            ticker, random.choice(["整体上涨", "震荡调整", "温和下跌"])
        )
        total_days = len(daily_data)
        bullish_days = sum(1 for item in daily_data if item["sentiment"] == "乐观")
        bearish_days = sum(1 for item in daily_data if item["sentiment"] == "悲观")
        neutral_days = total_days - bullish_days - bearish_days

        response_data = {
            "stock_info": {
                "name": f"{ticker} 公司", # 模拟股票名称
                "ticker": ticker,
                "exp_name": exp_name,
                "analysis_period": f"{start_date_str} 至 {end_date_str}"
            },
            "overall_trend_summary": overall_trend,
            "daily_analysis": daily_data,
            "statistics": {
                "total_days_analyzed": total_days,
                "bullish_days": bullish_days,
                "bearish_days": bearish_days,
                "neutral_days": neutral_days
            }
        }
        # --- 模拟结束 ---

        return jsonify(response_data), 200

    except Exception as e:
        print(f"Error in /api/historical_analysis: {e}")
        return jsonify({"error": "An internal server error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    # 确保在与 api_client.js 中相同的端口 (8000) 上运行
    app.run(debug=True, port=8000) 