import json
import math
# from turtle import shape
import numpy as np
from web3 import Web3, HTTPProvider

class Requester:
    truffle_file = json.load(open('./build/contracts/FLTask.json'))
    score_matrix = None

    def __init__(self, key):
        self.key = key
        # init web3.py instance
        self.w3 = Web3(HTTPProvider("http://localhost:7545"))
        if(self.w3.isConnected()):
            print("Requester initialization: connected to blockchain")

        self.account = self.w3.eth.account.privateKeyToAccount(key)
        self.contract = self.w3.eth.contract(bytecode=self.truffle_file['bytecode'], abi=self.truffle_file['abi'])

    def deploy_contract(self):

        construct_txn = self.contract.constructor().buildTransaction({
            'from': self.account.address,
            'nonce': self.w3.eth.getTransactionCount(self.account.address),
            'gas': 5000000,
            'gasPrice': self.w3.toWei('21', 'gwei')
        })

        signed = self.account.signTransaction(construct_txn)

        tx_hash=self.w3.eth.sendRawTransaction(signed.rawTransaction)
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        self.contract_address = tx_receipt['contractAddress']
        print("Contract Deployed At:", self.contract_address)

    def get_contract_address(self):
        return self.contract_address

    def init_task(self, deposit, model_uri, num_rounds):
        contract_instance = self.w3.eth.contract(abi=self.truffle_file['abi'], address=self.contract_address)

        tx = contract_instance.functions.initializeTask(model_uri, num_rounds).buildTransaction({
            "gasPrice": self.w3.eth.gas_price, 
            "chainId": 1337, 
            "from": self.account.address, 
            "value": deposit,
            'nonce': self.w3.eth.getTransactionCount(self.account.address)
        })
        #Get tx receipt to get contract address
        signed_tx = self.w3.eth.account.signTransaction(tx, self.key)
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)
    
    def init_score_matrix(self):
        self.score_matrix = np.empty((self.num_workers, self.num_workers))

    def start_task(self):
        self.contract_instance = self.w3.eth.contract(abi=self.truffle_file['abi'], address=self.contract_address)

        tx = self.contract_instance.functions.startTask().buildTransaction({
            "gasPrice": self.w3.eth.gas_price, 
            "chainId": 1337, 
            "from": self.account.address, 
            'nonce': self.w3.eth.getTransactionCount(self.account.address)
        })
        #Get tx receipt to get contract address
        signed_tx = self.w3.eth.account.signTransaction(tx, self.key)
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)

        self.num_workers = self.contract_instance.functions.getNumWorkers().call() 
        self.init_score_matrix()
    
    def next_round(self):
        self.contract_instance = self.w3.eth.contract(abi=self.truffle_file['abi'], address=self.contract_address)

        tx = self.contract_instance.functions.nextRound().buildTransaction({
            "gasPrice": self.w3.eth.gas_price, 
            "chainId": 1337, 
            "from": self.account.address, 
            'nonce': self.w3.eth.getTransactionCount(self.account.address)
        })
        #Get tx receipt to get contract address
        signed_tx = self.w3.eth.account.signTransaction(tx, self.key)
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)
        
        self.init_score_matrix()
    
    def push_scores(self, index_score_tuple):
        print("Length of score index_tuple",len(index_score_tuple))
        print("index_score ",index_score_tuple[0])
        print("index_score ",index_score_tuple[1])
        index = index_score_tuple[0]
        scores=index_score_tuple[1]
        self.score_matrix[index] = np.array(scores)
      

    def get_score_matrix(self):
        return self.score_matrix

    # calculate the top K of the round using the contribution scoring procedure from blockflow
    # inputs: score matrix dimension n x n where n = num_workers, number of workers
    # output: round top k with index of best performing workers
    def calc_overall_scores(self, score_matrix, num_workers):
        m = [] # median scores of each worker (m_k)
        m_scaled = [] # scaled median scores of each worker (m_k)
        t = np.full((num_workers, num_workers), -1.0) # evaluation quality scores
        t_scaled = np.full((num_workers, num_workers), -1.0) # transformed evaluation quality scores
        d = [] # least accurate evaluation each client performed
        overall_scores = [] # overall scores

        scores = np.array(score_matrix)
        print("scores",scores)

        #calculate median scores of each worker
        for i in range(num_workers):
            worker_scores = scores[:, i]
            scores_without_self = np.delete(worker_scores, i)
            m.append(np.median(scores_without_self))

        max_median = np.array(m).max() # maximum median score

        # scale median scores to ensure a maximum of 1.0
        for i in range(num_workers):
            m_scaled.append(m[i]/max_median)

        for i in range(num_workers):
            for j in range(num_workers):
                if i != j:
                    t[i, j] = abs(scores[i, j] - m[j]) # compute evaluation quality scores
                    t_scaled[i, j] = max(0, (0.5-t[i, j])/(0.5+t[i, j])) # transform evaluation quality scores
        
        for i in range(num_workers):
            quality_scores = t_scaled[i]
            quality_scores_without_self = np.delete(quality_scores, i)
            d.append(np.array(quality_scores_without_self).min()) # compute least accurate evaluation for each client

        max_d = np.array(d).max() # maximum value of least accurate evaluations used for scaling


        for i in range(num_workers):
            score = min(m_scaled[i], (d[i] / max_d))  # compute overall score as the minimum between m_scaled and d_scaled
            overall_scores.append(score)

        print("Overall Scores: ",overall_scores)
        return overall_scores

    # given the array of addresses and their respective overall score, returns the ordered top k addresses
    # note: k = num_workers in this first implementation, in future work add option to edit top k length 
    def compute_top_k(self, addresses, scores):
        temp_addresses = np.array(addresses)
        temp_scores = np.array(scores)

        top_k = []

        while len(temp_scores) > 0:
            index = np.where(temp_scores == temp_scores.max())[0][0]
            top_k.append(temp_addresses[index])
            temp_scores = np.delete(temp_scores, index)
            temp_addresses = np.delete(temp_addresses, index)
       
        return top_k
    
    def find_bad_workers(self, addresses, scores):
        temp_addresses = np.array(addresses)
        temp_scores = np.array(scores)

        bad_workers = []

        while len(temp_scores) > 0:
            index = np.where(temp_scores < 0.7)[0]  # Find indices of scores below 0.7
            if len(index) == 0:
                break
            min_index = index[0]  # Find the first occurrence of score below 0.7
            bad_workers.append(temp_addresses[min_index])
            temp_scores = np.delete(temp_scores, min_index)
            temp_addresses = np.delete(temp_addresses, min_index)

        return bad_workers



    def submit_top_k(self, top_k):
        self.contract_instance = self.w3.eth.contract(abi=self.truffle_file['abi'], address=self.contract_address)

        tx = self.contract_instance.functions.submitRoundTopK(top_k).buildTransaction({
            "gasPrice": self.w3.eth.gas_price, 
            "chainId": 1337, 
            "from": self.account.address, 
            'nonce': self.w3.eth.getTransactionCount(self.account.address)
        })
        #Get tx receipt to get contract address
        signed_tx = self.w3.eth.account.signTransaction(tx, self.key)
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)

    def distribute_rewards(self):
        self.contract_instance = self.w3.eth.contract(abi=self.truffle_file['abi'], address=self.contract_address)

        tx = self.contract_instance.functions.distributeRewards().buildTransaction({
            "gasPrice": self.w3.eth.gas_price, 
            "chainId": 1337, 
            "from": self.account.address, 
            'nonce': self.w3.eth.getTransactionCount(self.account.address)
        })
        #Get tx receipt to get contract address
        signed_tx = self.w3.eth.account.signTransaction(tx, self.key)
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)
        
    def penalize_worker(self, worker_addresses):
        contract_instance = self.w3.eth.contract(abi=self.truffle_file['abi'], address=self.contract_address)
        penalty_percentage = 70  # Increase the penalty percentage to 20%
        
        for worker_address in worker_addresses:
            # Retrieve the worker's deposit amount in ether from the contract
            deposit_ether = self.contract_instance.functions.getDepositEther(worker_address).call()
            print(f"Worker {worker_address} deposited in ether: {deposit_ether}")
            # Calculate the penalty amount (e.g., 10% of the deposit in ether)
            penalty_ether = (deposit_ether * penalty_percentage) // 100
            print(f"Worker {worker_address} will be penalized for {penalty_ether} ether")

            tx = self.contract_instance.functions.penalizeWorker(worker_address).buildTransaction({
                "gasPrice": self.w3.eth.gas_price,
                "chainId": 1337,
                "from": self.account.address,
                "value": penalty_ether,
                'nonce': self.w3.eth.getTransactionCount(self.account.address)
            })

            signed_tx = self.w3.eth.account.signTransaction(tx, self.key)
            tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
            tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)

            # Check the new deposit amount after penalty
            new_deposit_ether = self.contract_instance.functions.getDepositEther(worker_address).call()
            print(f"New deposit amount for Worker {worker_address} after penalty: {new_deposit_ether}")


  
    def refund_worker(self, worker_addresses):
        contract_instance = self.w3.eth.contract(abi=self.truffle_file['abi'], address=self.contract_address)

        for worker_address in worker_addresses:
            # Retrieve the worker's deposit amount in ether from the contract
            deposit_ether = self.contract_instance.functions.getDepositEther(worker_address).call()
            print(f"Worker {worker_address} refund back to the contract: {deposit_ether}")

            # Refund the worker's deposit amount
            tx = self.contract_instance.functions.refundWorker(worker_address).buildTransaction({
                "gasPrice": self.w3.eth.gas_price,
                "chainId": 1337,
                "from": self.account.address,
                'nonce': self.w3.eth.getTransactionCount(self.account.address)
            })

            signed_tx = self.w3.eth.account.signTransaction(tx, self.key)
            tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
            tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)




    def remove_worker(self, worker_address):
        contract_instance = self.w3.eth.contract(abi=self.truffle_file['abi'], address=self.contract_address)

        tx = contract_instance.functions.removeWorker(worker_address).buildTransaction({
            "gasPrice": self.w3.eth.gas_price,
            "chainId": 1337,
            "from": self.account.address,
            'nonce': self.w3.eth.getTransactionCount(self.account.address)
        })

        signed_tx = self.w3.eth.account.signTransaction(tx, self.key)
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)
