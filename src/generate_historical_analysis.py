# src/generate_historical_analysis.py
import argparse
import datetime
from main import run_single_day_analysis # 从我们刚修改的main.py中导入
from util.logger import logger

def get_trading_days(start_date_str: str, end_date_str: str) -> list[str]:
    """
    Generates a list of trading days (Mon-Fri) between start and end dates.
    Note: This is a simplified version and does not account for actual holidays.
    For A-shares, you'd need a proper trading calendar.
    """
    trading_days = []
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
    
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5: # Monday = 0, Sunday = 6
            trading_days.append(current_date.strftime("%Y-%m-%d"))
        current_date += datetime.timedelta(days=1)
    return trading_days

def main_historical():
    parser = argparse.ArgumentParser(description="Generate historical analysis for DeepFund.")
    parser.add_argument("--config", type=str, required=True, help="Path to configuration file (e.g., src/config/your_exp_config.yaml)")
    # Note: Tickers are usually defined IN the config file. 
    # If you want to run for a specific ticker NOT in the config, the config loading or AgentWorkflow might need adjustment.
    # For now, assume the config file has the target ticker(s).
    # parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol") 
    parser.add_argument("--start-date", type=str, required=True, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", type=str, required=True, help="End date in YYYY-MM-DD format")
    parser.add_argument("--local-db", action="store_true", help="Use local SQLite database")
    
    args = parser.parse_args()

    logger.info(f"Starting historical analysis generation: Config={args.config}, Start={args.start_date}, End={args.end_date}")

    # TODO: Potentially modify the config file in memory or create a temporary one 
    # if the ticker needs to be dynamically set for each run, and it's not already parameterized in the config.
    # For now, we assume the config pointed to by args.config is set up for the desired ticker(s).
    
    # Get the list of dates to process
    # For A-shares, a proper trading calendar API would be better than just Mon-Fri
    dates_to_process = get_trading_days(args.start_date, args.end_date)
    
    if not dates_to_process:
        logger.info("No trading days found in the specified date range.")
        return

    logger.info(f"Processing {len(dates_to_process)} trading day(s) from {args.start_date} to {args.end_date}.")

    successful_runs = 0
    failed_runs = 0

    for date_str in dates_to_process:
        logger.info(f"--- Processing analysis for date: {date_str} ---")
        # Here, config_file_path is passed directly.
        # The run_single_day_analysis function will use this config and the provided date_str.
        # The config file itself should ideally list the ticker(s) to be analyzed.
        # If you need to run for a SINGLE specific ticker passed via CLI and it's not easy to modify the config each time,
        # then ConfigParser or the workflow itself might need a way to override/specify the ticker.
        success = run_single_day_analysis(
            config_file_path=args.config,
            trading_date_str=date_str,
            use_local_db_flag=args.local_db
        )
        if success:
            successful_runs += 1
        else:
            failed_runs +=1
        logger.info(f"--- Completed processing for date: {date_str} ---")

    logger.info(f"Historical analysis generation finished. Successful runs: {successful_runs}, Failed runs: {failed_runs}.")

if __name__ == "__main__":
    main_historical()