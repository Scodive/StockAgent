import argparse
from typing import Dict, Any
from dotenv import load_dotenv
from graph.workflow import AgentWorkflow
from util.config import ConfigParser
from util.logger import logger
from util.db_helper import db_initialize, get_db

# Load environment variables from .env file
load_dotenv()

def load_portfolio_config(cfg: Dict[str, Any], db):
    """Load and validate config based on experiment configuration."""
    config_id = db.get_config_id_by_name(cfg["exp_name"])
    if not config_id:
        logger.info(f"Creating new config for {cfg['exp_name']}")
        config_id = db.create_config(cfg)
        if not config_id:
            raise RuntimeError(f"Failed to create config for {cfg['exp_name']}")
    return config_id

def run_single_day_analysis(config_file_path: str, trading_date_str: str, use_local_db_flag: bool):
    """
    Runs the DeepFund analysis workflow for a single trading day.
    """
    # In ConfigParser, we need to adjust it to accept file path and trading_date_str if it currently relies on args object
    # Assuming ConfigParser can be instantiated or called with config_file_path and trading_date_str
    cfg_parser = ConfigParser(config_file_path=config_file_path, trading_date_str=trading_date_str) # Adjusted instantiation
    cfg = cfg_parser.get_config()

    # Initialize the global database connection based on the local-db flag
    # Ensure db_initialize can be called multiple times or handles re-initialization safely
    db_initialize(use_local_db=use_local_db_flag)
    db = get_db() 

    logger.info(f"Loading config for {cfg['exp_name']}, trading date: {trading_date_str}")
    config_id = load_portfolio_config(cfg, db)
    logger.info("Init DeepFund and run")

    # Check if this date has already been processed for this config
    latest_trading_date_dt = db.get_latest_trading_date(config_id) # Returns datetime.datetime or None
    if latest_trading_date_dt and latest_trading_date_dt.date() > cfg["trading_date"]:
        logger.info(f"Trading date {cfg['trading_date'].strftime('%Y-%m-%d')} for {cfg['exp_name']} has already been processed or is earlier than the latest processed date ({latest_trading_date_dt.date().strftime('%Y-%m-%d')}). Skipping.")
        return True # Indicate success as it's already done or not needed
    
    try:
        app = AgentWorkflow(cfg, config_id)
        time_cost = app.run(config_id) # cfg already contains trading_date, app might use it
        logger.info(f"DeepFund run for {trading_date_str} completed in {time_cost:.2f} seconds")
        return True # Indicate success
    except Exception as e:
        logger.error(f"Error during portfolio operations for {trading_date_str}: {e}")
        return False # Indicate failure

def main():
    """Main entry point for the DeepFund System (Command Line Interface)."""

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the DeepFund System for a single day")
    parser.add_argument("--config", type=str, required=True, help="Path to configuration file")
    parser.add_argument("--trading-date", type=str, required=True, help="Trading date in format YYYY-MM-DD")
    parser.add_argument("--local-db", action="store_true", help="Use local SQLite database")
    args = parser.parse_args()

    # Call the refactored analysis function
    run_single_day_analysis(args.config, args.trading_date, args.local_db)

if __name__ == "__main__":
    main()
