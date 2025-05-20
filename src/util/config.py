import yaml
from datetime import datetime
from util.logger import logger
from typing import Dict, Any

class ConfigParser:
    """Manages configuration loading and validation."""

    def __init__(self, config_file_path: str, trading_date_str: str):
        """Initialize the configuration manager."""
        self.config_file_path = config_file_path
        self.trading_date_str = trading_date_str
        self.config = self._load_and_process_config()
        
    def _load_and_process_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file and process it."""
        cfg = {}
        try:
            with open(self.config_file_path, 'r') as f:
                logger.info(f"Loading configuration from {self.config_file_path}")
                cfg = yaml.safe_load(f)
        except FileNotFoundError:
            raise ValueError(f"Configuration file not found: {self.config_file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {e}")
        
        if not isinstance(cfg, dict):
            raise ValueError(f"Configuration file {self.config_file_path} did not load as a dictionary.")

        try:
            cfg['trading_date'] = datetime.strptime(self.trading_date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f"Invalid trading_date format: {self.trading_date_str}. Expected YYYY-MM-DD.")

        if 'exp_name' not in cfg:
            base_name = self.config_file_path.split('/')[-1].split('.')[0]
            cfg['exp_name'] = cfg.get('exp_name', f"exp_{base_name}_{self.trading_date_str}")
            logger.info(f"exp_name not found in config, derived as: {cfg['exp_name']}")

        cfg['planner_mode'] = cfg.get('planner_mode', False)

        return cfg

    def get_config(self) -> Dict[str, Any]:
        """Get the loaded and processed configuration."""
        return self.config
