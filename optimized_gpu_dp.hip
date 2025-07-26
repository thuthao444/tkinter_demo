#include <hip/hip_runtime.h>
#include <cstdlib>
#include <algorithm>

// Tối ưu 1: Sử dụng shared memory và vectorized operations
__global__ void init_kernel_optimized(int *dp, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    // Vectorized initialization - process 4 elements at once
    if (idx * 4 < size) {
        int4 init_val = make_int4(0, 0, 0, 0);
        if (idx == 0) init_val.x = 1; // dp[0] = 1
        
        int remaining = min(4, size - idx * 4);
        if (remaining >= 1) dp[idx * 4] = init_val.x;
        if (remaining >= 2) dp[idx * 4 + 1] = init_val.y;
        if (remaining >= 3) dp[idx * 4 + 2] = init_val.z;
        if (remaining >= 4) dp[idx * 4 + 3] = init_val.w;
    }
}

// Tối ưu 2: Sử dụng shared memory cho cache tăng tốc
__global__ void update_kernel_optimized(int *dp_old, int *dp_new, int item, int K) {
    extern __shared__ int shared_mem[];
    
    int tid = threadIdx.x;
    int gid = blockIdx.x * blockDim.x + threadIdx.x;
    int block_size = blockDim.x;
    
    // Load data to shared memory with coalesced access
    if (gid <= K) {
        shared_mem[tid] = dp_old[gid];
    }
    
    // Load additional data needed for dependencies
    if (tid < item && gid + block_size <= K) {
        shared_mem[tid + block_size] = dp_old[gid + block_size];
    }
    
    __syncthreads();
    
    if (gid <= K) {
        int result;
        if (gid < item) {
            result = shared_mem[tid];
        } else {
            // Check if we can use shared memory
            int dep_idx = gid - item;
            int local_dep_idx = dep_idx - blockIdx.x * blockDim.x;
            
            if (local_dep_idx >= 0 && local_dep_idx < block_size) {
                // Dependency is in shared memory
                result = (shared_mem[tid] + shared_mem[local_dep_idx]) % 1000;
            } else {
                // Need to access global memory
                result = (shared_mem[tid] + dp_old[dep_idx]) % 1000;
            }
        }
        dp_new[gid] = result;
    }
}

// Tối ưu 3: Kernel fusion - xử lý nhiều items cùng lúc
__global__ void fused_update_kernel(int *dp_old, int *dp_new, int *items, int start_item, int num_items, int K) {
    extern __shared__ int shared_data[];
    
    int tid = threadIdx.x;
    int gid = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (gid > K) return;
    
    // Load initial DP values
    shared_data[tid] = dp_old[gid];
    __syncthreads();
    
    int current_val = shared_data[tid];
    
    // Process multiple items in sequence
    for (int i = 0; i < num_items; i++) {
        int item = items[start_item + i];
        
        int new_val;
        if (gid < item) {
            new_val = current_val;
        } else {
            int dep_idx = gid - item;
            int dep_val;
            
            // Try to get dependency from shared memory
            int local_dep = dep_idx - blockIdx.x * blockDim.x;
            if (local_dep >= 0 && local_dep < blockDim.x) {
                dep_val = shared_data[local_dep];
            } else {
                dep_val = dp_old[dep_idx];
            }
            
            new_val = (current_val + dep_val) % 1000;
        }
        
        current_val = new_val;
        shared_data[tid] = current_val;
        __syncthreads();
    }
    
    dp_new[gid] = current_val;
}

// Tối ưu 4: Reduction kernel để tính tổng song song
__global__ void sum_reduction_kernel(int *dp, int size, int *result) {
    extern __shared__ int sdata[];
    
    unsigned int tid = threadIdx.x;
    unsigned int i = blockIdx.x * blockDim.x + threadIdx.x;
    
    // Load data into shared memory
    sdata[tid] = (i < size) ? dp[i] : 0;
    __syncthreads();
    
    // Reduction in shared memory
    for (unsigned int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) {
            sdata[tid] = (sdata[tid] + sdata[tid + s]) % 1000;
        }
        __syncthreads();
    }
    
    // Write result for this block to global memory
    if (tid == 0) {
        atomicAdd(result, sdata[0]);
    }
}

bool predict_optimized(int N, int K, int* w_cpu, int* output_cpu, int* w_gpu, int* output_gpu) {
    int *dp1 = nullptr, *dp2 = nullptr, *d_items = nullptr, *d_result = nullptr;
    hipError_t err;
    
    // Get device properties for optimization
    hipDeviceProp_t prop;
    hipGetDeviceProperties(&prop, 0);
    
    // Optimal block size based on device capabilities
    int optimal_block_size = min(256, prop.maxThreadsPerBlock);
    int shared_mem_size = prop.sharedMemPerBlock;
    
    // Memory allocation with optimal alignment
    size_t dp_size = (K + 1) * sizeof(int);
    err = hipMalloc(&dp1, dp_size);
    if (err != hipSuccess) return false;
    
    err = hipMalloc(&dp2, dp_size);
    if (err != hipSuccess) {
        hipFree(dp1);
        return false;
    }
    
    err = hipMalloc(&d_items, N * sizeof(int));
    if (err != hipSuccess) {
        hipFree(dp1); hipFree(dp2);
        return false;
    }
    
    err = hipMalloc(&d_result, sizeof(int));
    if (err != hipSuccess) {
        hipFree(dp1); hipFree(dp2); hipFree(d_items);
        return false;
    }
    
    // Tối ưu 5: Sử dụng streams để overlap computation và memory transfer
    hipStream_t stream1, stream2;
    hipStreamCreate(&stream1);
    hipStreamCreate(&stream2);
    
    // Copy items to GPU asynchronously
    err = hipMemcpyAsync(d_items, w_gpu, N * sizeof(int), hipMemcpyDeviceToDevice, stream1);
    if (err != hipSuccess) {
        hipFree(dp1); hipFree(dp2); hipFree(d_items); hipFree(d_result);
        return false;
    }
    
    // Initialize DP array with vectorized kernel
    dim3 init_block(optimal_block_size);
    dim3 init_grid(((K + 1) / 4 + init_block.x - 1) / init_block.x);
    init_kernel_optimized<<<init_grid, init_block, 0, stream1>>>(dp1, K + 1);
    
    hipStreamSynchronize(stream1);
    
    int *dp_old = dp1;
    int *dp_new = dp2;
    
    // Tối ưu 6: Batch processing với kernel fusion
    int batch_size = min(8, N); // Process multiple items per kernel launch
    int shared_mem_per_thread = sizeof(int) * 2; // For current and dependency values
    int max_shared_mem = shared_mem_size / shared_mem_per_thread;
    int actual_block_size = min(optimal_block_size, max_shared_mem);
    
    dim3 update_block(actual_block_size);
    dim3 update_grid((K + 1 + update_block.x - 1) / update_block.x);
    size_t shared_size = actual_block_size * sizeof(int) * 2;
    
    for (int i = 0; i < N; i += batch_size) {
        int current_batch = min(batch_size, N - i);
        
        if (current_batch > 1) {
            // Use fused kernel for multiple items
            fused_update_kernel<<<update_grid, update_block, shared_size, stream1>>>(
                dp_old, dp_new, d_items, i, current_batch, K);
            i += current_batch - 1; // Adjust for loop increment
        } else {
            // Single item kernel with shared memory optimization
            int item_val;
            hipMemcpyAsync(&item_val, d_items + i, sizeof(int), hipMemcpyDeviceToHost, stream2);
            hipStreamSynchronize(stream2);
            
            update_kernel_optimized<<<update_grid, update_block, shared_size, stream1>>>(
                dp_old, dp_new, item_val, K);
        }
        
        hipStreamSynchronize(stream1);
        
        // Swap pointers
        int *temp = dp_old;
        dp_old = dp_new;
        dp_new = temp;
    }
    
    // Tối ưu 7: Parallel reduction để tính tổng
    hipMemsetAsync(d_result, 0, sizeof(int), stream1);
    
    int reduction_block_size = min(512, prop.maxThreadsPerBlock);
    int reduction_grid_size = (K + 1 + reduction_block_size - 1) / reduction_block_size;
    size_t reduction_shared_size = reduction_block_size * sizeof(int);
    
    sum_reduction_kernel<<<reduction_grid_size, reduction_block_size, reduction_shared_size, stream1>>>(
        dp_old, K + 1, d_result);
    
    hipStreamSynchronize(stream1);
    
    // Copy result back
    int total;
    err = hipMemcpy(&total, d_result, sizeof(int), hipMemcpyDeviceToHost);
    if (err != hipSuccess) {
        hipStreamDestroy(stream1); hipStreamDestroy(stream2);
        hipFree(dp1); hipFree(dp2); hipFree(d_items); hipFree(d_result);
        return false;
    }
    
    total %= 1000;
    *output_cpu = total;
    hipMemcpy(output_gpu, &total, sizeof(int), hipMemcpyHostToDevice);
    
    // Cleanup
    hipStreamDestroy(stream1);
    hipStreamDestroy(stream2);
    hipFree(dp1);
    hipFree(dp2);
    hipFree(d_items);
    hipFree(d_result);
    
    return true;
}

// Tối ưu 8: Version sử dụng GPU memory hierarchy tối ưu
bool predict_ultra_optimized(int N, int K, int* w_cpu, int* output_cpu, int* w_gpu, int* output_gpu) {
    // Sử dụng managed memory cho tự động tối ưu hóa
    int *dp1, *dp2, *items;
    
    hipMallocManaged(&dp1, (K + 1) * sizeof(int));
    hipMallocManaged(&dp2, (K + 1) * sizeof(int));
    hipMallocManaged(&items, N * sizeof(int));
    
    // Prefetch data to GPU
    hipMemPrefetchAsync(dp1, (K + 1) * sizeof(int), 0);
    hipMemPrefetchAsync(dp2, (K + 1) * sizeof(int), 0);
    hipMemcpy(items, w_gpu, N * sizeof(int), hipMemcpyDeviceToDevice);
    hipMemPrefetchAsync(items, N * sizeof(int), 0);
    
    // Get optimal configuration
    hipDeviceProp_t prop;
    hipGetDeviceProperties(&prop, 0);
    
    int block_size = 256;
    int grid_size = (K + 1 + block_size - 1) / block_size;
    
    // Initialize
    init_kernel_optimized<<<grid_size, block_size>>>(dp1, K + 1);
    hipDeviceSynchronize();
    
    int *dp_current = dp1;
    int *dp_next = dp2;
    
    // Process items with maximum parallelism
    for (int i = 0; i < N; i++) {
        update_kernel_optimized<<<grid_size, block_size, block_size * sizeof(int)>>>(
            dp_current, dp_next, items[i], K);
        hipDeviceSynchronize();
        
        std::swap(dp_current, dp_next);
    }
    
    // Calculate sum with reduction
    int total = 0;
    for (int j = 0; j <= K; j++) {
        total = (total + dp_current[j]) % 1000;
    }
    
    *output_cpu = total;
    hipMemcpy(output_gpu, &total, sizeof(int), hipMemcpyHostToDevice);
    
    hipFree(dp1);
    hipFree(dp2);
    hipFree(items);
    
    return true;
}