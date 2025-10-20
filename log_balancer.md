2025-10-17T05:33:07.488239035Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T05:33:08.903270203Z INFO:database.models:Connesso a MongoDB
2025-10-17T05:33:08.903448607Z INFO:database.models:PositionManager inizializzato
2025-10-17T05:33:12.733712648Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T05:33:12.733915162Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T05:33:12.787305876Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 1']
2025-10-17T05:33:12.787331777Z INFO:__main__:Trovati 1 bot da processare su 8 totali
2025-10-17T05:33:12.787348887Z INFO:__main__:Processando bot 68e81c024fb2ad9fa9d63361 con leva target 8.0X
2025-10-17T05:33:12.789279918Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T05:33:12.789303669Z INFO:__main__:Trovate 2 posizioni aperte per bot 68e81c024fb2ad9fa9d63361
2025-10-17T05:33:12.816646785Z INFO:__main__:Avvio consolidamento wallet Bitfinex per bot 68e81c024fb2ad9fa9d63361
2025-10-17T05:33:12.816671715Z INFO:__main__:Inizio consolidamento wallet Bitfinex per utente 68b9d887c6a1151bcce4cd50
2025-10-17T05:33:14.900175932Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T05:33:15.608765789Z INFO:__main__:Saldi wallet Bitfinex: {'exchange': {}, 'margin': {}, 'funding': {}}
2025-10-17T05:33:15.60879353Z INFO:__main__:Nessun trasferimento necessario - fondi già consolidati
2025-10-17T05:33:15.60879779Z INFO:__main__:Consolidamento wallet completato per bot 68e81c024fb2ad9fa9d63361
2025-10-17T05:33:16.425554684Z INFO:trading.exchange_manager:Exchange bitmex inizializzato con successo
2025-10-17T05:33:16.425584205Z INFO:__main__:Exchange bitmex inizializzato con successo
2025-10-17T05:33:18.521056068Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T05:33:18.521090579Z INFO:__main__:Exchange bitfinex inizializzato con successo
2025-10-17T05:33:18.521097649Z INFO:__main__:Analisi posizione 219984293952 su bitfinex (SOL/USDT:USDT)
2025-10-17T05:33:19.217310281Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 0 - Notional: 2.5
2025-10-17T05:33:19.892723148Z INFO:trading.exchange_manager:Prezzo SOLANA su bitfinex: 187.15
2025-10-17T05:33:19.892747808Z INFO:__main__:=== DEBUG CALCOLO LEVA BITFINEX ===
2025-10-17T05:33:19.892753168Z INFO:__main__:Size posizione (notional): 2.5 SOL
2025-10-17T05:33:19.892770049Z INFO:__main__:Prezzo corrente SOL: 187.1500 USDT
2025-10-17T05:33:19.892774929Z INFO:__main__:Margine/Collaterale: 63.9652 USDT
2025-10-17T05:33:19.892815739Z INFO:__main__:Calcolo: |2.5 * 187.1500| / 63.9652 = 467.8750 / 63.9652 = 7.3145X
2025-10-17T05:33:19.89283936Z INFO:__main__:Leva effettiva finale: 7.31X
2025-10-17T05:33:19.892863271Z INFO:__main__:=== FINE DEBUG CALCOLO LEVA ===
2025-10-17T05:33:19.892971323Z INFO:__main__:Leva effettiva calcolata: 7.31X
2025-10-17T05:33:19.892980573Z INFO:__main__:Leva effettiva: 7.31X, Leva target: 8.00X
2025-10-17T05:33:19.892985733Z INFO:__main__:Deviazione leva: 0.69X - Ribilanciamento necessario
2025-10-17T05:33:20.495643011Z INFO:trading.exchange_manager:Prezzo SOLANA su bitfinex: 187.15
2025-10-17T05:33:20.495677682Z INFO:__main__:Size posizione: 2.5 SOL
2025-10-17T05:33:20.495699632Z INFO:__main__:Prezzo corrente: 187.1500 USDT
2025-10-17T05:33:20.495714603Z INFO:__main__:Prezzo entrata: 199.4168 USDT
2025-10-17T05:33:20.495730203Z INFO:__main__:PnL non realizzato: -30.5920 USDT
2025-10-17T05:33:20.495771844Z INFO:__main__:Valore nominale posizione: 467.88 USDT
2025-10-17T05:33:20.495796274Z INFO:__main__:Margine base per 8.0X: 58.48 USDT
2025-10-17T05:33:20.495832345Z INFO:__main__:Margine attuale: 63.97 USDT
2025-10-17T05:33:20.495892036Z INFO:__main__:Margine target: 89.08 USDT
2025-10-17T05:33:20.495941708Z INFO:__main__:Differenza: 25.11 USDT
2025-10-17T05:33:20.496008249Z INFO:__main__:Conversione simbolo: SOL/USDT:USDT -> tSOLF0:USTF0
2025-10-17T05:33:20.496103361Z INFO:__main__:Impostazione collaterale 89.08 per posizione tSOLF0:USTF0
2025-10-17T05:33:20.92279374Z INFO:__main__:Risposta API: [[1]]
2025-10-17T05:33:20.922821991Z INFO:__main__:Collaterale impostato con successo
2025-10-17T05:33:20.923795172Z INFO:__main__:Collaterale aggiustato con successo: 63.97 -> 89.08 USDT
2025-10-17T05:33:25.008128735Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T05:33:25.728949684Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 0 - Notional: 2.5
2025-10-17T05:33:25.728969275Z INFO:__main__:Leva effettiva dopo aggiustamento: 7.7940X
2025-10-17T05:33:25.728980295Z INFO:__main__:Leva aggiustata con successo (target: 8.0X, attuale: 7.7940X)
2025-10-17T05:33:25.733840529Z INFO:__main__:Ribilanciamento completato con successo per posizione 219984293952
2025-10-17T05:33:25.733871729Z INFO:__main__:Analisi posizione cfa71839-5211-40b4-857d-4ebf087010a5 su bitmex (SOL/USDT:USDT)
2025-10-17T05:33:25.984942507Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 25000.0
2025-10-17T05:33:25.985133201Z INFO:__main__:Leva effettiva calcolata: 4.78X
2025-10-17T05:33:25.985159092Z INFO:__main__:Leva effettiva: 4.78X, Leva target: 8.00X
2025-10-17T05:33:25.985246224Z INFO:__main__:Deviazione leva: 3.22X - Ribilanciamento necessario
2025-10-17T05:33:25.985259074Z INFO:__main__:Simbolo per posCross: SOL/USDT:USDT
2025-10-17T05:33:26.49067067Z INFO:__main__:Trovate 1 posizioni totali su BitMEX
2025-10-17T05:33:26.49070186Z INFO:__main__:posCross BitMEX per SOL/USDT:USDT: 939501 Satoshi = 0.939501 USDT
2025-10-17T05:33:26.490714731Z INFO:__main__:posCross BitMEX per SOL/USDT:USDT: 939501 Satoshi = 0.939501 USDT
2025-10-17T05:33:26.4907196Z INFO:__main__:Riduzione limitata dal posCross di BitMEX:
2025-10-17T05:33:26.490727771Z INFO:__main__:  - Riduzione richiesta: 39.37 USDT
2025-10-17T05:33:26.490779702Z INFO:__main__:  - Margine max rimovibile: 0.94 USDT
2025-10-17T05:33:26.490799752Z INFO:__main__:  - Riduzione sicura (90%): 0.85 USDT
2025-10-17T05:33:26.490841633Z INFO:__main__:  - Riduzione finale: 0.85 USDT
2025-10-17T05:33:26.490892354Z INFO:__main__:Margine attuale: 97.89 USDT
2025-10-17T05:33:26.490952176Z INFO:__main__:Margine target: 58.52 USDT
2025-10-17T05:33:26.490957516Z INFO:__main__:Differenza: -0.85 USDT
2025-10-17T05:33:26.491013817Z INFO:__main__:Differenza inferiore a 1 USDT, nessun aggiustamento necessario
2025-10-17T05:33:26.491024477Z INFO:__main__:Nessun aggiustamento necessario
2025-10-17T05:33:26.491083038Z INFO:__main__:Ribilanciamento completato con successo per posizione cfa71839-5211-40b4-857d-4ebf087010a5
2025-10-17T05:33:26.491131649Z INFO:__main__:✅ Bot 68e81c024fb2ad9fa9d63361 processato con successo - 2 posizioni bilanciate (stato: RUNNING)
2025-10-17T05:33:26.491212731Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 13.76s)
2025-10-17T05:33:26.491255892Z INFO:__main__:=== Fine Balancer ===
2025-10-17T05:48:10.822380234Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T05:48:12.387635098Z INFO:database.models:Connesso a MongoDB
2025-10-17T05:48:12.387774341Z INFO:database.models:PositionManager inizializzato
2025-10-17T05:48:15.90394966Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T05:48:15.90396892Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T05:48:15.966216604Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 1']
2025-10-17T05:48:15.966238084Z INFO:__main__:Trovati 1 bot da processare su 8 totali
2025-10-17T05:48:15.966257905Z INFO:__main__:Processando bot 68e81c024fb2ad9fa9d63361 con leva target 8.0X
2025-10-17T05:48:15.968171706Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T05:48:15.968184776Z INFO:__main__:Trovate 2 posizioni aperte per bot 68e81c024fb2ad9fa9d63361
2025-10-17T05:48:15.991562647Z INFO:__main__:Avvio consolidamento wallet Bitfinex per bot 68e81c024fb2ad9fa9d63361
2025-10-17T05:48:15.991583997Z INFO:__main__:Inizio consolidamento wallet Bitfinex per utente 68b9d887c6a1151bcce4cd50
2025-10-17T05:48:18.08530755Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T05:48:18.789604715Z INFO:__main__:Saldi wallet Bitfinex: {'exchange': {}, 'margin': {}, 'funding': {}}
2025-10-17T05:48:18.789626355Z INFO:__main__:Nessun trasferimento necessario - fondi già consolidati
2025-10-17T05:48:18.789630825Z INFO:__main__:Consolidamento wallet completato per bot 68e81c024fb2ad9fa9d63361
2025-10-17T05:48:20.904170374Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T05:48:20.904201315Z INFO:__main__:Exchange bitfinex inizializzato con successo
2025-10-17T05:48:21.737461703Z INFO:trading.exchange_manager:Exchange bitmex inizializzato con successo
2025-10-17T05:48:21.737490354Z INFO:__main__:Exchange bitmex inizializzato con successo
2025-10-17T05:48:21.737513024Z INFO:__main__:Analisi posizione 219984293952 su bitfinex (SOL/USDT:USDT)
2025-10-17T05:48:21.850218006Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 0 - Notional: 2.5
2025-10-17T05:48:22.482043314Z INFO:trading.exchange_manager:Prezzo SOLANA su bitfinex: 185.73
2025-10-17T05:48:22.482068935Z INFO:__main__:=== DEBUG CALCOLO LEVA BITFINEX ===
2025-10-17T05:48:22.482082085Z INFO:__main__:Size posizione (notional): 2.5 SOL
2025-10-17T05:48:22.482185017Z INFO:__main__:Prezzo corrente SOL: 185.7300 USDT
2025-10-17T05:48:22.482195268Z INFO:__main__:Margine/Collaterale: 63.9652 USDT
2025-10-17T05:48:22.482200998Z INFO:__main__:Calcolo: |2.5 * 185.7300| / 63.9652 = 464.3250 / 63.9652 = 7.2590X
2025-10-17T05:48:22.482208398Z INFO:__main__:Leva effettiva finale: 7.26X
2025-10-17T05:48:22.482274149Z INFO:__main__:=== FINE DEBUG CALCOLO LEVA ===
2025-10-17T05:48:22.4822845Z INFO:__main__:Leva effettiva calcolata: 7.26X
2025-10-17T05:48:22.4822941Z INFO:__main__:Leva effettiva: 7.26X, Leva target: 8.00X
2025-10-17T05:48:22.482348691Z INFO:__main__:Deviazione leva: 0.74X - Ribilanciamento necessario
2025-10-17T05:48:23.103361508Z INFO:trading.exchange_manager:Prezzo SOLANA su bitfinex: 185.73
2025-10-17T05:48:23.103390699Z INFO:__main__:Size posizione: 2.5 SOL
2025-10-17T05:48:23.103397189Z INFO:__main__:Prezzo corrente: 185.7300 USDT
2025-10-17T05:48:23.103416999Z INFO:__main__:Prezzo entrata: 199.4168 USDT
2025-10-17T05:48:23.10342326Z INFO:__main__:PnL non realizzato: -34.4920 USDT
2025-10-17T05:48:23.10344124Z INFO:__main__:Valore nominale posizione: 464.32 USDT
2025-10-17T05:48:23.10345597Z INFO:__main__:Margine base per 8.0X: 58.04 USDT
2025-10-17T05:48:23.103490241Z INFO:__main__:Margine attuale: 63.97 USDT
2025-10-17T05:48:23.103527482Z INFO:__main__:Margine target: 92.53 USDT
2025-10-17T05:48:23.103536912Z INFO:__main__:Differenza: 28.57 USDT
2025-10-17T05:48:23.103543512Z INFO:__main__:Conversione simbolo: SOL/USDT:USDT -> tSOLF0:USTF0
2025-10-17T05:48:23.103670675Z INFO:__main__:Impostazione collaterale 92.53 per posizione tSOLF0:USTF0
2025-10-17T05:48:23.304779238Z INFO:__main__:Risposta API: [[1]]
2025-10-17T05:48:23.304802778Z INFO:__main__:Collaterale impostato con successo
2025-10-17T05:48:23.30580605Z INFO:__main__:Collaterale aggiustato con successo: 63.97 -> 92.53 USDT
2025-10-17T05:48:27.391529158Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T05:48:28.089906371Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 0 - Notional: 2.5
2025-10-17T05:48:28.089954841Z INFO:__main__:Leva effettiva dopo aggiustamento: 7.7940X
2025-10-17T05:48:28.090050194Z INFO:__main__:Leva aggiustata con successo (target: 8.0X, attuale: 7.7940X)
2025-10-17T05:48:28.094349436Z INFO:__main__:Ribilanciamento completato con successo per posizione 219984293952
2025-10-17T05:48:28.094373596Z INFO:__main__:Analisi posizione cfa71839-5211-40b4-857d-4ebf087010a5 su bitmex (SOL/USDT:USDT)
2025-10-17T05:48:28.36655646Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 25000.0
2025-10-17T05:48:28.366585071Z INFO:__main__:Leva effettiva calcolata: 4.54X
2025-10-17T05:48:28.366599961Z INFO:__main__:Leva effettiva: 4.54X, Leva target: 8.00X
2025-10-17T05:48:28.366611391Z INFO:__main__:Deviazione leva: 3.46X - Ribilanciamento necessario
2025-10-17T05:48:28.366668962Z INFO:__main__:Simbolo per posCross: SOL/USDT:USDT
2025-10-17T05:48:28.880166999Z INFO:__main__:Trovate 1 posizioni totali su BitMEX
2025-10-17T05:48:28.880186849Z INFO:__main__:posCross BitMEX per SOL/USDT:USDT: 939501 Satoshi = 0.939501 USDT
2025-10-17T05:48:28.8802111Z INFO:__main__:posCross BitMEX per SOL/USDT:USDT: 939501 Satoshi = 0.939501 USDT
2025-10-17T05:48:28.88023315Z INFO:__main__:Riduzione limitata dal posCross di BitMEX:
2025-10-17T05:48:28.880251541Z INFO:__main__:  - Riduzione richiesta: 44.22 USDT
2025-10-17T05:48:28.880292362Z INFO:__main__:  - Margine max rimovibile: 0.94 USDT
2025-10-17T05:48:28.880337583Z INFO:__main__:  - Riduzione sicura (90%): 0.85 USDT
2025-10-17T05:48:28.880346173Z INFO:__main__:  - Riduzione finale: 0.85 USDT
2025-10-17T05:48:28.880390314Z INFO:__main__:Margine attuale: 102.20 USDT
2025-10-17T05:48:28.880420845Z INFO:__main__:Margine target: 57.98 USDT
2025-10-17T05:48:28.880477186Z INFO:__main__:Differenza: -0.85 USDT
2025-10-17T05:48:28.880485936Z INFO:__main__:Differenza inferiore a 1 USDT, nessun aggiustamento necessario
2025-10-17T05:48:28.880505636Z INFO:__main__:Nessun aggiustamento necessario
2025-10-17T05:48:28.880543167Z INFO:__main__:Ribilanciamento completato con successo per posizione cfa71839-5211-40b4-857d-4ebf087010a5
2025-10-17T05:48:28.880602598Z INFO:__main__:✅ Bot 68e81c024fb2ad9fa9d63361 processato con successo - 2 posizioni bilanciate (stato: RUNNING)
2025-10-17T05:48:28.88066447Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 12.98s)
2025-10-17T05:48:28.880718591Z INFO:__main__:=== Fine Balancer ===
2025-10-17T06:03:10.963975249Z INFO:database.models:PositionManager inizializzato
2025-10-17T06:03:14.18346741Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T06:03:14.18348788Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T06:03:14.2320912Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 1']
2025-10-17T06:03:14.23211269Z INFO:__main__:Trovati 1 bot da processare su 8 totali
2025-10-17T06:03:14.232195292Z INFO:__main__:Processando bot 68e81c024fb2ad9fa9d63361 con leva target 8.0X
2025-10-17T06:03:14.234043227Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T06:03:14.234058287Z INFO:__main__:Trovate 2 posizioni aperte per bot 68e81c024fb2ad9fa9d63361
2025-10-17T06:03:14.26609712Z INFO:__main__:Avvio consolidamento wallet Bitfinex per bot 68e81c024fb2ad9fa9d63361
2025-10-17T06:03:14.266114521Z INFO:__main__:Inizio consolidamento wallet Bitfinex per utente 68b9d887c6a1151bcce4cd50
2025-10-17T06:03:16.349511601Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T06:03:17.047472642Z INFO:__main__:Saldi wallet Bitfinex: {'exchange': {}, 'margin': {}, 'funding': {}}
2025-10-17T06:03:17.047505372Z INFO:__main__:Nessun trasferimento necessario - fondi già consolidati
2025-10-17T06:03:17.047517543Z INFO:__main__:Consolidamento wallet completato per bot 68e81c024fb2ad9fa9d63361
2025-10-17T06:03:19.132111556Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T06:03:19.132143847Z INFO:__main__:Exchange bitfinex inizializzato con successo
2025-10-17T06:03:19.956457194Z INFO:trading.exchange_manager:Exchange bitmex inizializzato con successo
2025-10-17T06:03:19.956478004Z INFO:__main__:Exchange bitmex inizializzato con successo
2025-10-17T06:03:19.956489575Z INFO:__main__:Analisi posizione 219984293952 su bitfinex (SOL/USDT:USDT)
2025-10-17T06:03:20.013420724Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 0 - Notional: 2.5
2025-10-17T06:03:20.702047676Z INFO:trading.exchange_manager:Prezzo SOLANA su bitfinex: 185.96
2025-10-17T06:03:20.702071476Z INFO:__main__:=== DEBUG CALCOLO LEVA BITFINEX ===
2025-10-17T06:03:20.702077666Z INFO:__main__:Size posizione (notional): 2.5 SOL
2025-10-17T06:03:20.702089636Z INFO:__main__:Prezzo corrente SOL: 185.9600 USDT
2025-10-17T06:03:20.702094496Z INFO:__main__:Margine/Collaterale: 63.9652 USDT
2025-10-17T06:03:20.702110477Z INFO:__main__:Calcolo: |2.5 * 185.9600| / 63.9652 = 464.9000 / 63.9652 = 7.2680X
2025-10-17T06:03:20.702124067Z INFO:__main__:Leva effettiva finale: 7.27X
2025-10-17T06:03:20.702183868Z INFO:__main__:=== FINE DEBUG CALCOLO LEVA ===
2025-10-17T06:03:20.702195388Z INFO:__main__:Leva effettiva calcolata: 7.27X
2025-10-17T06:03:20.702223169Z INFO:__main__:Leva effettiva: 7.27X, Leva target: 8.00X
2025-10-17T06:03:20.702229329Z INFO:__main__:Deviazione leva: 0.73X - Ribilanciamento necessario
2025-10-17T06:03:21.324129835Z INFO:trading.exchange_manager:Prezzo SOLANA su bitfinex: 185.96
2025-10-17T06:03:21.324189686Z INFO:__main__:Size posizione: 2.5 SOL
2025-10-17T06:03:21.324206006Z INFO:__main__:Prezzo corrente: 185.9600 USDT
2025-10-17T06:03:21.324211916Z INFO:__main__:Prezzo entrata: 199.4168 USDT
2025-10-17T06:03:21.324217596Z INFO:__main__:PnL non realizzato: -33.5420 USDT
2025-10-17T06:03:21.324230266Z INFO:__main__:Valore nominale posizione: 464.90 USDT
2025-10-17T06:03:21.324243947Z INFO:__main__:Margine base per 8.0X: 58.11 USDT
2025-10-17T06:03:21.324263797Z INFO:__main__:Margine attuale: 63.97 USDT
2025-10-17T06:03:21.324292198Z INFO:__main__:Margine target: 91.65 USDT
2025-10-17T06:03:21.324349049Z INFO:__main__:Differenza: 27.69 USDT
2025-10-17T06:03:21.324354339Z INFO:__main__:Conversione simbolo: SOL/USDT:USDT -> tSOLF0:USTF0
2025-10-17T06:03:21.324466401Z INFO:__main__:Impostazione collaterale 91.65 per posizione tSOLF0:USTF0
2025-10-17T06:03:21.607431523Z INFO:__main__:Risposta API: [[1]]
2025-10-17T06:03:21.607454454Z INFO:__main__:Collaterale impostato con successo
2025-10-17T06:03:21.608751939Z INFO:__main__:Collaterale aggiustato con successo: 63.97 -> 91.65 USDT
2025-10-17T06:03:25.705350357Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T06:03:26.420912464Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 0 - Notional: 2.5
2025-10-17T06:03:26.420940305Z INFO:__main__:Leva effettiva dopo aggiustamento: 7.7940X
2025-10-17T06:03:26.420951905Z INFO:__main__:Leva aggiustata con successo (target: 8.0X, attuale: 7.7940X)
2025-10-17T06:03:26.425107714Z INFO:__main__:Ribilanciamento completato con successo per posizione 219984293952
2025-10-17T06:03:26.425133445Z INFO:__main__:Analisi posizione cfa71839-5211-40b4-857d-4ebf087010a5 su bitmex (SOL/USDT:USDT)
2025-10-17T06:03:26.68889427Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 25000.0
2025-10-17T06:03:26.688924231Z INFO:__main__:Leva effettiva calcolata: 4.61X
2025-10-17T06:03:26.688939021Z INFO:__main__:Leva effettiva: 4.61X, Leva target: 8.00X
2025-10-17T06:03:26.688946071Z INFO:__main__:Deviazione leva: 3.39X - Ribilanciamento necessario
2025-10-17T06:03:26.688968022Z INFO:__main__:Simbolo per posCross: SOL/USDT:USDT
2025-10-17T06:03:27.207130023Z INFO:__main__:Trovate 1 posizioni totali su BitMEX
2025-10-17T06:03:27.207168084Z INFO:__main__:posCross BitMEX per SOL/USDT:USDT: 939501 Satoshi = 0.939501 USDT
2025-10-17T06:03:27.207181674Z INFO:__main__:posCross BitMEX per SOL/USDT:USDT: 939501 Satoshi = 0.939501 USDT
2025-10-17T06:03:27.207186134Z INFO:__main__:Riduzione limitata dal posCross di BitMEX:
2025-10-17T06:03:27.207230115Z INFO:__main__:  - Riduzione richiesta: 42.79 USDT
2025-10-17T06:03:27.207253875Z INFO:__main__:  - Margine max rimovibile: 0.94 USDT
2025-10-17T06:03:27.207297756Z INFO:__main__:  - Riduzione sicura (90%): 0.85 USDT
2025-10-17T06:03:27.207306776Z INFO:__main__:  - Riduzione finale: 0.85 USDT
2025-10-17T06:03:27.207351397Z INFO:__main__:Margine attuale: 100.93 USDT
2025-10-17T06:03:27.207390768Z INFO:__main__:Margine target: 58.14 USDT
2025-10-17T06:03:27.207403268Z INFO:__main__:Differenza: -0.85 USDT
2025-10-17T06:03:27.207410658Z INFO:__main__:Differenza inferiore a 1 USDT, nessun aggiustamento necessario
2025-10-17T06:03:27.2074889Z INFO:__main__:Nessun aggiustamento necessario
2025-10-17T06:03:27.20750223Z INFO:__main__:Ribilanciamento completato con successo per posizione cfa71839-5211-40b4-857d-4ebf087010a5
2025-10-17T06:03:27.207542971Z INFO:__main__:✅ Bot 68e81c024fb2ad9fa9d63361 processato con successo - 2 posizioni bilanciate (stato: RUNNING)
2025-10-17T06:03:27.207601132Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 13.02s)
2025-10-17T06:03:27.207639713Z INFO:__main__:=== Fine Balancer ===
2025-10-17T06:18:43.033863658Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T06:18:44.151258474Z INFO:database.models:Connesso a MongoDB
2025-10-17T06:18:44.151357306Z INFO:database.models:PositionManager inizializzato
2025-10-17T06:18:47.247271041Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T06:18:47.247289971Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T06:18:47.295600892Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 1']
2025-10-17T06:18:47.295622062Z INFO:__main__:Trovati 1 bot da processare su 8 totali
2025-10-17T06:18:47.295630882Z INFO:__main__:Processando bot 68e81c024fb2ad9fa9d63361 con leva target 8.0X
2025-10-17T06:18:47.29736754Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T06:18:47.29738134Z INFO:__main__:Trovate 2 posizioni aperte per bot 68e81c024fb2ad9fa9d63361
2025-10-17T06:18:47.319450556Z INFO:__main__:Avvio consolidamento wallet Bitfinex per bot 68e81c024fb2ad9fa9d63361
2025-10-17T06:18:47.319463796Z INFO:__main__:Inizio consolidamento wallet Bitfinex per utente 68b9d887c6a1151bcce4cd50
2025-10-17T06:18:49.396569029Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T06:18:50.098406101Z INFO:__main__:Saldi wallet Bitfinex: {'exchange': {}, 'margin': {}, 'funding': {}}
2025-10-17T06:18:50.098429272Z INFO:__main__:Nessun trasferimento necessario - fondi già consolidati
2025-10-17T06:18:50.098436552Z INFO:__main__:Consolidamento wallet completato per bot 68e81c024fb2ad9fa9d63361
2025-10-17T06:18:52.184637461Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T06:18:52.184670082Z INFO:__main__:Exchange bitfinex inizializzato con successo
2025-10-17T06:18:53.001396009Z INFO:trading.exchange_manager:Exchange bitmex inizializzato con successo
2025-10-17T06:18:53.001416289Z INFO:__main__:Exchange bitmex inizializzato con successo
2025-10-17T06:18:53.00142398Z INFO:__main__:Analisi posizione 219984293952 su bitfinex (SOL/USDT:USDT)
2025-10-17T06:18:53.070999399Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 0 - Notional: 2.5
2025-10-17T06:18:53.749870446Z INFO:trading.exchange_manager:Prezzo SOLANA su bitfinex: 185.67
2025-10-17T06:18:53.749896506Z INFO:__main__:=== DEBUG CALCOLO LEVA BITFINEX ===
2025-10-17T06:18:53.749899896Z INFO:__main__:Size posizione (notional): 2.5 SOL
2025-10-17T06:18:53.749918277Z INFO:__main__:Prezzo corrente SOL: 185.6700 USDT
2025-10-17T06:18:53.749926307Z INFO:__main__:Margine/Collaterale: 63.9652 USDT
2025-10-17T06:18:53.749935037Z INFO:__main__:Calcolo: |2.5 * 185.6700| / 63.9652 = 464.1750 / 63.9652 = 7.2567X
2025-10-17T06:18:53.749939057Z INFO:__main__:Leva effettiva finale: 7.26X
2025-10-17T06:18:53.749947597Z INFO:__main__:=== FINE DEBUG CALCOLO LEVA ===
2025-10-17T06:18:53.749954988Z INFO:__main__:Leva effettiva calcolata: 7.26X
2025-10-17T06:18:53.750015269Z INFO:__main__:Leva effettiva: 7.26X, Leva target: 8.00X
2025-10-17T06:18:53.750020069Z INFO:__main__:Deviazione leva: 0.74X - Ribilanciamento necessario
2025-10-17T06:18:54.369735471Z INFO:trading.exchange_manager:Prezzo SOLANA su bitfinex: 185.67
2025-10-17T06:18:54.369758502Z INFO:__main__:Size posizione: 2.5 SOL
2025-10-17T06:18:54.369760882Z INFO:__main__:Prezzo corrente: 185.6700 USDT
2025-10-17T06:18:54.369771632Z INFO:__main__:Prezzo entrata: 199.4168 USDT
2025-10-17T06:18:54.369780202Z INFO:__main__:PnL non realizzato: -35.8920 USDT
2025-10-17T06:18:54.369784692Z INFO:__main__:Valore nominale posizione: 464.17 USDT
2025-10-17T06:18:54.369793892Z INFO:__main__:Margine base per 8.0X: 58.02 USDT
2025-10-17T06:18:54.369801453Z INFO:__main__:Margine attuale: 63.97 USDT
2025-10-17T06:18:54.369824793Z INFO:__main__:Margine target: 93.91 USDT
2025-10-17T06:18:54.369877214Z INFO:__main__:Differenza: 29.95 USDT
2025-10-17T06:18:54.369926835Z INFO:__main__:Conversione simbolo: SOL/USDT:USDT -> tSOLF0:USTF0
2025-10-17T06:18:54.370016307Z INFO:__main__:Impostazione collaterale 93.91 per posizione tSOLF0:USTF0
2025-10-17T06:18:54.63096771Z INFO:__main__:Risposta API: [[1]]
2025-10-17T06:18:54.63099372Z INFO:__main__:Collaterale impostato con successo
2025-10-17T06:18:54.63236417Z INFO:__main__:Collaterale aggiustato con successo: 63.97 -> 93.91 USDT
2025-10-17T06:18:58.717427817Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T06:18:59.403796005Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 0 - Notional: 2.5
2025-10-17T06:18:59.403819666Z INFO:__main__:Leva effettiva dopo aggiustamento: 7.7940X
2025-10-17T06:18:59.403822646Z INFO:__main__:Leva aggiustata con successo (target: 8.0X, attuale: 7.7940X)
2025-10-17T06:18:59.407071766Z INFO:__main__:Ribilanciamento completato con successo per posizione 219984293952
2025-10-17T06:18:59.407102146Z INFO:__main__:Analisi posizione cfa71839-5211-40b4-857d-4ebf087010a5 su bitmex (SOL/USDT:USDT)
2025-10-17T06:18:59.670982842Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 25000.0
2025-10-17T06:18:59.671003612Z INFO:__main__:Leva effettiva calcolata: 4.47X
2025-10-17T06:18:59.671015733Z INFO:__main__:Leva effettiva: 4.47X, Leva target: 8.00X
2025-10-17T06:18:59.671023473Z INFO:__main__:Deviazione leva: 3.53X - Ribilanciamento necessario
2025-10-17T06:18:59.671055244Z INFO:__main__:Simbolo per posCross: SOL/USDT:USDT
2025-10-17T06:19:00.171995967Z INFO:__main__:Trovate 1 posizioni totali su BitMEX
2025-10-17T06:19:00.172014197Z INFO:__main__:posCross BitMEX per SOL/USDT:USDT: 939501 Satoshi = 0.939501 USDT
2025-10-17T06:19:00.172029178Z INFO:__main__:posCross BitMEX per SOL/USDT:USDT: 939501 Satoshi = 0.939501 USDT
2025-10-17T06:19:00.172079589Z INFO:__main__:Riduzione limitata dal posCross di BitMEX:
2025-10-17T06:19:00.172104469Z INFO:__main__:  - Riduzione richiesta: 45.71 USDT
2025-10-17T06:19:00.17213646Z INFO:__main__:  - Margine max rimovibile: 0.94 USDT
2025-10-17T06:19:00.17215922Z INFO:__main__:  - Riduzione sicura (90%): 0.85 USDT
2025-10-17T06:19:00.172193821Z INFO:__main__:  - Riduzione finale: 0.85 USDT
2025-10-17T06:19:00.172198281Z INFO:__main__:Margine attuale: 103.53 USDT
2025-10-17T06:19:00.172236412Z INFO:__main__:Margine target: 57.82 USDT
2025-10-17T06:19:00.172250512Z INFO:__main__:Differenza: -0.85 USDT
2025-10-17T06:19:00.172297323Z INFO:__main__:Differenza inferiore a 1 USDT, nessun aggiustamento necessario
2025-10-17T06:19:00.172304693Z INFO:__main__:Nessun aggiustamento necessario
2025-10-17T06:19:00.172354125Z INFO:__main__:Ribilanciamento completato con successo per posizione cfa71839-5211-40b4-857d-4ebf087010a5
2025-10-17T06:19:00.172405886Z INFO:__main__:✅ Bot 68e81c024fb2ad9fa9d63361 processato con successo - 2 posizioni bilanciate (stato: RUNNING)
2025-10-17T06:19:00.172464457Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 12.93s)
2025-10-17T06:19:00.172503308Z INFO:__main__:=== Fine Balancer ===
2025-10-17T06:33:19.278047917Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 0 - Notional: 2.5
2025-10-17T06:33:19.985829108Z INFO:trading.exchange_manager:Prezzo SOLANA su bitfinex: 183.07
2025-10-17T06:33:19.985893489Z INFO:__main__:=== DEBUG CALCOLO LEVA BITFINEX ===
2025-10-17T06:33:19.9859102Z INFO:__main__:Size posizione (notional): 2.5 SOL
2025-10-17T06:33:19.98591728Z INFO:__main__:Prezzo corrente SOL: 183.0700 USDT
2025-10-17T06:33:19.985969451Z INFO:__main__:Margine/Collaterale: 63.9652 USDT
2025-10-17T06:33:19.985992821Z INFO:__main__:Calcolo: |2.5 * 183.0700| / 63.9652 = 457.6750 / 63.9652 = 7.1551X
2025-10-17T06:33:19.986064403Z INFO:__main__:Leva effettiva finale: 7.16X
2025-10-17T06:33:19.986083153Z INFO:__main__:=== FINE DEBUG CALCOLO LEVA ===
2025-10-17T06:33:19.986105024Z INFO:__main__:Leva effettiva calcolata: 7.16X
2025-10-17T06:33:19.986137355Z INFO:__main__:Leva effettiva: 7.16X, Leva target: 8.00X
2025-10-17T06:33:19.986153085Z INFO:__main__:Deviazione leva: 0.84X - Ribilanciamento necessario
2025-10-17T06:33:20.552916679Z INFO:trading.exchange_manager:Prezzo SOLANA su bitfinex: 183.07
2025-10-17T06:33:20.5529544Z INFO:__main__:Size posizione: 2.5 SOL
2025-10-17T06:33:20.55296099Z INFO:__main__:Prezzo corrente: 183.0700 USDT
2025-10-17T06:33:20.55297739Z INFO:__main__:Prezzo entrata: 199.4168 USDT
2025-10-17T06:33:20.552983401Z INFO:__main__:PnL non realizzato: -40.7920 USDT
2025-10-17T06:33:20.553005911Z INFO:__main__:Valore nominale posizione: 457.67 USDT
2025-10-17T06:33:20.553069402Z INFO:__main__:Margine base per 8.0X: 57.21 USDT
2025-10-17T06:33:20.553091773Z INFO:__main__:Margine attuale: 63.97 USDT
2025-10-17T06:33:20.553133854Z INFO:__main__:Margine target: 98.00 USDT
2025-10-17T06:33:20.553180445Z INFO:__main__:Differenza: 34.04 USDT
2025-10-17T06:33:20.553189955Z INFO:__main__:Conversione simbolo: SOL/USDT:USDT -> tSOLF0:USTF0
2025-10-17T06:33:20.553304948Z INFO:__main__:Impostazione collaterale 98.00 per posizione tSOLF0:USTF0
2025-10-17T06:33:21.074503324Z INFO:__main__:Risposta API: [[1]]
2025-10-17T06:33:21.074535095Z INFO:__main__:Collaterale impostato con successo
2025-10-17T06:33:21.075762501Z INFO:__main__:Collaterale aggiustato con successo: 63.97 -> 98.00 USDT
2025-10-17T06:33:25.177700899Z INFO:trading.exchange_manager:Exchange bitfinex inizializzato con successo
2025-10-17T06:33:25.896104158Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 0 - Notional: 2.5
2025-10-17T06:33:25.896130978Z INFO:__main__:Leva effettiva dopo aggiustamento: 7.7940X
2025-10-17T06:33:25.896144459Z INFO:__main__:Leva aggiustata con successo (target: 8.0X, attuale: 7.7940X)
2025-10-17T06:33:25.899291516Z INFO:__main__:Ribilanciamento completato con successo per posizione 219984293952
2025-10-17T06:33:25.899305796Z INFO:__main__:Analisi posizione cfa71839-5211-40b4-857d-4ebf087010a5 su bitmex (SOL/USDT:USDT)
2025-10-17T06:33:26.178267004Z INFO:__main__:Posizione trovata: SOL/USDT:USDT - Size: 25000.0
2025-10-17T06:33:26.178292274Z INFO:__main__:Leva effettiva calcolata: 4.26X
2025-10-17T06:33:26.178303044Z INFO:__main__:Leva effettiva: 4.26X, Leva target: 8.00X
2025-10-17T06:33:26.178308165Z INFO:__main__:Deviazione leva: 3.74X - Ribilanciamento necessario
2025-10-17T06:33:26.178349876Z INFO:__main__:Simbolo per posCross: SOL/USDT:USDT
2025-10-17T06:33:26.674273199Z INFO:__main__:Trovate 1 posizioni totali su BitMEX
2025-10-17T06:33:26.67430046Z INFO:__main__:posCross BitMEX per SOL/USDT:USDT: 939501 Satoshi = 0.939501 USDT
2025-10-17T06:33:26.674342971Z INFO:__main__:posCross BitMEX per SOL/USDT:USDT: 939501 Satoshi = 0.939501 USDT
2025-10-17T06:33:26.675073706Z INFO:__main__:Riduzione limitata dal posCross di BitMEX:
2025-10-17T06:33:26.675085997Z INFO:__main__:  - Riduzione richiesta: 50.38 USDT
2025-10-17T06:33:26.675090607Z INFO:__main__:  - Margine max rimovibile: 0.94 USDT
2025-10-17T06:33:26.675095287Z INFO:__main__:  - Riduzione sicura (90%): 0.85 USDT
2025-10-17T06:33:26.675100097Z INFO:__main__:  - Riduzione finale: 0.85 USDT
2025-10-17T06:33:26.675104557Z INFO:__main__:Margine attuale: 107.68 USDT
2025-10-17T06:33:26.675108807Z INFO:__main__:Margine target: 57.30 USDT
2025-10-17T06:33:26.675113097Z INFO:__main__:Differenza: -0.85 USDT
2025-10-17T06:33:26.675118047Z INFO:__main__:Differenza inferiore a 1 USDT, nessun aggiustamento necessario
2025-10-17T06:33:26.675122538Z INFO:__main__:Nessun aggiustamento necessario
2025-10-17T06:33:26.675127688Z INFO:__main__:Ribilanciamento completato con successo per posizione cfa71839-5211-40b4-857d-4ebf087010a5
2025-10-17T06:33:26.675132138Z INFO:__main__:✅ Bot 68e81c024fb2ad9fa9d63361 processato con successo - 2 posizioni bilanciate (stato: RUNNING)
2025-10-17T06:33:26.675136538Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 13.25s)
2025-10-17T06:33:26.675141098Z INFO:__main__:=== Fine Balancer ===
2025-10-17T06:48:07.871215022Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T06:48:09.080229338Z INFO:database.models:Connesso a MongoDB
2025-10-17T06:48:09.080257779Z INFO:database.models:PositionManager inizializzato
2025-10-17T06:48:12.063275058Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T06:48:12.063297569Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T06:48:12.109816456Z INFO:__main__:Bot saltati: ['stopped: 6', 'transfer_requested: 1', 'external_transfer_pending: 1']
2025-10-17T06:48:12.109841436Z INFO:__main__:Nessun bot da processare trovato su 8 totali
2025-10-17T06:48:12.109865037Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 0.05s)
2025-10-17T06:48:12.109885797Z INFO:__main__:=== Fine Balancer ===
2025-10-17T07:03:07.171909215Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T07:03:08.473166215Z INFO:database.models:Connesso a MongoDB
2025-10-17T07:03:08.473302558Z INFO:database.models:PositionManager inizializzato
2025-10-17T07:03:11.878054662Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T07:03:11.878075442Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T07:03:11.924956187Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 2']
2025-10-17T07:03:11.924973158Z INFO:__main__:Nessun bot da processare trovato su 8 totali
2025-10-17T07:03:11.924983368Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 0.05s)
2025-10-17T07:03:11.925030379Z INFO:__main__:=== Fine Balancer ===
2025-10-17T07:18:07.753009086Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T07:18:09.054534714Z INFO:database.models:Connesso a MongoDB
2025-10-17T07:18:09.054629376Z INFO:database.models:PositionManager inizializzato
2025-10-17T07:18:12.37440808Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T07:18:12.374436851Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T07:18:12.424194714Z INFO:__main__:Bot saltati: ['stopped: 6', 'transfer_requested: 1', 'external_transfer_pending: 1']
2025-10-17T07:18:12.424220335Z INFO:__main__:Nessun bot da processare trovato su 8 totali
2025-10-17T07:18:12.424223615Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 0.05s)
2025-10-17T07:18:12.424227155Z INFO:__main__:=== Fine Balancer ===
2025-10-17T07:33:10.733464864Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T07:33:12.156481972Z INFO:database.models:Connesso a MongoDB
2025-10-17T07:33:12.156656716Z INFO:database.models:PositionManager inizializzato
2025-10-17T07:33:15.87078921Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T07:33:15.87081429Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T07:33:15.923905149Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 2']
2025-10-17T07:33:15.92393399Z INFO:__main__:Nessun bot da processare trovato su 8 totali
2025-10-17T07:33:15.9239796Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 0.05s)
2025-10-17T07:33:15.924005831Z INFO:__main__:=== Fine Balancer ===
2025-10-17T07:48:09.498358563Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T07:48:10.714168829Z INFO:database.models:Connesso a MongoDB
2025-10-17T07:48:10.71420562Z INFO:database.models:PositionManager inizializzato
2025-10-17T07:48:13.702958988Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T07:48:13.702983599Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T07:48:13.75305495Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 1']
2025-10-17T07:48:13.75307436Z INFO:__main__:Trovati 1 bot da processare su 8 totali
2025-10-17T07:48:13.753087681Z INFO:__main__:Processando bot 68e81c024fb2ad9fa9d63361 con leva target 8.0X
2025-10-17T07:48:13.755178939Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T07:48:13.75520553Z INFO:__main__:Nessuna posizione aperta per bot 68e81c024fb2ad9fa9d63361
2025-10-17T07:48:13.755250451Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 0.05s)
2025-10-17T07:48:13.755299112Z INFO:__main__:=== Fine Balancer ===
2025-10-17T08:03:08.417794736Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T08:03:10.016277551Z INFO:database.models:Connesso a MongoDB
2025-10-17T08:03:10.016312782Z INFO:database.models:PositionManager inizializzato
2025-10-17T08:03:14.111404871Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T08:03:14.111421681Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T08:03:14.163628082Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 1']
2025-10-17T08:03:14.163658733Z INFO:__main__:Trovati 1 bot da processare su 8 totali
2025-10-17T08:03:14.163662043Z INFO:__main__:Processando bot 68e81c024fb2ad9fa9d63361 con leva target 8.0X
2025-10-17T08:03:14.165630365Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T08:03:14.165640565Z INFO:__main__:Nessuna posizione aperta per bot 68e81c024fb2ad9fa9d63361
2025-10-17T08:03:14.165691716Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 0.05s)
2025-10-17T08:03:14.165761228Z INFO:__main__:=== Fine Balancer ===
2025-10-17T08:18:44.402502836Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T08:18:45.572913971Z INFO:database.models:Connesso a MongoDB
2025-10-17T08:18:45.573063285Z INFO:database.models:PositionManager inizializzato
2025-10-17T08:18:48.666542452Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T08:18:48.666560863Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T08:18:48.713705509Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 1']
2025-10-17T08:18:48.713724739Z INFO:__main__:Trovati 1 bot da processare su 8 totali
2025-10-17T08:18:48.71373525Z INFO:__main__:Processando bot 68e81c024fb2ad9fa9d63361 con leva target 8.0X
2025-10-17T08:18:48.715501216Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T08:18:48.715512086Z INFO:__main__:Nessuna posizione aperta per bot 68e81c024fb2ad9fa9d63361
2025-10-17T08:18:48.715564868Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 0.05s)
2025-10-17T08:18:48.715630029Z INFO:__main__:=== Fine Balancer ===
2025-10-17T08:33:43.345913997Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T08:33:44.44995413Z INFO:database.models:Connesso a MongoDB
2025-10-17T08:33:44.450048042Z INFO:database.models:PositionManager inizializzato
2025-10-17T08:33:47.45110183Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T08:33:47.451123381Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T08:33:47.503128055Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 1']
2025-10-17T08:33:47.503149816Z INFO:__main__:Trovati 1 bot da processare su 8 totali
2025-10-17T08:33:47.503158396Z INFO:__main__:Processando bot 68e81c024fb2ad9fa9d63361 con leva target 8.0X
2025-10-17T08:33:47.50492572Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T08:33:47.5049363Z INFO:__main__:Nessuna posizione aperta per bot 68e81c024fb2ad9fa9d63361
2025-10-17T08:33:47.504968661Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 0.05s)
2025-10-17T08:33:47.505006762Z INFO:__main__:=== Fine Balancer ===
2025-10-17T08:48:07.837024475Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T08:48:09.040690801Z INFO:database.models:Connesso a MongoDB
2025-10-17T08:48:09.040789423Z INFO:database.models:PositionManager inizializzato
2025-10-17T08:48:11.978824261Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T08:48:11.978849222Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T08:48:12.037908471Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 1']
2025-10-17T08:48:12.037933932Z INFO:__main__:Trovati 1 bot da processare su 8 totali
2025-10-17T08:48:12.037944732Z INFO:__main__:Processando bot 68e81c024fb2ad9fa9d63361 con leva target 8.0X
2025-10-17T08:48:12.039706253Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T08:48:12.039725074Z INFO:__main__:Nessuna posizione aperta per bot 68e81c024fb2ad9fa9d63361
2025-10-17T08:48:12.039775365Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 0.06s)
2025-10-17T08:48:12.039837646Z INFO:__main__:=== Fine Balancer ===
2025-10-17T09:03:10.580890369Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T09:03:11.744020292Z INFO:database.models:Connesso a MongoDB
2025-10-17T09:03:11.744068134Z INFO:database.models:PositionManager inizializzato
2025-10-17T09:03:14.897598569Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T09:03:14.897616559Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T09:03:14.946566044Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 1']
2025-10-17T09:03:14.946586034Z INFO:__main__:Trovati 1 bot da processare su 8 totali
2025-10-17T09:03:14.946595215Z INFO:__main__:Processando bot 68e81c024fb2ad9fa9d63361 con leva target 8.0X
2025-10-17T09:03:14.948257313Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T09:03:14.948270793Z INFO:__main__:Nessuna posizione aperta per bot 68e81c024fb2ad9fa9d63361
2025-10-17T09:03:14.948322055Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 0.05s)
2025-10-17T09:03:14.948358225Z INFO:__main__:=== Fine Balancer ===
2025-10-17T09:18:45.867736176Z ==> Running 'PYTHONPATH=. python trading/balancer.py'
2025-10-17T09:18:47.060871949Z INFO:database.models:Connesso a MongoDB
2025-10-17T09:18:47.060973715Z INFO:database.models:PositionManager inizializzato
2025-10-17T09:18:50.176156235Z INFO:__main__:=== Avvio Balancer ===
2025-10-17T09:18:50.176172676Z INFO:__main__:=== INIZIO CICLO BALANCER ===
2025-10-17T09:18:50.287051975Z INFO:__main__:Bot saltati: ['stopped: 6', 'external_transfer_pending: 1']
2025-10-17T09:18:50.287072156Z INFO:__main__:Trovati 1 bot da processare su 8 totali
2025-10-17T09:18:50.287117239Z INFO:__main__:Processando bot 68e81c024fb2ad9fa9d63361 con leva target 8.0X
2025-10-17T09:18:50.28886394Z INFO:database.models:Trovate 4 posizioni per bot 68e81c024fb2ad9fa9d63361
2025-10-17T09:18:50.288888181Z INFO:__main__:Nessuna posizione aperta per bot 68e81c024fb2ad9fa9d63361
2025-10-17T09:18:50.288927043Z INFO:__main__:=== FINE CICLO BALANCER === (durata: 0.11s)
2025-10-17T09:18:50.288969015Z INFO:__main__:=== Fine Balancer ===
