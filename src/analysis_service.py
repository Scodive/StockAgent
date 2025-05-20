# src/analysis_service.py
import datetime
from typing import Dict, Any, List, Optional
from util.db_helper import get_db, db_initialize # Assuming db_initialize is safe to call if already initialized
from util.logger import logger
# import yfinance as yf # Import yfinance if you plan to use it for prices soon

# Ensure database is initialized (especially if this service is called in a new process)
# This might need adjustment based on how your db connection is managed globally.
# If scripts calling this service already initialize, this might be redundant or configurable.
DEFAULT_USE_LOCAL_DB = True # Or read from an env var like: os.getenv("DEEPFUND_USE_LOCAL_DB", "True").lower() == "true"
db_initialize(use_local_db=DEFAULT_USE_LOCAL_DB) # Default to local, or make it configurable

def get_stock_prices_from_yfinance(ticker: str, start_date_str: str, end_date_str: str) -> List[Dict[str, Any]]:
    """Fetches stock prices from Yahoo Finance."""
    prices_data = []
    try:
        # yfinance often needs ticker symbols in a specific format (e.g., .SS for Shanghai, .SZ for Shenzhen for A-shares)
        # This might need adjustment based on the ticker format used in your system.
        stock = yf.Ticker(ticker)
        # yfinance end_date is exclusive, so add one day to include the end_date in results
        hist_end_date = (datetime.datetime.strptime(end_date_str, "%Y-%m-%d") + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        hist = stock.history(start=start_date_str, end=hist_end_date)
        if not hist.empty:
            for index, row in hist.iterrows():
                prices_data.append({
                    "trading_date": index.date(), # Already a date object
                    "close_price": row.get("Close"),
                    "open_price": row.get("Open"),
                    "high_price": row.get("High"),
                    "low_price": row.get("Low"),
                    "volume": row.get("Volume")
                })
        logger.info(f"Successfully fetched {len(prices_data)} price points for {ticker} from yfinance.")
    except Exception as e:
        logger.error(f"Error fetching prices from yfinance for {ticker}: {e}")
    return prices_data

def get_historical_summary(exp_name: str, ticker: str, start_date_str: str, end_date_str: str) -> Dict[str, Any]:
    """
    Retrieves and summarizes historical analysis data for a given ticker and period.
    """
    db = get_db()
    if not db:
        logger.error("Database not initialized for get_historical_summary.")
        # Attempt re-initialization as a fallback, though ideally it should be initialized by the calling context
        db_initialize(use_local_db=DEFAULT_USE_LOCAL_DB) 
        db = get_db()
        if not db:
            return {"error": "Database connection failed."}

    try:
        start_date_obj = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date_obj = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        logger.error(f"Invalid date format. Start: {start_date_str}, End: {end_date_str}")
        return {"error": f"Invalid date format. Expected YYYY-MM-DD."}

    config_id_str = db.get_config_id_by_name(exp_name) # Expects string UUID
    if not config_id_str:
        logger.warning(f"Experiment name '{exp_name}' not found in database.")
        return {"error": f"Experiment '{exp_name}' not found."}
    
    logger.info(f"Fetching historical summary for exp_name='{exp_name}' (config_id={config_id_str}), ticker='{ticker}', period='{start_date_str}' to '{end_date_str}'")

    signals_raw = []
    decisions_raw = []
    prices_raw = [] # Initialize as empty

    try:
        signals_raw = db.get_signals_for_ticker_period(config_id_str, ticker, start_date_str, end_date_str)
        decisions_raw = db.get_decisions_for_ticker_period(config_id_str, ticker, start_date_str, end_date_str)
        
        # Fetch prices using yfinance instead of a DB call for now
        # prices_raw = get_stock_prices_from_yfinance(ticker, start_date_str, end_date_str)
        # For now, let's keep prices_raw empty to avoid yfinance dependency if not installed/configured
        logger.info("Price fetching from yfinance is available but commented out. prices_raw will be empty.")
        # If you want to enable it, uncomment the line above and ensure yfinance is installed.

    except Exception as e:
        logger.error(f"Error fetching data from database for historical summary: {e}")
        return {"error": f"Database query error: {e}"}

    daily_summary = {}
    # Create a set of all unique dates from signals, decisions, and prices to iterate over
    all_event_dates = set()
    if signals_raw: all_event_dates.update([s['trading_date'] for s in signals_raw])
    if decisions_raw: all_event_dates.update([d['trading_date'] for d in decisions_raw])
    if prices_raw: all_event_dates.update([p['trading_date'] for p in prices_raw])

    # Ensure dates are actual date objects if they are strings from DB
    processed_dates = set()
    for d_str in all_event_dates:
        if isinstance(d_str, str):
            try:
                processed_dates.add(datetime.datetime.strptime(d_str, "%Y-%m-%d").date())
            except ValueError:
                logger.warning(f"Could not parse date string {d_str} from DB records. Skipping.")
        elif isinstance(d_str, datetime.date):
            processed_dates.add(d_str)
    
    sorted_dates = sorted(list(processed_dates))

    bullish_days = 0
    bearish_days = 0
    neutral_days = 0

    for L_date_obj in sorted_dates:
        date_str_key = L_date_obj.strftime("%Y-%m-%d")
        daily_summary[date_str_key] = {
            "date": date_str_key,
            "analyst_signals": [],
            "manager_decision": None,
            "price_info": None,
            "overall_sentiment_of_day": "Neutral"
        }

        analyst_sentiment_scores = {"Bullish": 0, "Bearish": 0, "Neutral": 0}
        for signal in signals_raw:
            signal_date = signal['trading_date']
            if isinstance(signal_date, str): signal_date = datetime.datetime.strptime(signal_date, "%Y-%m-%d").date()
            if signal_date == L_date_obj:
                daily_summary[date_str_key]["analyst_signals"].append({
                    "analyst": signal.get('analyst_name'),
                    "signal": signal.get('signal_type'),
                    "reason": signal.get('justification', '')
                })
                if signal.get('signal_type') in analyst_sentiment_scores:
                    analyst_sentiment_scores[signal.get('signal_type')] += 1
        
        current_day_sentiment = "Neutral"
        if analyst_sentiment_scores["Bullish"] > analyst_sentiment_scores["Bearish"]:
            current_day_sentiment = "Bullish"
            bullish_days +=1
        elif analyst_sentiment_scores["Bearish"] > analyst_sentiment_scores["Bullish"]:
            current_day_sentiment = "Bearish"
            bearish_days +=1
        elif sum(analyst_sentiment_scores.values()) > 0:
            current_day_sentiment = "Neutral"
            neutral_days +=1
        daily_summary[date_str_key]["overall_sentiment_of_day"] = current_day_sentiment

        for decision in decisions_raw:
            decision_date = decision['trading_date']
            if isinstance(decision_date, str): decision_date = datetime.datetime.strptime(decision_date, "%Y-%m-%d").date()
            if decision_date == L_date_obj:
                daily_summary[date_str_key]["manager_decision"] = {
                    "action": decision.get('decision_type'),
                    "reason": decision.get('justification', '')
                }
                if decision.get('decision_type', '').upper() == "BUY":
                     daily_summary[date_str_key]["overall_sentiment_of_day"] = "Strongly Bullish"
                elif decision.get('decision_type', '').upper() == "SELL":
                     daily_summary[date_str_key]["overall_sentiment_of_day"] = "Strongly Bearish"
                break 
        
        for price_entry in prices_raw:
            price_date = price_entry['trading_date'] # Should be date object from yfinance helper
            if price_date == L_date_obj:
                daily_summary[date_str_key]["price_info"] = price_entry # Store full dict: close, open, high, low, volume
                break
    
    overall_trend_summary_text = (
        f"Trend analysis for {ticker} from {start_date_str} to {end_date_str} for experiment '{exp_name}'. "
        f"Observed {bullish_days} bullish-leaning days, {bearish_days} bearish-leaning days, "
        f"and {neutral_days} neutral/mixed days based on analyst signals and manager decisions."
    )
    if not sorted_dates:
        overall_trend_summary_text = f"No analysis data found for {ticker} in the period {start_date_str} to {end_date_str} for experiment '{exp_name}'."

    return {
        "ticker": ticker,
        "experiment_name": exp_name,
        "analysis_period": {"start": start_date_str, "end": end_date_str},
        "overall_trend_summary": overall_trend_summary_text,
        "daily_breakdown": list(daily_summary.values()),
        "statistics": {
            "total_days_analyzed": len(sorted_dates),
            "bullish_sentiment_days": bullish_days,
            "bearish_sentiment_days_approx": bearish_days, # Renamed for clarity if neutral_days logic is simple
            "neutral_sentiment_days_approx": neutral_days,
        }
    }

if __name__ == '__main__':
    # Ensure yfinance is installed if you uncomment price fetching: pip install yfinance
    # You might need to load .env for DB credentials if db_initialize relies on it implicitly
    # from dotenv import load_dotenv
    # load_dotenv()

    # --- IMPORTANT: Configure these for your test --- 
    test_exp_name = "ollama-test"  # Replace with a real exp_name from your Config table
    test_ticker = "BABA"          # Replace with a ticker you ran historical analysis for (e.g., 600036.SS)
    test_start_date = "2025-05-01"          # Adjust date range to match data generated by generate_historical_analysis.py
    test_end_date = "2023-05-20"
    # --- End of test configuration ---

    if test_exp_name == "your_actual_exp_name" or test_ticker == "YOUR_TICKER.SS":
        logger.error("Please update test_exp_name and test_ticker in src/analysis_service.py before running the test.")
    else:
        logger.info(f"Running test for get_historical_summary with exp='{test_exp_name}', ticker='{test_ticker}'")
        summary = get_historical_summary(test_exp_name, test_ticker, test_start_date, test_end_date)
        
        if "error" in summary:
            logger.error(f"Test failed: {summary['error']}")
        else:
            logger.info("Test run successful. Summary data (first 2 daily entries shown if available):")
            import json
            # Pretty print, handling date objects
            summary_to_print = summary.copy()
            if len(summary_to_print.get("daily_breakdown", [])) > 2:
                summary_to_print["daily_breakdown"] = summary_to_print["daily_breakdown"][:2] + [f"... and {len(summary["daily_breakdown"])-2} more days ..."]
            
            print(json.dumps(summary_to_print, indent=2, default=str)) 