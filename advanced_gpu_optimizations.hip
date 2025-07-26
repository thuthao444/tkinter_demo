#include <hip/hip_runtime.h>
#include <hip/hip_cooperative_groups.h>
#include <cstdlib>
#include <algorithm>

namespace cg = cooperative_groups;

// Tối ưu 9: Sử dụng Cooperative Groups cho synchronization hiệu quả
__global__ void cooperative_update_kernel(int *dp_old, int *dp_new, int item, int K) {
    cg::grid_group grid = cg::this_grid();
    cg::thread_block block = cg::this_thread_block();
    cg::thread_block_tile<32> warp = cg::tiled_partition<32>(block);
    
    int gid = blockIdx.x * blockDim.x + threadIdx.x;
    int warp_id = threadIdx.x / 32;
    int lane_id = threadIdx.x % 32;
    
    extern __shared__ int shared_mem[];
    int *warp_shared = &shared_mem[warp_id * 32];
    
    if (gid <= K) {
        // Load data with warp-level coalescing
        warp_shared[lane_id] = dp_old[gid];
        warp.sync();
        
        int result;
        if (gid < item) {
            result = warp_shared[lane_id];
        } else {
            int dep_idx = gid - item;
            
            // Warp-level optimization for dependency access
            int dep_val;
            if (dep_idx >= blockIdx.x * blockDim.x && dep_idx < (blockIdx.x + 1) * blockDim.x) {
                // Dependency is in the same block
                int local_dep = dep_idx - blockIdx.x * blockDim.x;
                int dep_warp = local_dep / 32;
                int dep_lane = local_dep % 32;
                
                if (dep_warp == warp_id) {
                    dep_val = warp_shared[dep_lane];
                } else {
                    dep_val = shared_mem[local_dep];
                }
            } else {
                dep_val = dp_old[dep_idx];
            }
            
            result = (warp_shared[lane_id] + dep_val) % 1000;
        }
        
        warp_shared[lane_id] = result;
        warp.sync();
        dp_new[gid] = result;
    }
}

// Tối ưu 10: Warp-level primitives cho reduction nhanh hơn
__device__ __forceinline__ int warp_reduce_sum(int val) {
    #pragma unroll
    for (int offset = 16; offset > 0; offset /= 2) {
        val = (val + __shfl_down(val, offset)) % 1000;
    }
    return val;
}

__global__ void warp_optimized_sum_kernel(int *dp, int size, int *result) {
    int tid = threadIdx.x;
    int gid = blockIdx.x * blockDim.x + threadIdx.x;
    int lane_id = tid % 32;
    int warp_id = tid / 32;
    
    __shared__ int warp_sums[32]; // Max 32 warps per block
    
    // Each thread loads one element
    int val = (gid < size) ? dp[gid] : 0;
    
    // Warp-level reduction
    val = warp_reduce_sum(val);
    
    // First thread in each warp writes to shared memory
    if (lane_id == 0) {
        warp_sums[warp_id] = val;
    }
    
    __syncthreads();
    
    // Final reduction by first warp
    if (warp_id == 0) {
        val = (tid < (blockDim.x / 32)) ? warp_sums[tid] : 0;
        val = warp_reduce_sum(val);
        
        if (tid == 0) {
            atomicAdd(result, val);
        }
    }
}

// Tối ưu 11: Memory coalescing tối ưu với padding
__global__ void coalesced_update_kernel(int *dp_old, int *dp_new, int item, int K, int padded_size) {
    int gid = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (gid <= K) {
        // Sử dụng texture memory hoặc constant memory cho small arrays
        int current_val = dp_old[gid];
        
        if (gid >= item) {
            int dep_idx = gid - item;
            int dep_val = dp_old[dep_idx];
            current_val = (current_val + dep_val) % 1000;
        }
        
        // Coalesced write
        dp_new[gid] = current_val;
    }
}

// Tối ưu 12: Multi-GPU support với peer-to-peer communication
bool predict_multi_gpu(int N, int K, int* w_cpu, int* output_cpu, int* w_gpu, int* output_gpu) {
    int device_count;
    hipGetDeviceCount(&device_count);
    
    if (device_count < 2) {
        // Fallback to single GPU
        return predict_optimized(N, K, w_cpu, output_cpu, w_gpu, output_gpu);
    }
    
    // Enable peer access between GPUs
    for (int i = 0; i < device_count; i++) {
        for (int j = 0; j < device_count; j++) {
            if (i != j) {
                hipSetDevice(i);
                int can_access;
                hipDeviceCanAccessPeer(&can_access, i, j);
                if (can_access) {
                    hipDeviceEnablePeerAccess(j, 0);
                }
            }
        }
    }
    
    // Split work among GPUs
    int items_per_gpu = N / device_count;
    int *dp_arrays[4]; // Support up to 4 GPUs
    hipStream_t streams[4];
    
    for (int gpu = 0; gpu < device_count; gpu++) {
        hipSetDevice(gpu);
        hipMalloc(&dp_arrays[gpu], (K + 1) * sizeof(int));
        hipStreamCreate(&streams[gpu]);
    }
    
    // Initialize all GPUs
    for (int gpu = 0; gpu < device_count; gpu++) {
        hipSetDevice(gpu);
        dim3 block(256);
        dim3 grid((K + 1 + block.x - 1) / block.x);
        init_kernel_optimized<<<grid, block, 0, streams[gpu]>>>(dp_arrays[gpu], K + 1);
    }
    
    // Process items in parallel across GPUs
    for (int i = 0; i < N; i++) {
        int gpu = i % device_count;
        hipSetDevice(gpu);
        
        int item_val;
        hipMemcpy(&item_val, w_gpu + i, sizeof(int), hipMemcpyDeviceToHost);
        
        dim3 block(256);
        dim3 grid((K + 1 + block.x - 1) / block.x);
        
        cooperative_update_kernel<<<grid, block, block.x * sizeof(int), streams[gpu]>>>(
            dp_arrays[gpu], dp_arrays[gpu], item_val, K);
    }
    
    // Synchronize all GPUs
    for (int gpu = 0; gpu < device_count; gpu++) {
        hipSetDevice(gpu);
        hipStreamSynchronize(streams[gpu]);
    }
    
    // Aggregate results from all GPUs
    int total = 0;
    for (int gpu = 0; gpu < device_count; gpu++) {
        hipSetDevice(gpu);
        int *h_dp = (int*)malloc((K + 1) * sizeof(int));
        hipMemcpy(h_dp, dp_arrays[gpu], (K + 1) * sizeof(int), hipMemcpyDeviceToHost);
        
        for (int j = 0; j <= K; j++) {
            total = (total + h_dp[j]) % 1000;
        }
        
        free(h_dp);
        hipFree(dp_arrays[gpu]);
        hipStreamDestroy(streams[gpu]);
    }
    
    *output_cpu = total;
    hipMemcpy(output_gpu, &total, sizeof(int), hipMemcpyHostToDevice);
    
    return true;
}

// Tối ưu 13: Persistent kernel cho giảm thiểu kernel launch overhead
__global__ void persistent_dp_kernel(int *dp1, int *dp2, int *items, int N, int K, int *final_result) {
    extern __shared__ int shared_workspace[];
    
    int tid = threadIdx.x;
    int bid = blockIdx.x;
    int gid = bid * blockDim.x + tid;
    
    // Initialize
    if (gid <= K) {
        dp1[gid] = (gid == 0) ? 1 : 0;
    }
    __syncthreads();
    
    int *current_dp = dp1;
    int *next_dp = dp2;
    
    // Process all items in persistent kernel
    for (int item_idx = 0; item_idx < N; item_idx++) {
        int item = items[item_idx];
        
        // Load current values to shared memory
        if (gid <= K && tid < blockDim.x) {
            shared_workspace[tid] = current_dp[gid];
        }
        __syncthreads();
        
        // Update DP values
        if (gid <= K) {
            int result;
            if (gid < item) {
                result = shared_workspace[tid];
            } else {
                int dep_idx = gid - item;
                int dep_val;
                
                // Check if dependency is in shared memory
                int local_dep = dep_idx - bid * blockDim.x;
                if (local_dep >= 0 && local_dep < blockDim.x) {
                    dep_val = shared_workspace[local_dep];
                } else {
                    dep_val = current_dp[dep_idx];
                }
                
                result = (shared_workspace[tid] + dep_val) % 1000;
            }
            next_dp[gid] = result;
        }
        
        __syncthreads();
        
        // Swap pointers
        int *temp = current_dp;
        current_dp = next_dp;
        next_dp = temp;
    }
    
    // Final reduction in shared memory
    if (gid <= K) {
        shared_workspace[tid] = current_dp[gid];
    } else {
        shared_workspace[tid] = 0;
    }
    __syncthreads();
    
    // Tree reduction
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (tid < stride && tid + stride <= K) {
            shared_workspace[tid] = (shared_workspace[tid] + shared_workspace[tid + stride]) % 1000;
        }
        __syncthreads();
    }
    
    if (tid == 0) {
        atomicAdd(final_result, shared_workspace[0]);
    }
}

// Tối ưu 14: Dynamic parallelism cho adaptive load balancing
__global__ void dynamic_dp_kernel(int *dp_old, int *dp_new, int *items, int start_idx, int end_idx, int K) {
    int gid = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (gid <= K) {
        for (int i = start_idx; i < end_idx; i++) {
            int item = items[i];
            
            if (gid >= item) {
                dp_new[gid] = (dp_old[gid] + dp_old[gid - item]) % 1000;
            } else {
                dp_new[gid] = dp_old[gid];
            }
            
            __syncthreads();
            
            // Launch child kernels for complex dependencies
            if (threadIdx.x == 0 && item > 1000) {
                dim3 child_grid((K + 1 + 127) / 128);
                dim3 child_block(128);
                
                dynamic_dp_kernel<<<child_grid, child_block>>>(
                    dp_new, dp_old, items, i + 1, min(i + 4, end_idx), K);
                hipDeviceSynchronize();
                
                // Skip processed items
                i += 3;
            }
        }
    }
}

// Main optimized function với tất cả optimizations
bool predict_ultimate_optimized(int N, int K, int* w_cpu, int* output_cpu, int* w_gpu, int* output_gpu) {
    // Get device capabilities
    hipDeviceProp_t prop;
    hipGetDeviceProperties(&prop, 0);
    
    // Choose best strategy based on problem size
    if (N < 100 && K < 10000) {
        // Small problem: use persistent kernel
        int *dp1, *dp2, *items, *result;
        
        hipMalloc(&dp1, (K + 1) * sizeof(int));
        hipMalloc(&dp2, (K + 1) * sizeof(int));
        hipMalloc(&items, N * sizeof(int));
        hipMalloc(&result, sizeof(int));
        
        hipMemcpy(items, w_gpu, N * sizeof(int), hipMemcpyDeviceToDevice);
        hipMemset(result, 0, sizeof(int));
        
        dim3 block(min(256, prop.maxThreadsPerBlock));
        dim3 grid(max(1, (K + 1 + block.x - 1) / block.x));
        size_t shared_size = block.x * sizeof(int);
        
        persistent_dp_kernel<<<grid, block, shared_size>>>(dp1, dp2, items, N, K, result);
        hipDeviceSynchronize();
        
        int total;
        hipMemcpy(&total, result, sizeof(int), hipMemcpyDeviceToHost);
        
        *output_cpu = total % 1000;
        hipMemcpy(output_gpu, output_cpu, sizeof(int), hipMemcpyHostToDevice);
        
        hipFree(dp1); hipFree(dp2); hipFree(items); hipFree(result);
        
    } else if (N > 1000) {
        // Large problem: use multi-GPU if available
        return predict_multi_gpu(N, K, w_cpu, output_cpu, w_gpu, output_gpu);
        
    } else {
        // Medium problem: use cooperative groups
        return predict_optimized(N, K, w_cpu, output_cpu, w_gpu, output_gpu);
    }
    
    return true;
}