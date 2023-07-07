// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

// Smart contract representing a FL task
contract FLTask {
    // Representing the status of the task
    // Pending: invalid status, created when the smart contract is deployed
    // Initialized: the task is ready to be joined by workers
    // Running, Completed, Canceled: self-explanatory
    enum TaskStatus {    
        Pending, 
        Initialized, 
        Running,
        Completed,
        Canceled
    }

    //Struct representing a wokrer of the task, still under development
    //the boolean field is used to verify that a worker cannot join the task twice
    struct Worker {
        bool registered;
        uint8 workerId;
        
    }

    //struct representing the evaluation submitted by a worker at the end of the evaluation phase
    struct SubmittedEval {
        address workerAddress;
        address[] addressScored;
        uint16[] scores;
        //uint16 score; //only for testing
        
    }

    
    uint8 private numRounds; //number of rounds of the fl task
    uint8 private round; //number of the actual round
    uint8 private numWorkers = 0;
    mapping(address => Worker) private workers; //to each worker address is associated his worker object
    mapping(address => uint256) private workerDeposits;

    SubmittedEval[] private roundScores; //to each round are associated the submitted evaluations
    address[] private roundTopK;
    address public immutable requester;
    string private modelURI; //URI of the model pushed by the requester at initialization phase
    uint256 roundMoney;
    TaskStatus public taskStatus;
    

    // Penalty percentage to deduct from the worker's deposit (e.g., 10%)
    uint256 private constant PENALTY_PERCENTAGE = 10;

    constructor() {
        requester = msg.sender;
        taskStatus = TaskStatus.Pending;
    }

    // function modifier allowing the function to be called only by the requester
    modifier onlyRequester() {
        require(msg.sender == requester, "This operation can be performed only by the task requester");
        _;
    }

    // function modifier allowing the function to be called only by the workers
    modifier onlyWorker() {
        require(workers[msg.sender].registered, "This operation can be performed only by the task workers");
        _;
    }

    // function modifier allowing the function to be called only by requester and workers
    modifier restrictAccess() {
        require((workers[msg.sender].registered || msg.sender == requester), "You do not have the rights to perform this operation");
        _;
    }

    // function modifier allowing the function to be called only if the task has been initialized
    modifier taskInitialized(){
        require(uint(taskStatus) == 1, "Task not initialized");
        _;
    }

    // function modifier allowing the function to be called only if the task has started
    modifier taskRunning(){
        require(uint(taskStatus) == 2, "Task not running");
        _;
    }

    // function called to initialize the task, mandatory to put a deposit in the smart contract
    function initializeTask(string memory _modelURI, uint8 _numRounds) public payable onlyRequester{
        require(msg.value != 0, "Cannot initialize contract without deposit");
        modelURI = _modelURI;
        numRounds = _numRounds;
        roundMoney = msg.value / numRounds;
        taskStatus = TaskStatus.Initialized;
    }

    // start the task
    function startTask() public onlyRequester {
        taskStatus = TaskStatus.Running;
        round = 1;
    }

    // advance round
    function nextRound() public onlyRequester taskRunning {
        delete roundScores;
        round++;
    }

    // get the number of actual round
    function getRound() public taskRunning view returns (uint8){
        return round;
    }

    // get the number of workers
    function getNumWorkers() public view returns (uint8){
        return numWorkers;
    }

    // get the amount of money deposited in the smart contract
    function getDeposit() public onlyRequester view returns (uint) {
        return address(this).balance;
    }

    // get the address of the requester
    function getRequester() public view returns (address){
        return requester;
    }

    // get the URI of the model
    function getModelURI() public view restrictAccess returns (string memory){
        return modelURI;
    }

    function joinTask() public payable taskInitialized returns (string memory) {
        require(!workers[msg.sender].registered, "Worker is already registered");
        require(msg.sender != requester, "Requester cannot be a worker!");
        require(msg.value == 5 ether, "Worker must deposit 5 ethers to join the task");

        workers[msg.sender].registered = true;
        workers[msg.sender].workerId = numWorkers + 1;
        workerDeposits[msg.sender] = msg.value;
        numWorkers++;
        return modelURI;
    }



  
    function removeWorker() public {
        require(workers[msg.sender].registered, "Worker is not registered");
        penalizeWorker(msg.sender);
        delete workers[msg.sender];
        numWorkers--;
    }

    // Get the deposit amount of a worker
    function getDepositEther(address workerAddress) public view returns (uint256) {
        require(workerAddress != address(0), "Invalid worker address");
        require(workers[workerAddress].registered, "Worker is not registered");

        return workerDeposits[workerAddress];
    }


    function penalizeWorker(address workerAddress) public payable onlyRequester {
        uint256 penaltyAmount = msg.value;
        require(penaltyAmount <= address(this).balance, "Insufficient contract balance");

        // Deduct the penalty amount from the worker's deposit
        workerDeposits[workerAddress] -= penaltyAmount;

        // Transfer the penalty amount to the requester's account
        payable(requester).transfer(penaltyAmount);
    }


    function refundWorker(address workerAddress) public payable onlyRequester {
        require(workers[workerAddress].registered, "Worker is not registered");

        uint256 refundAmount = workerDeposits[workerAddress];
        require(refundAmount > 0, "No deposit available for refund");

        // Clear the worker's deposit
        workerDeposits[workerAddress] = 0;

        // Transfer the refund amount back to the worker
        payable(workerAddress).transfer(refundAmount);
    }



    function submitScore(address[] memory _workers, uint16[] memory _scores) public onlyWorker taskRunning {
        roundScores.push(SubmittedEval({
            workerAddress: msg.sender,
            addressScored: _workers,
            scores: _scores
        }));
    }

    function getSubmissionsNumber() public onlyRequester view returns (uint8){
        return uint8(roundScores.length);
    }

    function getSubmissions() public onlyRequester taskRunning view returns (SubmittedEval[] memory) {
        SubmittedEval[] memory evals = new SubmittedEval[](getSubmissionsNumber());
        for (uint8 i = 0; i < roundScores.length; i++){
            evals[i] = roundScores[i];
        }
        return evals;
    }

    function submitRoundTopK(address[] memory _topK) public onlyRequester {
        roundTopK = _topK;
    }

    function distributeRewards() public onlyRequester payable {
        uint256 amountToDistribute = roundMoney;
        uint8 usersToReward = uint8(roundTopK.length);
        uint8 usersRewarded;
        for(usersRewarded = 0; usersRewarded < usersToReward-3; usersRewarded++){
            payable(roundTopK[usersRewarded]).transfer(amountToDistribute / 2);
            amountToDistribute = amountToDistribute / 2;
        }
        amountToDistribute = amountToDistribute / 2;
        uint256 finalPortion = amountToDistribute / usersToReward;
        payable(roundTopK[usersRewarded]).transfer(amountToDistribute + finalPortion);
        payable(roundTopK[usersRewarded + 1]).transfer(amountToDistribute - finalPortion);
    }
}
