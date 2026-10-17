import logging
import traceback
from pathlib import Path
from django.db import connection
from django.db.utils import DatabaseError

LOG_DIR = Path(__file__).resolve().parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
logger = logging.getLogger('db_errors')
logger.setLevel(logging.ERROR)
if not logger.handlers:
    fh = logging.FileHandler(LOG_DIR / 'db_errors.log', encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(fh)

def call_procedure(name, params=(), out_count=0, fetch=True):
    out_vars = [f"@out_{i}" for i in range(out_count)]
    
    args = list(params) + out_vars
    
    in_placeholders = ','.join(['%s'] * len(params))
    if out_count:
        placeholders = f"{in_placeholders},{','.join(out_vars)}"
    else:
        placeholders = in_placeholders
        
    sql = f"CALL {name}({placeholders})"
    
    try:
        with connection.cursor() as cur:
            # Выполняем процедуру
            cur.execute(sql, params)
            rows = cur.fetchall() if fetch else None
            
            out_values = []
            if out_count:
                # Забираем значения OUT-переменных отдельным запросом
                select_sql = f"SELECT {','.join(out_vars)}"
                cur.execute(select_sql)
                out_values = list(cur.fetchone())
                
        return rows, out_values
    except DatabaseError:
        logger.error("DB error in %s params=%s\n%s", name, params, traceback.format_exc())
        raise

def call_function(name, params=()):
    placeholders = ','.join(['%s'] * len(params))
    sql = f"SELECT {name}({placeholders})"
    try:
        with connection.cursor() as cur:
            cur.execute(sql, list(params))
            return cur.fetchone()[0]
    except DatabaseError:
        logger.error("DB error in function %s params=%s\n%s", name, params, traceback.format_exc())
        raise