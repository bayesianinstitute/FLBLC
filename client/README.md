## Setup
a. Create a virtual environment and install the requirements.txt.

b. Create a Ipfs running on local host

## Running
The script is built to run on top of a Ganache testnet. It also requires Truffle to compile the smart contract.

Compile and migrate the smart contract running 
```
truffle compile
```

```
truffle migrate
```

Create a `.env` file containing the private keys of requester and workers in the following format:
```
REQUESTER_KEY=0x...
WORKER1_KEY=0x...
WORKER2_KEY=0x...
WORKER3_KEY=0x...
...
```
upload fs-sim folder on your local ipfs

Run the following python command
```
python main.py --num_workers 3 --num_rounds 10 
```

If you want to simulate a training session with evil workers, add the parameter `--num-evil` with the desired number of evil workers. 

