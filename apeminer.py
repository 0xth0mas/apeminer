from cffi import FFI
import numpy as np
import time
import json
from web3 import Web3
import random
from dotenv import dotenv_values
from eth_account.signers.local import LocalAccount
from eth_account import Account
config = dotenv_values(".env")

# Initialize FFI for CUDA Driver API
ffi = FFI()

ffi.cdef("""
typedef int CUresult;
typedef int CUdevice;
typedef void *CUcontext;
typedef void *CUmodule;
typedef void *CUfunction;
typedef void *CUstream;
typedef void *CUevent;
typedef unsigned long long CUdeviceptr;

CUresult cuInit(unsigned int flags);
CUresult cuDeviceGet(CUdevice *device, int ordinal);
CUresult cuCtxCreate(CUcontext *pctx, unsigned int flags, CUdevice dev);
CUresult cuModuleLoad(CUmodule *module, const char *fname);
CUresult cuModuleGetFunction(CUfunction *hfunc, CUmodule hmod, const char *name);
CUresult cuMemsetD8(CUdeviceptr dstDevice, unsigned char uc, size_t N);
CUresult cuLaunchKernel(CUfunction f,
                        unsigned int gridDimX,
                        unsigned int gridDimY,
                        unsigned int gridDimZ,
                        unsigned int blockDimX,
                        unsigned int blockDimY,
                        unsigned int blockDimZ,
                        unsigned int sharedMemBytes,
                        CUstream hStream,
                        void **kernelParams,
                        void **extra);
CUresult cuMemAlloc(CUdeviceptr *dptr, size_t bytesize);
CUresult cuMemcpyDtoH(void *dstHost, CUdeviceptr srcDevice, size_t ByteCount);
CUresult cuEventCreate(CUevent *phEvent, unsigned int Flags);
CUresult cuEventRecord(CUevent hEvent, CUstream hStream);
CUresult cuEventSynchronize(CUevent hEvent);
CUresult cuEventDestroy(CUevent hEvent);  // Include this declaration
CUresult cuCtxDestroy(CUcontext ctx);
CUresult cuMemFree(CUdeviceptr dptr);
""")

# Load the CUDA Driver library
cuda = ffi.dlopen("/usr/local/cuda-12.6/compat/libcuda.so")

# Define constants
CUDA_SUCCESS = 0

# Define error handling
def check_cuda_error(result, msg=""):
    if result != CUDA_SUCCESS:
        raise RuntimeError(f"CUDA Error: {msg} (Error code: {result})")

# Initialize CUDA
check_cuda_error(cuda.cuInit(0), "Failed to initialize CUDA")

# Get the CUDA device
device = ffi.new("CUdevice *")
check_cuda_error(cuda.cuDeviceGet(device, 0), "Failed to get CUDA device")

# Create a CUDA context
context = ffi.new("CUcontext *")
check_cuda_error(cuda.cuCtxCreate(context, 0, device[0]), "Failed to create CUDA context")

# Load the CUBIN file
module = ffi.new("CUmodule *")
check_cuda_error(cuda.cuModuleLoad(module, b"kernels/ape.cubin"), "Failed to load CUBIN module")

# Get the kernel function
function = ffi.new("CUfunction *")
check_cuda_error(cuda.cuModuleGetFunction(function, module[0], b"hashMessage"), "Failed to get kernel function")

# Allocate device memory for output
output_size = 152  # Adjust based on your kernel's output size
output = ffi.new(f"uint8_t[{output_size}]")
d_output = ffi.new("CUdeviceptr *")
check_cuda_error(cuda.cuMemAlloc(d_output, output_size), "Failed to allocate device memory")

# Define kernel launch parameters
threads_per_block = (256, 1, 1)  # Adjust as needed
blocks_per_grid = (1024, 1024, 64)  # Adjust as needed

# Prepare kernel arguments
nonce = ffi.new("uint64_t *", 0)
i_0_0_start = ffi.new("uint64_t *", 0)
i_1_0_start = ffi.new("uint64_t *", 0)
i_2_0_start = ffi.new("uint64_t *", 0)
i_1_1_start = ffi.new("uint64_t *", 0)
i_2_1_start = ffi.new("uint64_t *", 0)
i_3_1_start = ffi.new("uint64_t *", 0)
i_4_1_start = ffi.new("uint64_t *", 0)
i_0_2_start = ffi.new("uint64_t *", 0)
target = ffi.new("uint64_t *", 0)
args = [
    ffi.new("CUdeviceptr *", d_output[0]),
    ffi.cast("void *", nonce),
    ffi.cast("void *", i_0_0_start),
    ffi.cast("void *", i_1_0_start),
    ffi.cast("void *", i_2_0_start),
    ffi.cast("void *", i_1_1_start),
    ffi.cast("void *", i_2_1_start),
    ffi.cast("void *", i_3_1_start),
    ffi.cast("void *", i_4_1_start),
    ffi.cast("void *", i_0_2_start),
    ffi.cast("void *", target)
]
arg_array = ffi.new("void *[]", args)

# Create CUDA events for timing
start_event = ffi.new("CUevent *")
end_event = ffi.new("CUevent *")
check_cuda_error(cuda.cuEventCreate(start_event, 0), "Failed to create start event")
check_cuda_error(cuda.cuEventCreate(end_event, 0), "Failed to create end event")

total_start_time = time.time()  # Start timer
last_time = time.time()  # Start timer

senderPK = config["SENDER_PK"]
sender: LocalAccount = Account.from_key(senderPK)
from_address = config["FROM"]
mining_message = config["MESSAGE"]

while True:
    try:
        proof_of_ape_address = "0x1655C0EF91C7b19FD59b42b1A89eBB2bb97448Fd"
        proof_of_ape_abi = json.loads('[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"allowance","type":"uint256"},{"internalType":"uint256","name":"needed","type":"uint256"}],"name":"ERC20InsufficientAllowance","type":"error"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"uint256","name":"balance","type":"uint256"},{"internalType":"uint256","name":"needed","type":"uint256"}],"name":"ERC20InsufficientBalance","type":"error"},{"inputs":[{"internalType":"address","name":"approver","type":"address"}],"name":"ERC20InvalidApprover","type":"error"},{"inputs":[{"internalType":"address","name":"receiver","type":"address"}],"name":"ERC20InvalidReceiver","type":"error"},{"inputs":[{"internalType":"address","name":"sender","type":"address"}],"name":"ERC20InvalidSender","type":"error"},{"inputs":[{"internalType":"address","name":"spender","type":"address"}],"name":"ERC20InvalidSpender","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"miner","type":"address"},{"indexed":false,"internalType":"uint256","name":"difficulty","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"blockHeight","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"hash","type":"uint256"}],"name":"Mined","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[],"name":"HALVING_INTERVAL","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"MAXIMUM_TARGET","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"REWARD_START","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"START_DIFFICULTY","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"TARGET_TIME","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"blockData","outputs":[{"internalType":"address","name":"miner","type":"address"},{"internalType":"string","name":"data","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"blockHeight","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"difficulty","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"difficultyStartTime","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"lastBlockHash","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_nonce","type":"uint256"},{"internalType":"string","name":"_data","type":"string"}],"name":"mine","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_address","type":"address"},{"internalType":"uint256","name":"_nonce","type":"uint256"},{"internalType":"uint256","name":"_hash","type":"uint256"}],"name":"returnHash","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"pure","type":"function"},{"inputs":[],"name":"reward","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"target","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]')
        w3 = Web3(Web3.HTTPProvider('https://apechain.calderachain.xyz/http:8545'))

        proof_of_ape = w3.eth.contract(address=proof_of_ape_address, abi=proof_of_ape_abi)

        found = False
        while True:
            try: 
                last_hash = proof_of_ape.functions.lastBlockHash().call().hex()
                nonce_int = random.randint(1,2**32)
                nonce_end = nonce_int + 0
                nonce[0] = nonce_int

                i_0_0_start[0] = int.from_bytes(bytes.fromhex(from_address[2:18]), byteorder="little")
                i_1_0_start[0] = int.from_bytes(bytes.fromhex(from_address[18:34]), byteorder="little")
                i_2_0_start[0] = int.from_bytes(bytes.fromhex(from_address[34:42] + "00000000"), byteorder="little")
                i_1_1_start[0] = int.from_bytes(bytes.fromhex("00000000" + last_hash[0:8]), byteorder="little")
                i_2_1_start[0] = int.from_bytes(bytes.fromhex(last_hash[8:24]), byteorder="little")
                i_3_1_start[0] = int.from_bytes(bytes.fromhex(last_hash[24:40]), byteorder="little")
                i_4_1_start[0] = int.from_bytes(bytes.fromhex(last_hash[40:56]), byteorder="little")
                i_0_2_start[0] = int.from_bytes(bytes.fromhex(last_hash[56:] + "00000000"), byteorder="little")

                target_value = proof_of_ape.functions.target().call().hex()
                target[0] = int.from_bytes(bytes.fromhex(target_value[0:16]), byteorder="big")

                hash_result = ""
                
                check_cuda_error(
                    cuda.cuMemsetD8(d_output[0], 0, output_size),
                    "Failed to memset device memory"
                )
                while not found: 
                    try: 
                        # Record the start event
                        check_cuda_error(cuda.cuEventRecord(start_event[0], ffi.NULL), "Failed to record start event")

                        check_cuda_error(
                            cuda.cuLaunchKernel(
                                function[0],
                                blocks_per_grid[0], blocks_per_grid[1], blocks_per_grid[2],
                                threads_per_block[0], threads_per_block[1], threads_per_block[2],
                                0,
                                ffi.NULL,
                                arg_array,
                                ffi.NULL
                            ),
                            "Failed to launch kernel"
                        )

                        check_cuda_error(cuda.cuEventRecord(end_event[0], ffi.NULL), "Failed to record end event")
                        check_cuda_error(cuda.cuEventSynchronize(end_event[0]), "Failed to synchronize end event")
                        check_cuda_error(cuda.cuMemcpyDtoH(output, d_output[0], output_size), "Failed to copy result to host")

                        # Process result
                        hash_result = bytes(output).hex()
                        if hash_result != "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000":
                            found = True
                            print(hash_result)
                        else:
                            nonce_int += 1  # Increment nonce if solution not found
                            nonce[0] = nonce_int 

                        if nonce_int == nonce_end: 
                            break
                    except Exception as err:
                        print(err)
                        break
                if found:
                    try:
                        total_end_time = time.time()
                        total_elapsed_time = total_end_time - last_time
                        last_time = total_end_time
                        print(f"Total elapsed time: {total_elapsed_time:.2f} seconds")

                        current_hash = proof_of_ape.functions.lastBlockHash().call().hex()

                        if last_hash != current_hash: 
                            found = False 
                            break

                        last_hash = hash_result[32:96]
                        encoded_data = proof_of_ape.encode_abi("mine", args=[Web3.to_int(hexstr=f'0x000000000000000000000000{hash_result[0:32]}00000000'), mining_message])
                        tx = {
                            'to': proof_of_ape_address,
                            'data': encoded_data,
                            'from': sender.address,
                            'nonce': w3.eth.get_transaction_count(sender.address),
                            'gas': 125000,
                            'value': 0,
                            'maxPriorityFeePerGas': 0,
                            'maxFeePerGas': 50000000000,
                            'chainId': 33139
                        }
                        
                        signed_tx = w3.eth.account.sign_transaction(tx, senderPK)
                        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, 10)
                    except Exception as err:
                        print('failed to mine')
                        print(err)
                        print(hash_result[32:96])
                        last_hash = proof_of_ape.functions.lastBlockHash().call().hex()
                    print(f'Nonce: 0x000000000000000000000000{hash_result[0:32]}00000000')
                    found = False
            except Exception as err:
                print("error at: ")
                print(err)
                break
    except Exception as err:
        print(err)
        time.sleep(6.0)