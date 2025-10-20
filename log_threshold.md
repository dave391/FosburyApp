2025-10-17T05:06:11.632109832Z ==> Running 'PYTHONPATH=. python monitor/threshold_monitoring.py'
2025-10-17T05:06:12.432311229Z INFO:database.models:Connesso a MongoDB
2025-10-17T05:06:12.43235097Z INFO:database.models:PositionManager inizializzato
2025-10-17T05:06:16.392386217Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T05:06:18.482046238Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T05:06:19.292866935Z INFO:trading.exchange_manager:Exchange bitmex inizializzato con successo
2025-10-17T05:06:19.379544315Z INFO:trading.exchange_manager:Posizione bitfinex: {'info': ['tSOLF0:USTF0', 'ACTIVE', '2.5', '199.4168', '0', '0', '-30.092', '-6.036000978854339', '178.816140956', '7.7939570051771465', None, '185729809', None, None, None, '1', None, '63.96519761', '24.9271', None], 'id': '185729809', 'symbol': 'SOL/USDT:USDT', 'notional': 2.5, 'marginMode': 'isolated', 'liquidationPrice': 178.816140956, 'entryPrice': 199.4168, 'unrealizedPnl': -30.092, 'percentage': -6.036000978854339, 'contracts': None, 'contractSize': 1.0, 'markPrice': None, 'lastPrice': None, 'side': 'long', 'hedged': None, 'timestamp': None, 'datetime': None, 'lastUpdateTimestamp': None, 'maintenanceMargin': 24.9271, 'maintenanceMarginPercentage': None, 'collateral': 63.96519761, 'initialMargin': None, 'initialMarginPercentage': None, 'leverage': 7.7939570051771465, 'marginRatio': None, 'stopLossPrice': None, 'takeProfitPrice': None}
2025-10-17T05:06:19.392892294Z INFO:database.models:Threshold aggiornati per posizione 219984293952
2025-10-17T05:06:19.769768178Z INFO:database.models:Threshold aggiornati per posizione cfa71839-5211-40b4-857d-4ebf087010a5
2025-10-17T05:06:19.769804039Z Liquidation price recuperato da bitfinex: 178.816140956
2025-10-17T05:06:19.769818449Z Calcolo threshold long: entry=195.1288, liq=178.816140956, diff=16.3127, threshold=179.6318
2025-10-17T05:06:19.769823489Z Calcolo threshold long: entry=195.1288, liq=178.816140956, diff=16.3127, threshold=182.0787
2025-10-17T05:06:19.769827729Z Liquidation price recuperato da bitmex: 225.26
2025-10-17T05:06:19.769831179Z Calcolo threshold short: entry=195.6624, liq=225.26, diff=29.5976, threshold=223.7801
2025-10-17T05:06:19.769834589Z Calcolo threshold short: entry=195.6624, liq=225.26, diff=29.5976, threshold=219.3405
2025-10-17T05:26:08.034023732Z ==> Running 'PYTHONPATH=. python monitor/threshold_monitoring.py'
2025-10-17T05:26:08.782853977Z INFO:database.models:Connesso a MongoDB
2025-10-17T05:26:08.782889618Z INFO:database.models:PositionManager inizializzato
2025-10-17T05:26:12.802449553Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T05:26:13.630130023Z INFO:trading.exchange_manager:Exchange bitmex inizializzato con successo
2025-10-17T05:26:15.707751874Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T05:26:16.425314473Z INFO:trading.exchange_manager:Posizione bitfinex: {'info': ['tSOLF0:USTF0', 'ACTIVE', '2.5', '199.4168', '0', '0', '-31.01700000000001', '-6.221542016520175', '178.816140956', '7.7939570051771465', None, '185729809', None, None, None, '1', None, '63.96519761', '24.9271', None], 'id': '185729809', 'symbol': 'SOL/USDT:USDT', 'notional': 2.5, 'marginMode': 'isolated', 'liquidationPrice': 178.816140956, 'entryPrice': 199.4168, 'unrealizedPnl': -31.01700000000001, 'percentage': -6.221542016520175, 'contracts': None, 'contractSize': 1.0, 'markPrice': None, 'lastPrice': None, 'side': 'long', 'hedged': None, 'timestamp': None, 'datetime': None, 'lastUpdateTimestamp': None, 'maintenanceMargin': 24.9271, 'maintenanceMarginPercentage': None, 'collateral': 63.96519761, 'initialMargin': None, 'initialMarginPercentage': None, 'leverage': 7.7939570051771465, 'marginRatio': None, 'stopLossPrice': None, 'takeProfitPrice': None}
2025-10-17T05:26:16.440095013Z INFO:database.models:Threshold aggiornati per posizione 219984293952
2025-10-17T05:26:16.713100722Z INFO:database.models:Threshold aggiornati per posizione cfa71839-5211-40b4-857d-4ebf087010a5
2025-10-17T05:26:16.713141113Z Liquidation price recuperato da bitfinex: 178.816140956
2025-10-17T05:26:16.713149333Z Calcolo threshold long: entry=195.1288, liq=178.816140956, diff=16.3127, threshold=179.6318
2025-10-17T05:26:16.713158723Z Calcolo threshold long: entry=195.1288, liq=178.816140956, diff=16.3127, threshold=182.0787
2025-10-17T05:26:16.713164964Z Liquidation price recuperato da bitmex: 225.26
2025-10-17T05:26:16.713170284Z Calcolo threshold short: entry=195.6624, liq=225.26, diff=29.5976, threshold=223.7801
2025-10-17T05:26:16.713177844Z Calcolo threshold short: entry=195.6624, liq=225.26, diff=29.5976, threshold=219.3405
2025-10-17T05:46:08.860695504Z ==> Running 'PYTHONPATH=. python monitor/threshold_monitoring.py'
2025-10-17T05:46:09.647867919Z INFO:database.models:Connesso a MongoDB
2025-10-17T05:46:09.647888529Z INFO:database.models:PositionManager inizializzato
2025-10-17T05:46:13.484813975Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T05:46:15.577829476Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T05:46:16.394884798Z INFO:trading.exchange_manager:Exchange bitmex inizializzato con successo
2025-10-17T05:46:16.469334654Z INFO:trading.exchange_manager:Posizione bitfinex: {'info': ['tSOLF0:USTF0', 'ACTIVE', '2.5', '199.4168', '0', '0', '-34.091999999999985', '-6.838340601193077', '178.816140956', '7.7939570051771465', None, '185729809', None, None, None, '1', None, '63.96519761', '24.9271', None], 'id': '185729809', 'symbol': 'SOL/USDT:USDT', 'notional': 2.5, 'marginMode': 'isolated', 'liquidationPrice': 178.816140956, 'entryPrice': 199.4168, 'unrealizedPnl': -34.091999999999985, 'percentage': -6.838340601193077, 'contracts': None, 'contractSize': 1.0, 'markPrice': None, 'lastPrice': None, 'side': 'long', 'hedged': None, 'timestamp': None, 'datetime': None, 'lastUpdateTimestamp': None, 'maintenanceMargin': 24.9271, 'maintenanceMarginPercentage': None, 'collateral': 63.96519761, 'initialMargin': None, 'initialMarginPercentage': None, 'leverage': 7.7939570051771465, 'marginRatio': None, 'stopLossPrice': None, 'takeProfitPrice': None}
2025-10-17T05:46:16.496062102Z INFO:database.models:Threshold aggiornati per posizione 219984293952
2025-10-17T05:46:16.853264202Z INFO:database.models:Threshold aggiornati per posizione cfa71839-5211-40b4-857d-4ebf087010a5
2025-10-17T05:46:16.853316963Z Liquidation price recuperato da bitfinex: 178.816140956
2025-10-17T05:46:16.853335304Z Calcolo threshold long: entry=195.1288, liq=178.816140956, diff=16.3127, threshold=179.6318
2025-10-17T05:46:16.853342724Z Calcolo threshold long: entry=195.1288, liq=178.816140956, diff=16.3127, threshold=182.0787
2025-10-17T05:46:16.853348494Z Liquidation price recuperato da bitmex: 225.26
2025-10-17T05:46:16.853353375Z Calcolo threshold short: entry=195.6624, liq=225.26, diff=29.5976, threshold=223.7801
2025-10-17T05:46:16.853357655Z Calcolo threshold short: entry=195.6624, liq=225.26, diff=29.5976, threshold=219.3405
2025-10-17T06:06:07.788881347Z ==> Running 'PYTHONPATH=. python monitor/threshold_monitoring.py'
2025-10-17T06:06:08.692685561Z INFO:database.models:Connesso a MongoDB
2025-10-17T06:06:08.692774392Z INFO:database.models:PositionManager inizializzato
2025-10-17T06:06:12.925207716Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T06:06:13.773272138Z INFO:trading.exchange_manager:Exchange bitmex inizializzato con successo
2025-10-17T06:06:15.854410359Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T06:06:16.54785208Z INFO:trading.exchange_manager:Posizione bitfinex: {'info': ['tSOLF0:USTF0', 'ACTIVE', '2.5', '199.4168', '0', '0', '-33.367000000000004', '-6.692916544644184', '178.816140956', '7.7939570051771465', None, '185729809', None, None, None, '1', None, '63.96519761', '24.9271', None], 'id': '185729809', 'symbol': 'SOL/USDT:USDT', 'notional': 2.5, 'marginMode': 'isolated', 'liquidationPrice': 178.816140956, 'entryPrice': 199.4168, 'unrealizedPnl': -33.367000000000004, 'percentage': -6.692916544644184, 'contracts': None, 'contractSize': 1.0, 'markPrice': None, 'lastPrice': None, 'side': 'long', 'hedged': None, 'timestamp': None, 'datetime': None, 'lastUpdateTimestamp': None, 'maintenanceMargin': 24.9271, 'maintenanceMarginPercentage': None, 'collateral': 63.96519761, 'initialMargin': None, 'initialMarginPercentage': None, 'leverage': 7.7939570051771465, 'marginRatio': None, 'stopLossPrice': None, 'takeProfitPrice': None}
2025-10-17T06:06:16.561137097Z INFO:database.models:Threshold aggiornati per posizione 219984293952
2025-10-17T06:06:16.84442934Z INFO:database.models:Threshold aggiornati per posizione cfa71839-5211-40b4-857d-4ebf087010a5
2025-10-17T06:06:16.844454231Z Liquidation price recuperato da bitfinex: 178.816140956
2025-10-17T06:06:16.844473681Z Calcolo threshold long: entry=195.1288, liq=178.816140956, diff=16.3127, threshold=179.6318
2025-10-17T06:06:16.844481271Z Calcolo threshold long: entry=195.1288, liq=178.816140956, diff=16.3127, threshold=182.0787
2025-10-17T06:06:16.844487451Z Liquidation price recuperato da bitmex: 225.26
2025-10-17T06:06:16.844492912Z Calcolo threshold short: entry=195.6624, liq=225.26, diff=29.5976, threshold=223.7801
2025-10-17T06:06:16.844496832Z Calcolo threshold short: entry=195.6624, liq=225.26, diff=29.5976, threshold=219.3405
2025-10-17T06:26:08.368836075Z ==> Running 'PYTHONPATH=. python monitor/threshold_monitoring.py'
2025-10-17T06:26:09.46553878Z INFO:database.models:Connesso a MongoDB
2025-10-17T06:26:09.466278286Z INFO:database.models:PositionManager inizializzato
2025-10-17T06:26:14.956103418Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T06:26:17.056897244Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T06:26:17.880617821Z INFO:trading.exchange_manager:Exchange bitmex inizializzato con successo
2025-10-17T06:26:18.033929515Z INFO:trading.exchange_manager:Posizione bitfinex: {'info': ['tSOLF0:USTF0', 'ACTIVE', '2.5', '199.4168', '0', '0', '-38.41699999999996', '-7.705870317846833', '178.816140956', '7.7939570051771465', None, '185729809', None, None, None, '1', None, '63.96519761', '24.9271', None], 'id': '185729809', 'symbol': 'SOL/USDT:USDT', 'notional': 2.5, 'marginMode': 'isolated', 'liquidationPrice': 178.816140956, 'entryPrice': 199.4168, 'unrealizedPnl': -38.41699999999996, 'percentage': -7.705870317846833, 'contracts': None, 'contractSize': 1.0, 'markPrice': None, 'lastPrice': None, 'side': 'long', 'hedged': None, 'timestamp': None, 'datetime': None, 'lastUpdateTimestamp': None, 'maintenanceMargin': 24.9271, 'maintenanceMarginPercentage': None, 'collateral': 63.96519761, 'initialMargin': None, 'initialMarginPercentage': None, 'leverage': 7.7939570051771465, 'marginRatio': None, 'stopLossPrice': None, 'takeProfitPrice': None}
2025-10-17T06:26:18.046393113Z INFO:database.models:Threshold aggiornati per posizione 219984293952
2025-10-17T06:26:18.322233652Z INFO:database.models:Threshold aggiornati per posizione cfa71839-5211-40b4-857d-4ebf087010a5
2025-10-17T06:26:18.322303224Z Liquidation price recuperato da bitfinex: 178.816140956
2025-10-17T06:26:18.322321494Z Calcolo threshold long: entry=195.1288, liq=178.816140956, diff=16.3127, threshold=179.6318
2025-10-17T06:26:18.322328344Z Calcolo threshold long: entry=195.1288, liq=178.816140956, diff=16.3127, threshold=182.0787
2025-10-17T06:26:18.322332944Z Liquidation price recuperato da bitmex: 225.26
2025-10-17T06:26:18.322336524Z Calcolo threshold short: entry=195.6624, liq=225.26, diff=29.5976, threshold=223.7801
2025-10-17T06:26:18.322339974Z Calcolo threshold short: entry=195.6624, liq=225.26, diff=29.5976, threshold=219.3405
2025-10-17T06:46:07.971672302Z ==> Running 'PYTHONPATH=. python monitor/threshold_monitoring.py'
2025-10-17T06:46:08.865774762Z INFO:database.models:Connesso a MongoDB
2025-10-17T06:46:08.865938776Z INFO:database.models:PositionManager inizializzato
2025-10-17T07:06:07.346450798Z ==> Running 'PYTHONPATH=. python monitor/threshold_monitoring.py'
2025-10-17T07:06:08.151294729Z INFO:database.models:Connesso a MongoDB
2025-10-17T07:06:08.151356811Z INFO:database.models:PositionManager inizializzato
2025-10-17T07:26:08.60785246Z ==> Running 'PYTHONPATH=. python monitor/threshold_monitoring.py'
2025-10-17T07:26:09.414676964Z INFO:database.models:Connesso a MongoDB
2025-10-17T07:26:09.414729265Z INFO:database.models:PositionManager inizializzato
2025-10-17T07:46:09.513107881Z ==> Running 'PYTHONPATH=. python monitor/threshold_monitoring.py'
2025-10-17T07:46:10.321991631Z INFO:database.models:Connesso a MongoDB
2025-10-17T07:46:10.322127824Z INFO:database.models:PositionManager inizializzato
2025-10-17T08:06:07.716998681Z ==> Running 'PYTHONPATH=. python monitor/threshold_monitoring.py'
2025-10-17T08:06:08.788145429Z INFO:database.models:Connesso a MongoDB
2025-10-17T08:06:08.78820217Z INFO:database.models:PositionManager inizializzato
2025-10-17T08:26:09.150732777Z ==> Running 'PYTHONPATH=. python monitor/threshold_monitoring.py'
2025-10-17T08:26:09.946258715Z INFO:database.models:Connesso a MongoDB
2025-10-17T08:26:09.946396388Z INFO:database.models:PositionManager inizializzato
2025-10-17T08:46:07.115181469Z ==> Running 'PYTHONPATH=. python monitor/threshold_monitoring.py'
2025-10-17T08:46:07.928233567Z INFO:database.models:Connesso a MongoDB
2025-10-17T08:46:07.928273938Z INFO:database.models:PositionManager inizializzato