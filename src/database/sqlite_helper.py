import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from graph.schema import Decision, AnalystSignal
from database.interface import BaseDB
from database.sqlite_setup import DB_PATH
from util.logger import logger

class SQLiteDB(BaseDB):
    def __init__(self):
        self.db_path = DB_PATH

    def _get_connection(self):
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row # access columns by name
        return conn


    def get_config(self, config_id: str) -> Optional[Dict]:
        """Get config by id."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM config WHERE id = ?', (config_id,))
            row = cursor.fetchone()
            
            if row:
                return row
            return None
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return None
        finally:
            if conn:
                conn.close()
            
    def get_config_id_by_name(self, exp_name: str) -> Optional[str]:
        query = "SELECT id FROM Config WHERE exp_name = ?;"
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (exp_name,))
            result = cursor.fetchone()
            return str(result['id']) if result else None
        except Exception as e:
            logger.error(f"SQLite Error getting config_id for {exp_name}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def create_config(self, config: Dict) -> Optional[str]:
        """Create a new config entry."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            config_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO config (id, exp_name, updated_at, tickers, has_planner, llm_model, llm_provider)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                config_id,
                config["exp_name"],
                datetime.now(timezone.utc).isoformat(), # UTC time
                json.dumps(config["tickers"]),
                config["planner_mode"],
                config["llm"]["model"],
                config["llm"]["provider"]
            ))
            
            conn.commit()
            return config_id
        except Exception as e:
            logger.error(f"Error creating config: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_latest_trading_date(self, config_id: str) -> Optional[datetime]:
        """Get the latest trading date for a config."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT trading_date FROM portfolio 
                WHERE config_id = ? AND trading_date IS NOT NULL
                ORDER BY updated_at DESC 
                LIMIT 1
            ''', (config_id,))
            
            row = cursor.fetchone()
            
            if row:
                return datetime.fromisoformat(row['trading_date'])
            return None
        except Exception as e:
            logger.error(f"Error getting latest trading date: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_latest_portfolio(self, config_id: str) -> Optional[Dict]:
        """Get the latest portfolio for a config."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM portfolio 
                WHERE config_id = ? AND trading_date IS NOT NULL
                ORDER BY updated_at DESC 
                LIMIT 1
            ''', (config_id,))
            
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row['id'],
                    'cashflow': row['cashflow'],
                    'positions': json.loads(row['positions'])
                }
            return None
        except Exception as e:
            logger.error(f"Portfolio not found: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def create_portfolio(self, config_id: str, cashflow: float, trading_date: datetime) -> Optional[Dict]:
        """Create a new portfolio."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            portfolio_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO portfolio (id, config_id, updated_at, trading_date, cashflow, total_assets, positions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                portfolio_id,
                config_id,
                datetime.now(timezone.utc).isoformat(), # UTC time
                trading_date.isoformat(),
                cashflow,
                cashflow,
                json.dumps({})
            ))
            
            conn.commit()
            return {
                'id': portfolio_id,
                'cashflow': cashflow,
                'total_assets': cashflow,
                'positions': {}
            }
        except Exception as e:
            logger.error(f"Error creating portfolio: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def copy_portfolio(self, config_id: str, portfolio: Dict, trading_date: datetime) -> Optional[Dict]:
        """Copy a portfolio."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            portfolio_id = str(uuid.uuid4())
            total_assets = portfolio['cashflow'] + sum(position['value'] for position in portfolio['positions'].values())
            cursor.execute('''
                INSERT INTO portfolio (id, config_id, updated_at, trading_date, cashflow, total_assets, positions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                portfolio_id,
                config_id,
                datetime.now(timezone.utc).isoformat(), # UTC time
                trading_date.isoformat(),
                portfolio['cashflow'],
                total_assets,
                json.dumps(portfolio['positions'])
            ))

            conn.commit()
            return {
                'id': portfolio_id,
                'cashflow': portfolio['cashflow'],
                'positions': portfolio['positions']
            }
        except Exception as e:
            logger.error(f"Error copying portfolio: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_portfolio(self, config_id: str, portfolio: Dict, trading_date: datetime) -> bool:
        """update portfolio."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            total_assets = portfolio['cashflow'] + sum(position['value'] for position in portfolio['positions'].values())
            
            cursor.execute('''
                UPDATE portfolio 
                SET config_id = ?, updated_at = ?, trading_date = ?, cashflow = ?, total_assets = ?, positions = ?
                WHERE id = ?
            ''', (
                config_id,
                datetime.now(timezone.utc).isoformat(), # UTC time
                trading_date.isoformat(),
                portfolio['cashflow'],
                total_assets,
                json.dumps(portfolio['positions']),
                portfolio['id']
            ))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")
            return False
        finally:
            if conn:
                conn.close()
        
    def save_decision(self, portfolio_id: str, ticker: str, prompt: str, decision: Decision, trading_date: datetime) -> Optional[str]:
        """Save a new decision."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            decision_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO decision (id, portfolio_id, updated_at, trading_date, ticker, llm_prompt, 
                                   action, shares, price, justification)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                decision_id,
                portfolio_id,
                datetime.now(timezone.utc).isoformat(), # UTC time
                trading_date.isoformat(),
                ticker,
                prompt,
                str(decision.action),
                decision.shares,
                decision.price,
                decision.justification
            ))
            
            conn.commit()
            return decision_id
        except Exception as e:
            logger.error(f"Error saving decision: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def save_signal(self, portfolio_id: str, analyst: str, ticker: str, prompt: str, signal: AnalystSignal) -> Optional[str]:
        """Save a new signal."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            signal_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO signal (id, portfolio_id, updated_at, ticker, llm_prompt,
                                  analyst, signal, justification)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal_id,
                portfolio_id,
                datetime.now(timezone.utc).isoformat(), # UTC time 
                ticker,
                prompt,
                analyst,
                str(signal.signal),
                signal.justification
            ))
            
            conn.commit()
            return signal_id
        except Exception as e:
            logger.error(f"Error saving signal: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_recent_portfolio_ids_by_config_id(self, config_id: str, limit: int) -> List[str]:
        """Get recent portfolio ids by config id."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()  
            
            cursor.execute('''
                SELECT id FROM portfolio 
                WHERE config_id = ? AND trading_date IS NOT NULL
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (config_id, limit))
            
            return [row['id'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting portfolio ids: {e}")   
            return []
        finally:
            if conn:
                conn.close()

    def get_decision_memory(self, exp_name: str, ticker: str, limit: int) -> List[Dict]:
        """Get recent decisions for a ticker."""
        
        # Step 1: Get config id by exp_name
        config_id = self.get_config_id_by_name(exp_name)
        if not config_id:
            logger.error(f"Config not found for {exp_name}")
            return []
        
        # Step 2: Get recent 5 portfolio transactions
        portfolio_ids = self.get_recent_portfolio_ids_by_config_id(config_id, limit)
        if not portfolio_ids:
            logger.error(f"Portfolio not found for {config_id}")
            return []
        
        # Step 3: Get decision memory by portfolio ids and ticker
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create the correct number of placeholders for the IN clause
            placeholders = ','.join('?' * len(portfolio_ids))
            query = f'''
                SELECT * FROM decision 
                WHERE portfolio_id IN ({placeholders}) AND ticker = ?
                ORDER BY updated_at DESC
            '''
            
            # Combine portfolio_ids and ticker into parameters
            params = portfolio_ids + [ticker]
            cursor.execute(query, params)
              
            decisions = []
            for row in cursor.fetchall():
                decisions.append({
                    'trading_date': row['trading_date'],
                    'action': row['action'],
                    'shares': row['shares'],
                    'price': row['price'],
                })
            
            return decisions
        except Exception as e:
            logger.warning(f"No decision memory found for {ticker} in {exp_name}: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_signals_for_ticker_period(self, config_id: str, ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        query = """
            SELECT p.trading_date, s.analyst AS analyst_name, s.signal AS signal_type, 
                   s.justification, s.ticker AS ticker_symbol
            FROM Signal s
            JOIN Portfolio p ON s.portfolio_id = p.id
            WHERE p.config_id = ? AND s.ticker = ? AND p.trading_date BETWEEN ? AND ?
            ORDER BY p.trading_date, s.analyst;
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (config_id, ticker, start_date, end_date))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"SQLite Error getting signals for config_id={config_id}, ticker={ticker}, period={start_date}-{end_date}: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_decisions_for_ticker_period(self, config_id: str, ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        query = """
            SELECT d.trading_date, d.action AS decision_type, d.justification, d.ticker AS ticker_symbol
            FROM Decision d
            JOIN Portfolio p ON d.portfolio_id = p.id
            WHERE p.config_id = ? AND d.ticker = ? AND d.trading_date BETWEEN ? AND ?
            ORDER BY d.trading_date;
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (config_id, ticker, start_date, end_date))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"SQLite Error getting decisions for config_id={config_id}, ticker={ticker}, period={start_date}-{end_date}: {e}")
            return []
        finally:
            if conn:
                conn.close()

## init global instance
# sqlite_db = SQLiteDB()