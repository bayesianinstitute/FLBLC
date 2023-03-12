// const Migrations = artifacts.require("Migrations");
const FLTask = artifacts.require("FLTask");


module.exports = function (deployer) {
  // deployer.deploy(Migrations);
  deployer.deploy(FLTask);
  
};
