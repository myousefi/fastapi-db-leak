# Experiment Report

## Log Inventory
- 36 JSON artifacts recorded on 2025-10-03 under `logs/hey/` (one per concurrency/route combination); each file stores `command`, `parameters`, `metrics`, `raw_output`, `status` (always `0`), and `timestamp`.
- Generated rollups: `logs/hey/summary.json`, `logs/hey/summary.csv`, `logs/hey/summary.txt`, plus per-route extracts (`logs/hey/filters-di.txt`, `logs/hey/filters-di-noquery.txt`, `logs/hey/filters-inline.txt`, `logs/hey/filters-inline-mw.txt`).

## Shared Hey Parameters
- Command template: `hey -c <concurrency> -z 30s -H Authorization: Bearer ******** <url>`.
- Defaults: `method` GET, `duration` `30s`, `rps` `null` (unbounded), `auth_header` true, `headers`/`extra_args` null.
- Response payload defaults: `bytes_per_request` 50, `total_seconds` ≈30 s when no timeouts, ≈40 s when timeouts dominate.
- `raw_output` contains summary, histogram, percentile distribution, and phase timings (`DNS+dialup`, `DNS-lookup`, `req write`, `resp wait`, `resp read`).

## Per-Route Metrics

### `/api/v1/experiments/connection-lifetime/filters-di`
```
concurrency-5-api-v1-experiments-connection-lifetime-filters-di-20251003-180709: api_path=/api/v1/experiments/connection-lifetime/filters-di, concurrency=5, total_seconds=30.0126, fastest=0.0168, slowest=0.1535, avg=0.0307, throughput_rps=162.7649, bytes_per_req=50, total_bytes=244250, successes=4885, status_codes=200:4885, errors=0, error_messages=none, p10=0.0248s, p25=0.0268s, p50=0.0291s, p75=0.0319s, p90=0.0377s, p95=0.0474s, p99=0.0535s
concurrency-10-api-v1-experiments-connection-lifetime-filters-di-20251003-180739: api_path=/api/v1/experiments/connection-lifetime/filters-di, concurrency=10, total_seconds=30.0343, fastest=0.0322, slowest=0.1556, avg=0.0639, throughput_rps=156.4212, bytes_per_req=50, total_bytes=234900, successes=4698, status_codes=200:4698, errors=0, error_messages=none, p10=0.0532s, p25=0.0568s, p50=0.0612s, p75=0.0680s, p90=0.0794s, p95=0.0847s, p99=0.0988s
concurrency-25-api-v1-experiments-connection-lifetime-filters-di-20251003-180810: api_path=/api/v1/experiments/connection-lifetime/filters-di, concurrency=25, total_seconds=30.0692, fastest=0.0732, slowest=0.2805, avg=0.1567, throughput_rps=159.3327, bytes_per_req=50, total_bytes=239550, successes=4791, status_codes=200:4791, errors=0, error_messages=none, p10=0.1348s, p25=0.1431s, p50=0.1542s, p75=0.1668s, p90=0.1800s, p95=0.1903s, p99=0.2389s
concurrency-50-api-v1-experiments-connection-lifetime-filters-di-20251003-180840: api_path=/api/v1/experiments/connection-lifetime/filters-di, concurrency=50, total_seconds=30.196, fastest=0.1079, slowest=0.8168, avg=0.318, throughput_rps=156.8091, bytes_per_req=50, total_bytes=236750, successes=4735, status_codes=200:4735, errors=0, error_messages=none, p10=0.2742s, p25=0.2962s, p50=0.3138s, p75=0.3353s, p90=0.3689s, p95=0.4180s, p99=0.5096s
concurrency-75-api-v1-experiments-connection-lifetime-filters-di-20251003-180910: api_path=/api/v1/experiments/connection-lifetime/filters-di, concurrency=75, total_seconds=40.4769, fastest=0.0989, slowest=0.4664, avg=0.2755, throughput_rps=5.0399, bytes_per_req=50, total_bytes=2700, successes=54, status_codes=200:54, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-di": context deadline exceeded (Client.Timeout exceeded while awaiting headers), p10=0.1458s, p25=0.1976s, p50=0.2694s, p75=0.3464s, p90=0.4197s, p95=0.4507s
concurrency-100-api-v1-experiments-connection-lifetime-filters-di-20251003-180951: api_path=/api/v1/experiments/connection-lifetime/filters-di, concurrency=100, total_seconds=40.5271, fastest=0.1098, slowest=0.4798, avg=0.2889, throughput_rps=6.1687, bytes_per_req=50, total_bytes=2500, successes=50, status_codes=200:50, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-di": context deadline exceeded (Client.Timeout exceeded while awaiting headers), p10=0.1600s, p25=0.2462s, p50=0.3060s, p75=0.3560s, p90=0.3964s, p95=0.4795s
concurrency-250-api-v1-experiments-connection-lifetime-filters-di-20251003-181052: api_path=/api/v1/experiments/connection-lifetime/filters-di, concurrency=250, total_seconds=40.6206, fastest=0.1193, slowest=0.5943, avg=0.3581, throughput_rps=13.5645, bytes_per_req=50, total_bytes=2550, successes=51, status_codes=200:51, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-di": context deadline exceeded (Client.Timeout exceeded while awaiting headers), p10=0.1867s, p25=0.2519s, p50=0.3576s, p75=0.4452s, p90=0.5188s, p95=0.5834s
concurrency-500-api-v1-experiments-connection-lifetime-filters-di-20251003-181254: api_path=/api/v1/experiments/connection-lifetime/filters-di, concurrency=500, total_seconds=40.7772, fastest=0.2192, slowest=0.772, avg=0.4342, throughput_rps=25.7987, bytes_per_req=50, total_bytes=2600, successes=52, status_codes=200:52, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-di": context deadline exceeded (Client.Timeout exceeded while awaiting headers), p10=0.2813s, p25=0.3167s, p50=0.4154s, p75=0.5489s, p90=0.6146s, p95=0.7595s
concurrency-1000-api-v1-experiments-connection-lifetime-filters-di-20251003-181825: api_path=/api/v1/experiments/connection-lifetime/filters-di, concurrency=1000, total_seconds=40.1629, fastest=0.0, slowest=0.0, avg=None, throughput_rps=49.7971, bytes_per_req=None, total_bytes=None, successes=0, status_codes=none, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-di": context deadline exceeded (Client.Timeout exceeded while awaiting headers), latency distribution not available
```

### `/api/v1/experiments/connection-lifetime/filters-di-noquery`
```
concurrency-5-api-v1-experiments-connection-lifetime-filters-di-noquery-20251003-185856: api_path=/api/v1/experiments/connection-lifetime/filters-di-noquery, concurrency=5, total_seconds=30.0151, fastest=0.0132, slowest=0.093, avg=0.0294, throughput_rps=169.7813, bytes_per_req=50, total_bytes=254800, successes=5096, status_codes=200:5096, errors=0, error_messages=none, p10=0.0237s, p25=0.0257s, p50=0.0278s, p75=0.0305s, p90=0.0363s, p95=0.0466s, p99=0.0557s
concurrency-10-api-v1-experiments-connection-lifetime-filters-di-noquery-20251003-185927: api_path=/api/v1/experiments/connection-lifetime/filters-di-noquery, concurrency=10, total_seconds=30.0867, fastest=0.0208, slowest=0.1672, avg=0.0615, throughput_rps=162.4636, bytes_per_req=50, total_bytes=244400, successes=4888, status_codes=200:4888, errors=0, error_messages=none, p10=0.0487s, p25=0.0541s, p50=0.0597s, p75=0.0668s, p90=0.0785s, p95=0.0848s, p99=0.0967s
concurrency-25-api-v1-experiments-connection-lifetime-filters-di-noquery-20251003-185957: api_path=/api/v1/experiments/connection-lifetime/filters-di-noquery, concurrency=25, total_seconds=30.0842, fastest=0.0765, slowest=0.282, avg=0.1552, throughput_rps=160.8816, bytes_per_req=50, total_bytes=242000, successes=4840, status_codes=200:4840, errors=0, error_messages=none, p10=0.1249s, p25=0.1372s, p50=0.1526s, p75=0.1698s, p90=0.1886s, p95=0.2019s, p99=0.2336s
concurrency-50-api-v1-experiments-connection-lifetime-filters-di-noquery-20251003-190027: api_path=/api/v1/experiments/connection-lifetime/filters-di-noquery, concurrency=50, total_seconds=30.1648, fastest=0.0701, slowest=0.7296, avg=0.3014, throughput_rps=165.4907, bytes_per_req=50, total_bytes=249600, successes=4992, status_codes=200:4992, errors=0, error_messages=none, p10=0.2630s, p25=0.2795s, p50=0.2981s, p75=0.3181s, p90=0.3416s, p95=0.3612s, p99=0.4202s
concurrency-75-api-v1-experiments-connection-lifetime-filters-di-noquery-20251003-190058: api_path=/api/v1/experiments/connection-lifetime/filters-di-noquery, concurrency=75, total_seconds=30.254, fastest=0.0787, slowest=1.3246, avg=0.4575, throughput_rps=163.3174, bytes_per_req=50, total_bytes=247050, successes=4941, status_codes=200:4941, errors=0, error_messages=none, p10=0.4049s, p25=0.4264s, p50=0.4503s, p75=0.4786s, p90=0.5132s, p95=0.5461s, p99=0.6599s
concurrency-100-api-v1-experiments-connection-lifetime-filters-di-noquery-20251003-190128: api_path=/api/v1/experiments/connection-lifetime/filters-di-noquery, concurrency=100, total_seconds=30.356, fastest=0.1244, slowest=1.8306, avg=0.6098, throughput_rps=163.0318, bytes_per_req=50, total_bytes=247450, successes=4949, status_codes=200:4949, errors=0, error_messages=none, p10=0.5513s, p25=0.5765s, p50=0.6042s, p75=0.6386s, p90=0.6798s, p95=0.7032s, p99=0.7769s
concurrency-250-api-v1-experiments-connection-lifetime-filters-di-noquery-20251003-190159: api_path=/api/v1/experiments/connection-lifetime/filters-di-noquery, concurrency=250, total_seconds=30.8759, fastest=0.0828, slowest=5.4134, avg=1.5182, throughput_rps=162.748, bytes_per_req=50, total_bytes=251250, successes=5025, status_codes=200:5025, errors=0, error_messages=none, p10=1.2494s, p25=1.4687s, p50=1.5112s, p75=1.5714s, p90=1.6539s, p95=1.7181s, p99=4.2940s
concurrency-500-api-v1-experiments-connection-lifetime-filters-di-noquery-20251003-190230: api_path=/api/v1/experiments/connection-lifetime/filters-di-noquery, concurrency=500, total_seconds=31.8096, fastest=0.3131, slowest=10.9307, avg=3.0674, throughput_rps=159.1344, bytes_per_req=50, total_bytes=253100, successes=5062, status_codes=200:5062, errors=0, error_messages=none, p10=1.6360s, p25=2.9645s, p50=3.0670s, p75=3.1855s, p90=3.3243s, p95=4.7387s, p99=10.0504s
concurrency-1000-api-v1-experiments-connection-lifetime-filters-di-noquery-20251003-190302: api_path=/api/v1/experiments/connection-lifetime/filters-di-noquery, concurrency=1000, total_seconds=34.5737, fastest=0.0407, slowest=19.9963, avg=5.5786, throughput_rps=155.4649, bytes_per_req=50, total_bytes=258450, successes=5169, status_codes=200:5169, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-di-noquery": context deadline exceeded (Client.Timeout exceeded while awaiting headers), p10=1.4768s, p25=3.4463s, p50=5.6941s, p75=6.4764s, p90=8.7440s, p95=13.4150s, p99=18.7260s
```

### `/api/v1/experiments/connection-lifetime/filters-inline`
```
concurrency-5-api-v1-experiments-connection-lifetime-filters-inline-20251003-183026: api_path=/api/v1/experiments/connection-lifetime/filters-inline, concurrency=5, total_seconds=30.0141, fastest=0.0135, slowest=0.075, avg=0.0284, throughput_rps=176.2506, bytes_per_req=50, total_bytes=264500, successes=5290, status_codes=200:5290, errors=0, error_messages=none, p10=0.0222s, p25=0.0245s, p50=0.0269s, p75=0.0297s, p90=0.0352s, p95=0.0461s, p99=0.0529s
concurrency-10-api-v1-experiments-connection-lifetime-filters-inline-20251003-185447: api_path=/api/v1/experiments/connection-lifetime/filters-inline, concurrency=10, total_seconds=30.0187, fastest=0.0242, slowest=0.1761, avg=0.0594, throughput_rps=168.3618, bytes_per_req=50, total_bytes=252700, successes=5054, status_codes=200:5054, errors=0, error_messages=none, p10=0.0480s, p25=0.0523s, p50=0.0571s, p75=0.0639s, p90=0.0750s, p95=0.0806s, p99=0.0902s
concurrency-25-api-v1-experiments-connection-lifetime-filters-inline-20251003-185518: api_path=/api/v1/experiments/connection-lifetime/filters-inline, concurrency=25, total_seconds=30.0872, fastest=0.0851, slowest=0.2906, avg=0.1482, throughput_rps=168.5766, bytes_per_req=50, total_bytes=253600, successes=5072, status_codes=200:5072, errors=0, error_messages=none, p10=0.1207s, p25=0.1313s, p50=0.1449s, p75=0.1611s, p90=0.1787s, p95=0.1923s, p99=0.2300s
concurrency-50-api-v1-experiments-connection-lifetime-filters-inline-20251003-185548: api_path=/api/v1/experiments/connection-lifetime/filters-inline, concurrency=50, total_seconds=30.1888, fastest=0.1, slowest=0.7554, avg=0.2911, throughput_rps=171.4541, bytes_per_req=50, total_bytes=258800, successes=5176, status_codes=200:5176, errors=0, error_messages=none, p10=0.2516s, p25=0.2684s, p50=0.2877s, p75=0.3083s, p90=0.3319s, p95=0.3500s, p99=0.4109s
concurrency-75-api-v1-experiments-connection-lifetime-filters-inline-20251003-185619: api_path=/api/v1/experiments/connection-lifetime/filters-inline, concurrency=75, total_seconds=30.2518, fastest=0.072, slowest=1.5046, avg=0.4377, throughput_rps=170.8329, bytes_per_req=50, total_bytes=258400, successes=5168, status_codes=200:5168, errors=0, error_messages=none, p10=0.3925s, p25=0.4114s, p50=0.4333s, p75=0.4575s, p90=0.4864s, p95=0.5128s, p99=0.5668s
concurrency-100-api-v1-experiments-connection-lifetime-filters-inline-20251003-185649: api_path=/api/v1/experiments/connection-lifetime/filters-inline, concurrency=100, total_seconds=30.2995, fastest=0.0941, slowest=2.1886, avg=0.5786, throughput_rps=172.1808, bytes_per_req=50, total_bytes=260850, successes=5217, status_codes=200:5217, errors=0, error_messages=none, p10=0.5281s, p25=0.5503s, p50=0.5729s, p75=0.5990s, p90=0.6323s, p95=0.6643s, p99=0.7734s
concurrency-250-api-v1-experiments-connection-lifetime-filters-inline-20251003-185720: api_path=/api/v1/experiments/connection-lifetime/filters-inline, concurrency=250, total_seconds=30.7521, fastest=0.1238, slowest=7.2886, avg=1.4954, throughput_rps=165.5822, bytes_per_req=50, total_bytes=254600, successes=5092, status_codes=200:5092, errors=0, error_messages=none, p10=0.9971s, p25=1.4278s, p50=1.4803s, p75=1.5471s, p90=1.6361s, p95=1.6765s, p99=5.6103s
concurrency-500-api-v1-experiments-connection-lifetime-filters-inline-20251003-185751: api_path=/api/v1/experiments/connection-lifetime/filters-inline, concurrency=500, total_seconds=31.7639, fastest=0.0637, slowest=11.7769, avg=2.9313, throughput_rps=167.1392, bytes_per_req=50, total_bytes=265450, successes=5309, status_codes=200:5309, errors=0, error_messages=none, p10=1.7773s, p25=2.7469s, p50=2.9228s, p75=2.9903s, p90=3.0641s, p95=3.4381s, p99=10.3282s
concurrency-1000-api-v1-experiments-connection-lifetime-filters-inline-20251003-185823: api_path=/api/v1/experiments/connection-lifetime/filters-inline, concurrency=1000, total_seconds=33.164, fastest=1.2445, slowest=19.926, avg=5.5107, throughput_rps=165.2092, bytes_per_req=50, total_bytes=267400, successes=5348, status_codes=200:5348, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-inline": context deadline exceeded (Client.Timeout exceeded while awaiting headers), p10=2.9407s, p25=3.8746s, p50=5.5541s, p75=6.1013s, p90=6.4014s, p95=11.0207s, p99=18.2018s
```

### `/api/v1/experiments/connection-lifetime/filters-inline-mw`
```
concurrency-5-api-v1-experiments-connection-lifetime-filters-inline-mw-20251003-190337: api_path=/api/v1/experiments/connection-lifetime/filters-inline-mw, concurrency=5, total_seconds=30.0125, fastest=0.0148, slowest=0.1026, avg=0.0423, throughput_rps=118.0843, bytes_per_req=50, total_bytes=177200, successes=3544, status_codes=200:3544, errors=0, error_messages=none, p10=0.0349s, p25=0.0373s, p50=0.0402s, p75=0.0440s, p90=0.0551s, p95=0.0615s, p99=0.0713s
concurrency-10-api-v1-experiments-connection-lifetime-filters-inline-mw-20251003-190408: api_path=/api/v1/experiments/connection-lifetime/filters-inline-mw, concurrency=10, total_seconds=30.0578, fastest=0.0571, slowest=0.1924, avg=0.0889, throughput_rps=112.3837, bytes_per_req=50, total_bytes=168900, successes=3378, status_codes=200:3378, errors=0, error_messages=none, p10=0.0746s, p25=0.0793s, p50=0.0855s, p75=0.0949s, p90=0.1072s, p95=0.1156s, p99=0.1536s
concurrency-25-api-v1-experiments-connection-lifetime-filters-inline-mw-20251003-190438: api_path=/api/v1/experiments/connection-lifetime/filters-inline-mw, concurrency=25, total_seconds=30.167, fastest=0.0548, slowest=0.4806, avg=0.2255, throughput_rps=110.6508, bytes_per_req=50, total_bytes=166900, successes=3338, status_codes=200:3338, errors=0, error_messages=none, p10=0.1568s, p25=0.2004s, p50=0.2225s, p75=0.2485s, p90=0.2933s, p95=0.3178s, p99=0.3867s
concurrency-50-api-v1-experiments-connection-lifetime-filters-inline-mw-20251003-190508: api_path=/api/v1/experiments/connection-lifetime/filters-inline-mw, concurrency=50, total_seconds=40.1973, fastest=0.1417, slowest=0.1926, avg=0.1652, throughput_rps=2.7614, bytes_per_req=50, total_bytes=550, successes=11, status_codes=200:11, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-inline-mw": context deadline exceeded (Client.Timeout exceeded while awaiting headers), p10=0.1524s, p25=0.1526s, p50=0.1714s, p75=0.1889s, p90=0.1926s
concurrency-75-api-v1-experiments-connection-lifetime-filters-inline-mw-20251003-190549: api_path=/api/v1/experiments/connection-lifetime/filters-inline-mw, concurrency=75, total_seconds=40.329, fastest=0.2152, slowest=0.3224, avg=0.2465, throughput_rps=3.9426, bytes_per_req=50, total_bytes=450, successes=9, status_codes=200:9, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-inline-mw": context deadline exceeded (Client.Timeout exceeded while awaiting headers), p10=0.2278s, p25=0.2279s, p50=0.2392s, p75=0.2732s
concurrency-100-api-v1-experiments-connection-lifetime-filters-inline-mw-20251003-190650: api_path=/api/v1/experiments/connection-lifetime/filters-inline-mw, concurrency=100, total_seconds=40.2087, fastest=0.1426, slowest=0.2037, avg=0.1755, throughput_rps=5.1979, bytes_per_req=50, total_bytes=450, successes=9, status_codes=200:9, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-inline-mw": context deadline exceeded (Client.Timeout exceeded while awaiting headers), p10=0.1561s, p25=0.1696s, p50=0.1829s, p75=0.2002s
concurrency-250-api-v1-experiments-connection-lifetime-filters-inline-mw-20251003-190850: api_path=/api/v1/experiments/connection-lifetime/filters-inline-mw, concurrency=250, total_seconds=40.2406, fastest=0.1588, slowest=0.2345, avg=0.1932, throughput_rps=12.6489, bytes_per_req=50, total_bytes=450, successes=9, status_codes=200:9, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-inline-mw": context deadline exceeded (Client.Timeout exceeded while awaiting headers), p10=0.1591s, p25=0.1798s, p50=0.2085s, p75=0.2224s
concurrency-500-api-v1-experiments-connection-lifetime-filters-inline-mw-20251003-191121: api_path=/api/v1/experiments/connection-lifetime/filters-inline-mw, concurrency=500, total_seconds=40.1387, fastest=0.0, slowest=0.0, avg=None, throughput_rps=24.9136, bytes_per_req=None, total_bytes=None, successes=0, status_codes=none, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-inline-mw": context deadline exceeded (Client.Timeout exceeded while awaiting headers), latency distribution not available
concurrency-1000-api-v1-experiments-connection-lifetime-filters-inline-mw-20251003-191752: api_path=/api/v1/experiments/connection-lifetime/filters-inline-mw, concurrency=1000, total_seconds=40.2237, fastest=0.2027, slowest=0.2048, avg=0.2039, throughput_rps=49.7966, bytes_per_req=50, total_bytes=150, successes=3, status_codes=200:3, errors=1, error_messages=Get "http://localhost:8000/api/v1/experiments/connection-lifetime/filters-inline-mw": context deadline exceeded (Client.Timeout exceeded while awaiting headers), p10=0.2041s, p25=0.2048s
```

## Raw Output Example
```
  Total:	30.0343 secs
  Slowest:	0.1556 secs
  Fastest:	0.0322 secs
  Average:	0.0639 secs
  Requests/sec:	156.4212
  
  Total data:	234900 bytes
  Size/request:	50 bytes

Response time histogram:
  0.032 [1]	|
  0.045 [20]	|
  0.057 [1161]	|■■■■■■■■■■■■■■■■■■■
  0.069 [2440]	|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.082 [712]	|■■■■■■■■■■■■
  0.094 [298]	|■■■■■
  0.106 [36]	|■
  0.119 [13]	|
  0.131 [6]	|
  0.143 [7]	|
  0.156 [4]	|

Latency distribution:
  10% in 0.0532 secs
  25% in 0.0568 secs
```

## API Implementation Overview
```python
# backend/app/api/v1/connection_lifetime.py:25
@experiment_router.get("/filters-di", response_model=IncentiveSearchQueryFilters)
def get_filters_di(
    ctx: deps.UserContext = Depends(deps.get_current_active_user_context),
) -> IncentiveSearchQueryFilters:
    return _run_filters(ctx.db)

# backend/app/api/v1/connection_lifetime.py:32
@experiment_router.get("/filters-inline", response_model=IncentiveSearchQueryFilters)
def get_filters_inline(request: Request) -> IncentiveSearchQueryFilters:
    token = deps.extract_bearer_token(request)
    with Session(engine) as session:
        ctx = deps.build_user_context(session, token)
        return _run_filters(ctx.db)
```

## Dependency and Context Handling
```python
# backend/app/api/deps.py:103
def build_user_context(session: Session, token: str) -> UserContext:
    user = _load_user(session, token)
    return UserContext(
        user_id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        db=session,
    )

# backend/app/api/deps.py:138
def extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, _, credentials = authorization.partition(" ")
    if scheme.lower() != "bearer" or not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials
```

## Service Layer Queries
```python
# backend/app/services/incentive_discovery.py:22
def get_filters(self) -> IncentiveSearchQueryFilters:
    total_users = self._db.exec(
        select(func.count()).select_from(User)
    ).one()
    active_users = self._db.exec(
        select(func.count()).select_from(User).where(User.is_active)
    ).one()
    total_items = self._db.exec(
        select(func.count()).select_from(Item)
    ).one()

    return IncentiveSearchQueryFilters(
        total_users=total_users,
        active_users=active_users,
        total_items=total_items,
    )
```

## Database Engine and Pool Instrumentation
```python
# backend/app/core/db.py:8
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERflow,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,
)

set_pool_metrics(instrument_engine(engine))
```

## Settings Defaults
```python
# backend/app/core/config.py:33
API_V1_STR: str = "/api/v1"
SECRET_KEY: str = secrets.token_urlsafe(32)
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
FRONTEND_HOST: str = "http://localhost:5173"
ENVIRONMENT: Literal["local", "staging", "production"] = "local"
OTEL_TRACING_ENABLED: bool = False
OTEL_LOGS_ENABLED: bool = False
OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
OTEL_SQLCOMMENTER_ENABLED: bool = True
DB_POOL_SIZE: int = 10
DB_MAX_OVERFLOW: int = 10
DB_POOL_TIMEOUT: float = 30.0
```

## Observability Hooks
```python
# backend/app/main.py:36
app.include_router(api_router, prefix=settings.API_V1_STR)

setup_logging()
setup_tracing(app, engine=engine)
```

```python
# backend/app/observability/tracing.py:27
if not settings.OTEL_TRACING_ENABLED:
    _logger.debug("Skipping OpenTelemetry setup because OTEL_TRACING_ENABLED is false")
    return
```

```python
# backend/app/observability/logging.py:20
if not settings.OTEL_LOGS_ENABLED:
    _logger.debug("Skipping OpenTelemetry log setup because OTEL_LOGS_ENABLED is false")
    return
```

## SigNoz Runtime Context
- Active containers (`docker ps`):
  - `signoz/signoz:v0.96.1` on TCP 8080 (UI/API gateway).
  - `signoz/signoz-otel-collector:v0.129.6` on ports 4317-4318.
  - `clickhouse/clickhouse-server:25.5.6` backend, `signoz/zookeeper:3.7.1` dependencies.
- `curl` to `http://localhost:8080/api/...` returns the SigNoz single-page app HTML shell; unauthenticated REST responses not available without proper session or API key.

