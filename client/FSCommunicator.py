import torch
import ipfshttpclient
import os
import io
import shutil
import numpy as np
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend


# create an empty list to store all the model hashes
model_hashes =[]


class FSCommunicator:
    def __init__(self, ipfs_path, device):
        self.ipfs_path = ipfs_path
        self.DEVICE = device
        self.model_hashes = []
        
        # Generate RSA key pair
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

        # Serialize public key to PEM format
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Generate AES key
        self.aes_key = Fernet.generate_key()
        print("ase", self.aes_key)

        # Create Fernet object with AES key
        self.fernet = Fernet(self.aes_key)

        # Connect to the IPFS daemon
        self.client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
        files = self.client.ls(self.ipfs_path)
        
        

    def fetch_initial_model(self):
        # Load the model and optimizer state_dicts from IPFS

        model_hash = 'QmZaeFLUPJZopTvKWsuji2Q5RPWaTLBRtpCoBbDM6sDyqM'
        model_bytes = self.client.cat(model_hash)
        model = torch.jit.load(io.BytesIO(model_bytes),
                               map_location=self.DEVICE)
        print("Done Model!!!!!!")

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
            print("worker",i)
            print("hash length",len(model_hashes))
            # Load the encrypted AES key from the disk
            k="aes_key_encrypted_round_{}_index_{}.pem".format(round, worker_index)
            print(k)
            with open(k, "rb") as f:
                encrypted_aes_key = f.read()
            
            print("Decryption key", self.aes_key)
            

        # Decrypt the AES key with the private RSA key
            decrypted_aes_key = self.private_key.decrypt(
                encrypted_aes_key,
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None)
            )
            print("Encryption Key", decrypted_aes_key)
            # Create a Fernet object using the decrypted AES key
            fernet = Fernet(decrypted_aes_key)

            # Load the encrypted model from the disk
         
            model_filename1 = 'model_encrypted_round_{}_index_{}.pt'.format(round, worker_index)

            print(model_filename1)
            with open(model_filename1, "rb") as f:
                encrypted_model = f.read()
                
            model_filename2 = 'Decriprited_model_round_{}_index_{}.pt'.format(round, worker_index)
            print(model_filename2)
            # Decrypt the encrypted model using the Fernet object
            decrypted_model = fernet.decrypt(encrypted_model)

            # Save the decrypted model to the disk
            with open(model_filename2, "wb") as f:
                f.write(decrypted_model)
            if i < (len(model_hashes)-1):
                
                model = torch.load(model_filename2)
                state_dicts.append(model)
            
            
            
    
        
      
        return state_dicts  
    
    def push_model(self, state_dict, worker_index, round, num_workers):
        
        # Clear the model_hashes list if it has reached the number of workers

        if (len(model_hashes)) == num_workers:
                model_hashes.clear()
                print("model_hashes list cleared",model_hashes)
                
        # Save the state_dict to a file
        print("Pushing Model")
        model_filename = 'model_round_{}_index_{}.pt'.format(round, worker_index)
        torch.save(state_dict, model_filename)
        print("MODEL SAVE TO LOCAL")
       

        # Load file into memory
        with open(model_filename , "rb") as f:
            file_contents = f.read()

        # Encrypt file with AES key
        encrypted_file = self.fernet.encrypt(file_contents)

        # Encrypt AES key with RSA public key
        encrypted_aes_key = self.public_key.encrypt(
            self.aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        
        model_filename1 = 'model_encrypted_round_{}_index_{}.pt'.format(round, worker_index)
        k="aes_key_encrypted_round_{}_index_{}.pem".format(round, worker_index)
        # Save encrypted file and encrypted AES key to disk
        with open(model_filename1, "wb") as f:
            f.write(encrypted_file)

        with open(k, "wb") as f:
            f.write(encrypted_aes_key)

        # Add the file to IPFS and get the new hash
        model_has = self.client.add(model_filename1)
        model_hash = model_has['Hash']
       

        print("Length of model hashes:", len(model_hashes))
        
        
        model_hashes.append(model_hash)  # add the new model hash to the list
        print("List of hash:", model_hashes)
        print("Model Hash:", model_hash)
        print("Pushing Complete")

        # Remove the local file
        os.remove(model_filename)

        

        
