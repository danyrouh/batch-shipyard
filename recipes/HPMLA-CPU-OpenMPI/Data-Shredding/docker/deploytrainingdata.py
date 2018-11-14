### this code is deployed as is.  It's designed to support shredding criteo-libsvm-uniform dataset.
### the shredding is designed to use file counts and not the files sizes.  Having said that, the code
### is designed to make it easier to change it to be based on the file size.
 
from __future__ import print_function

import sys
import os
import time
from mpi4py import MPI
import json
import tempfile
from azure.storage.blob.models import BlobBlock
from azure.storage.blob import BlockBlobService
from os import listdir
from os.path import isfile, join
import math
import shutil

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# make sure config data is encode it correctly
def encode(value):
    if isinstance(value, type('str')):
        return value
    return value.encode('utf-8')


# load the configuration data
class Configuration:

    def __init__(self, file_name):
        if not os.path.exists(file_name):
            raise ValueError('Cannot find configuration file "{0}"'.
                             format(file_name))

        with open(file_name, 'r') as f:
            conf = json.load(f)

        try:
            self.resource_group = encode(conf['resource_group'])
            self.data_prefix = encode(conf['data_prefix'])
            self.data_container_name = encode(conf['data_container_name'])
            self.data_local_dir = encode(conf['data_local_dir'])
            self.storage_account_name = encode(conf['storage_account']['name'])
            self.storage_account_key = encode(conf['storage_account']['key'])
            self.input_data_container_name = encode(conf['input_data_container_name'])
            self.input_storage_account_name = encode(conf['input_storage_account']['name'])
            self.input_storage_account_key = encode(conf['input_storage_account']['key'])        
        except KeyError as err:
            raise AttributeError('Please provide a value for "{0}" configuration key'.format(err.args[0]))
        
# load eh configuration data
cfg = Configuration('/parasail/configuration.json')

# azure block service object
blob_service = BlockBlobService(cfg.storage_account_name, cfg.storage_account_key)

# create the container that will host the training data blobs
blob_service.create_container(cfg.data_container_name, fail_on_exist=False)


# azure block service object
import_blob_service = BlockBlobService(cfg.input_storage_account_name, cfg.input_storage_account_key)


# the function that load the data from the training blob, partition the data
# and upload it to the container blobs
def upload_data_to_blob(container_name, input_container_name, data_local_Per_Node_dir):
    
    print(data_local_Per_Node_dir)
    #make local training dir exists
    if not os.path.exists(data_local_Per_Node_dir):
        os.makedirs(data_local_Per_Node_dir)

    # Read the list the blobs in a training container to get the data size
    blobs = []
    marker = None
    blobs_size = 1
    while True:
        batch = import_blob_service.list_blobs(input_container_name, marker=marker)
        blobs.extend(batch)
        if not batch.next_marker:
            break
        marker = batch.next_marker
    for blob in blobs:
        blobs_size  += blob.properties.content_length
        #print(blob.name)
        
    files_count = len(blobs)

    # get the file count per vm
    files_count_per_node = int(round(files_count / (size)))
    filename = "data.lst"
                 
    files_end_index = int(((rank + 1) * files_count_per_node))
    files_start_index = int(files_end_index - files_count_per_node)
    
    print(" files_start_index: " ,files_start_index)
    print("files_end_index: " ,files_end_index)
    print("files_count_per_node: " ,files_count_per_node)

    local_dir = data_local_Per_Node_dir
    is_local_dir = False
    
    merged_blob_name = cfg.data_prefix + "%05d" % (rank,)
    dir_blob_per_node = os.path.join(data_local_Per_Node_dir, merged_blob_name)
    print(dir_blob_per_node)
    if not os.path.exists(dir_blob_per_node):
        os.makedirs(dir_blob_per_node)
        
    merged_file_path_name =os.path.join(dir_blob_per_node,filename)
    print(merged_file_path_name)

    
    with open(merged_file_path_name, 'w') as wr:
        while((files_start_index < files_end_index) and (files_start_index < files_count)):   
            blob = blobs[files_start_index]
            if(len(blob.name.split("/",1)) > 1 and is_local_dir == False):
                is_local_dir = True
                blob_folder_name = blob.name.split("/",1)[0] 
                blob_name = blob.name.split("/",1)[1] 
                local_dir = os.path.join(data_local_Per_Node_dir,  blob_folder_name)
                if not os.path.exists(local_dir):
                    os.makedirs(local_dir)
        
            local_dir_blob = os.path.join(data_local_Per_Node_dir, blob.name)
            import_blob_service.get_blob_to_path(input_container_name, blob.name, local_dir_blob)
            print(str(rank) +" : " + local_dir_blob)
            files_start_index +=1
            
            with open(local_dir_blob, 'r') as in_file:
                for line in in_file:
                    line = line.replace('\r\n', '\n')
                    wr.write(line)

            os.remove(local_dir_blob)

    blob_service.create_blob_from_path(container_name,  os.path.basename(dir_blob_per_node) + '/' + filename, merged_file_path_name)
    print("done uploading merged file")
            
    for subdir, dirs, files in os.walk(data_local_Per_Node_dir):
                for d in dirs:
                    shutil.rmtree(os.path.join(subdir, d), ignore_errors=True) 
                for f in files:
                    os.remove(os.path.join(subdir, f))
    print('Done')

upload_data_to_blob(cfg.data_container_name,cfg.input_data_container_name, os.path.normpath(cfg.data_local_dir))