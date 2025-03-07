import gc
import torch 
import tensorflow as tf  
from numba import cuda  
import logging
from typing import List, Tuple

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GarbageCollectorServicec:
    def __init__(self,data:Tuple):
        self.data = data

    def garbage_collecting(self):
        del self.data
        gc.collect()  
        if torch.cuda.is_available():  
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        if tf.config.list_physical_devices('GPU'):  
            tf.keras.backend.clear_session()

        try:
            cuda.select_device(0)  
            cuda.close()
        except Exception as e:
            logging.debug(f"an error has raised: {e}")
            