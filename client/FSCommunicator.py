import torch
import ipfshttpclient
import os
import io
import shutil


class FSCommunicator:
    def __init__(self, ipfs_path, device):
        self.ipfs_path = ipfs_path
        self.DEVICE = device

        # Connect to the IPFS daemon
        self.client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
        files = self.client.ls(self.ipfs_path)
        # print(files)
        # model_hash = files[0]['Hash']

    def fetch_initial_model(self):
        # Load the model and optimizer state_dicts from IPFS

        model_hash = 'QmZaeFLUPJZopTvKWsuji2Q5RPWaTLBRtpCoBbDM6sDyqM'
        model_bytes = self.client.cat(model_hash)
        # model_file = 'QmZaeFLUPJZopTvKWsuji2Q5RPWaTLBRtpCoBbDM6sDyqM'
        model = torch.jit.load(io.BytesIO(model_bytes),
                               map_location=self.DEVICE)
        print("Done Model!!!!!!")
        # print(m)

        optimizer_hash = 'Qmd96G9irL6hQuSfGFNoYqeVgg8DvAyv6GCt9CqCsEDj1w'
        optimizer_bytes = self.client.cat(optimizer_hash)
        optimizer = torch.load(io.BytesIO(
            optimizer_bytes), map_location=self.DEVICE)
        print("Done Optimizer !!!!!")

        return model, optimizer

    def fetch_evaluation_models(self, worker_index, round, num_workers):
        print("Fetch Function")
        state_dicts = []
        for i in range(num_workers):
            if i != worker_index:
                model_hash = self.client.ls(
                     'model_round_{}_index_{}.pt'.format(round, i))[1]
                model_bytes = self.client.cat(model_hash)
                print(model_hash)
                state_dicts.append(torch.load(io.BytesIO(
                    model_bytes), map_location=self.DEVICE))
        print("Fetching")
        return state_dicts
    
    def push_model(self, state_dict, worker_index, round):
    # Save the state_dict to a file
        print("Pushing Model")
        model_filename = 'model_round_{}_index_{}.pt'.format(round, worker_index)
        torch.save(state_dict, model_filename)

    # Add the file to IPFS and get the new hash
        model_has = self.client.add(model_filename, self.ipfs_path)
        model_hash=model_has['Hash']
        print("Model Hash:", model_hash)

    # Remove the local file
        os.remove(model_filename)



    # def fetch_evaluation_models(self, worker_index, round, num_workers):
    #     print("Fetch Function")
    #     state_dicts = []
    #     for i in range(num_workers):
    #         if i != worker_index:
    #             model_hash = self.client.ls(
    #                 self.ipfs_path + 'model_round_{}_index_{}.pt'.format(round, i))[1]
    #             model_bytes = self.client.cat(model_hash)
    #             print(model_hash)
    #             state_dicts.append(torch.load(io.BytesIO(
    #                 model_bytes), map_location=self.DEVICE))
    #     print("Fetching")
    #     return state_dicts

    # def push_model(self, state_dict, worker_index, round):
    #     # Save the state_dict to a buffer
    #     buffer = io.BytesIO()
    #     torch.save(state_dict, 'model')

    #     # Add the buffer to IPFS and get the new hash
    #     # model_bytes = buffer.getvalue()
    #     # print(model_bytes)
    #     # model_hash = self.client.add_bytes(model_bytes)
    #     # print("model_hash :", model_hash)

    #   # Rename the pinned file to include the worker index and round number
    #     # new_name = 'model_round_{}_index_{}.pt'.format(round, worker_index)
    #     new_name = 'model_round_{}_index_{}.pt'.format(round, worker_index)
    #     os.rename('model', new_name)
    #     with open(new_name, 'rb') as f:
    #         model_bytes = f.read()
    #         model_hash = self.client.add_bytes(model_bytes)[1]
    #         print("Model Hash :",model_hash)
            
        # print("ipfs file path :", self.ipfs_path)
        # self.client.add('model.pt', self.ipfs_path + new_name)
    # def push_model(self, state_dict, worker_index, round):
    # # Save the state_dict to a buffer
    #     buffer = io.BytesIO()
    #     torch.save(state_dict, 'model')

    # # Rename the file to include the worker index and round number
    #     new_name = 'model_round_{}_index_{}.pt'.format(round, worker_index)
    #     shutil.move('model', new_name)

    # # Add the renamed file to IPFS and get the new hash
    #     with open(new_name, 'rb') as f:
    #         model_bytes = f.read()
    #         model_hash = self.client.add_bytes(model_bytes)[1]
    #         print("Model Hash:", model_hash)