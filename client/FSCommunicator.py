import torch
import ipfshttpclient
import os
import io


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
        state_dicts = []
        for i in range(num_workers):
            if i != worker_index:
                model_hash = self.client.ls(
                    self.ipfs_path + 'model_round_{}_index_{}.pt'.format(round, i))['Hash']
                model_bytes = self.client.cat(model_hash)
                print(model_hash)
                state_dicts.append(torch.load(io.BytesIO(
                    model_bytes), map_location=self.DEVICE))
        print("Fetching")
        return state_dicts

    def push_model(self, state_dict, worker_index, round):
        # Save the state_dict to a buffer
        buffer = io.BytesIO()
        torch.save(state_dict, 'model')

        # Add the buffer to IPFS and get the new hash
        # model_bytes = buffer.getvalue()
        # print(model_bytes)
        # model_hash = self.client.add_bytes(model_bytes)
        # print("model_hash :", model_hash)

      # Rename the pinned file to include the worker index and round number
        new_name = 'model_round_{}_index_{}.pt'.format(round, worker_index)
        print("ipfs file path :", self.ipfs_path)
        self.client.add('model.pt', self.ipfs_path + new_name)
