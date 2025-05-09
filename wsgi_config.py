import multiprocessing

workers = max(multiprocessing.cpu_count() - 2, 1)

bind = "0.0.0.0:8000"

worker_class = "gthread"
threads = 2

timeout = 120

loglevel = "info"
accesslog = "-"
errorlog = "-"
