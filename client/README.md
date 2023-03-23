## Setup
a. Create a virtual environment and install the requirements.txt.

b. Install  Ipfs 

## Running
The script is built to run on top of a Ganache testnet. It also requires Truffle to compile the smart contract.

1. Ganache

- Open Ganache and click on settings in the top right corner.
- Under **Server** tab:
  - Set Hostname to 127.0.0.1 -lo
  - Set Port Number to 7545
  - Enable Automine
- Under **Accounts & Keys** tab:
  - Enable Autogenerate HD Mnemonic

2. IPFS



- Fire up your terminal and run `ipfs init`
- Then run

  ```
  ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '[\"*\"]'
  ipfs config --json API.HTTPHeaders.Access-Control-Allow-Credentials '[\"true\"]'
  ipfs config --json API.HTTPHeaders.Access-Control-Allow-Methods '[\"PUT\", \"POST\", \"GET\"]'
  ```
-  Run `ipfs daemon` in terimal.  

- upload fs-sim folder on your local ipfs

### Compile and migrate the smart contract running 
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


Run the following python command
```
python main.py --num_workers 3 --num_rounds 10 
```

If you want to simulate a training session with evil workers, add the parameter `--num-evil` with the desired number of evil workers. 

