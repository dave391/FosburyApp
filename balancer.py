#!/usr/bin/env python3
"""
Balancer - Script per il bilanciamento automatico della leva finanziaria

Questo script monitora i bot con stato "running" e mantiene la leva finanziaria
entro i parametri desiderati, aggiustando il margine quando necessario.

Uso:
    python balancer.py
"""

import logging
import sys
import os
import time
from datetime import datetime

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Crea directory logs se non esiste
os.makedirs("logs", exist_ok=True)

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/balancer_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)

logger = logging.getLogger('balancer')

# Importa il modulo balancer
from trading.balancer import Balancer

def main():
    """Funzione principale"""
    logger.info("=== Avvio Balancer ===")
    balancer = Balancer()
    
    try:
        balancer.run()
        success = True
    except KeyboardInterrupt:
        logger.info("Interruzione manuale del balancer")
        success = True
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione del balancer: {e}")
        success = False
    
    logger.info("=== Fine Balancer ===")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)