async function main(){
    const auditLogger = await ethers.getContractFactory("AuditLogger");
    const auditLoggerContract = await auditLogger.deploy();
    await auditLoggerContract.deployed();
    console.log("AuditLogger deployed to:", auditLoggerContract.address);
}

main().catch((error) => {  
    console.error(error);
    process.exitCode = 1;
});