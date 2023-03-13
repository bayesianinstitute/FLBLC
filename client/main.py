from Application import Application
import argparse
import ipfshttpclient

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Simulate the distributed execution locally')
    parser.add_argument('--num_workers', metavar='-M', type=int, help='number of workers to simulate the distributed environment')
    parser.add_argument('--num_rounds', metavar='-N', type=int, help='number of rounds that should be simulated')
    # not needed in simulation
    parser.add_argument('--index', metavar='-i', type=int, help='Index of current worker used for data splits')
    parser.add_argument('--model_path', metavar='-p', type=str, help='Path to the model file')
    parser.add_argument('--num_evil', metavar='-e', default=0, type=int, help='Number of evil workers you want')
    args = parser.parse_args()

    # create an IPFS client
    client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

    # add the model file to IPFS
    # res = client.get(QmdzVYP8EqpK8CvH7aEAxxms2nCRNc98fTFL2cSiiRbHxn)

    # get the IPFS Folder hash to the added file
    ipfs_hash = "QmdzVYP8EqpK8CvH7aEAxxms2nCRNc98fTFL2cSiiRbHxn"

    print(f"IPFS hash: {ipfs_hash}")

    # create an instance of the Application class with the parsed arguments and the IPFS hash
    sim = Application(args.num_workers, args.num_rounds, ipfs_hash, args.num_evil)
    sim.run()