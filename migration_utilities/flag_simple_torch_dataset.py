from numpy.core.fromnumeric import reshape
import torch

from torch.utils.data import Dataset, DataLoader
from tfrecord.torch.dataset import TFRecordDataset
import os
from os import path
import json
import numpy as np

class FlagSimpleDataset(Dataset):
    def __init__(self, path, split, add_targets=None, split_and_preprocess=None):
        self.path = path
        self.split = split
        self.add_targets = add_targets
        self.split_and_preprocess = split_and_preprocess
        try:
            with open(os.path.join(path, 'meta.json'), 'r') as fp:
                self.meta = json.loads(fp.read())
            self.shapes = {}
            self.dtypes = {}
            self.types = {}
            for key, field in self.meta['features'].items():
                self.shapes[key] = field['shape']
                self.dtypes[key] = field['dtype']
                self.types[key] = field['type']
        except FileNotFoundError as e:
            print(e)
            quit()
        tfrecord_path = path + split + ".tfrecord"
        # index is generated by tfrecord2idx
        index_path = path + split + ".idx"
        tf_dataset = TFRecordDataset(tfrecord_path, index_path, None)
        # loader and iter(loader) have size 1000, which is the number of all training trajectories
        loader = torch.utils.data.DataLoader(tf_dataset, batch_size=1)
        # use list to make list from iterable so that the order of elements is ensured
        self.dataset = list(iter(loader))

    def __len__(self):
        # flag simple dataset contains 1000 trajectories, each trajectory contains 400 steps
        return 1000

    def __getitem__(self, idx):
        sample = self.dataset[idx]
        trajectory = {}
        # decode bytes into corresponding dtypes
        for key, value in sample.items():
            raw_data = value.numpy().tobytes()
            mature_data = np.frombuffer(raw_data, dtype=getattr(np, self.dtypes[key]))
            mature_data = torch.from_numpy(mature_data)
            reshaped_data = torch.reshape(mature_data, self.shapes[key])
            if self.types[key] == 'static':
                reshaped_data = torch.tile(reshaped_data, (self.meta['trajectory_length'], 1, 1))
            elif self.types[key] == 'dynamic_varlen':
                # not used in cloth_model
                '''
                length = tf.io.decode_raw(features['length_'+key].values, tf.int32)
                length = tf.reshape(length, [-1])
                data = tf.RaggedTensor.from_row_lengths(data, row_lengths=length)
            '''
            elif self.types[key] != 'dynamic':
                raise ValueError('invalid data format')
            trajectory[key] = reshaped_data
        
        if self.add_targets is not None:
            trajectory = self.add_targets(trajectory)
        if self.split_and_preprocess is not None:
            trajectory = self.split_and_preprocess(trajectory)
        
        
        return trajectory

# code to check whether custom dataset work as expected

# add timer to measure execution time
'''
import time
start_time = time.time()
'''
'''
num_workers = 1
batch_size = 2
flag_simple_dataset = DataLoader(FlagSimpleDataset(path='../../../mgn_dataset/flag_simple/', split='train'), batch_size=batch_size, num_workers=num_workers)
print('flag_simple_dataset size is ' + str(sum(1 for e in flag_simple_dataset)))
for example1_key, example1_value in next(iter(flag_simple_dataset)).items():
    print("example1_key is: ", example1_key)
    print("example1_value size is: ", example1_value.size())
'''
    # print("example1_key size is: ", example1_key.size())
    # print("example1_value is: ", example1_value)
'''
    for example2 in example1:
        print("example2 is: ", example2)
        for key, value in example2.items():
            print(str(key) + ": " + str(value))
            print()
'''
'''
for key, value in next(iter(flag_simple_dataset)).items():
    print(str(key) + ": " + str(value))
    print()
'''
'''

# print("Execution time for flag simple dataset: ", time.time() - start_time)
'''

