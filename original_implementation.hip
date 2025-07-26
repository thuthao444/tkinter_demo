#include <hip/hip_runtime.h>
#include <cstdlib>

// Kernel khởi tạo mảng DP
__global__ void init_kernel(int *dp, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        dp[idx] = (idx == 0) ? 1 : 0;
    }
}

// Kernel cập nhật mảng DP cho từng món hàng
__global__ void update_kernel(int *dp_old, int *dp_new, int item, int K) {
    int j = blockIdx.x * blockDim.x + threadIdx.x;
    if (j <= K) {
        if (j < item) {
            dp_new[j] = dp_old[j];
        } else {
            int temp = dp_old[j] + dp_old[j - item];
            dp_new[j] = temp % 1000;
        }
    }
}

bool predict(int N, int K, int* w_cpu, int* output_cpu, int* w_gpu, int* output_gpu) {
    int *dp1 = nullptr, *dp2 = nullptr;
    hipError_t err;

    // Cấp phát bộ nhớ cho 2 mảng DP trên GPU
    err = hipMalloc(&dp1, (K+1)*sizeof(int));
    if (err != hipSuccess) return false;
    err = hipMalloc(&dp2, (K+1)*sizeof(int));
    if (err != hipSuccess) {
        hipFree(dp1);
        return false;
    }

    // Khởi tạo mảng DP ban đầu
    dim3 block(256);
    dim3 grid((K+1 + block.x - 1) / block.x);
    init_kernel<<<grid, block>>>(dp1, K+1);
    if (hipGetLastError() != hipSuccess) {
        hipFree(dp1); hipFree(dp2);
        return false;
    }
    hipDeviceSynchronize();

    // Sao chép dữ liệu món hàng từ GPU sang CPU
    int *h_items = (int*)malloc(N * sizeof(int));
    if (h_items == NULL) {
        hipFree(dp1); hipFree(dp2);
        return false;
    }
    err = hipMemcpy(h_items, w_gpu, N * sizeof(int), hipMemcpyDeviceToHost);
    if (err != hipSuccess) {
        free(h_items); hipFree(dp1); hipFree(dp2);
        return false;
    }

    int *dp_old = dp1;
    int *dp_new = dp2;

    // Cấu hình kernel cập nhật
    dim3 update_block(256);
    dim3 update_grid((K+1 + update_block.x - 1) / update_block.x);

    // Xử lý từng món hàng
    for (int i = 0; i < N; i++) {
        int item = h_items[i];
        update_kernel<<<update_grid, update_block>>>(dp_old, dp_new, item, K);
        if (hipGetLastError() != hipSuccess) {
            free(h_items); hipFree(dp1); hipFree(dp2);
            return false;
        }
        hipDeviceSynchronize();

        // Hoán đổi con trỏ mảng DP
        int *temp = dp_old;
        dp_old = dp_new;
        dp_new = temp;
    }

    // Sao chép kết quả từ GPU sang CPU
    int *h_dp = (int*)malloc((K+1)*sizeof(int));
    if (h_dp == NULL) {
        free(h_items); hipFree(dp1); hipFree(dp2);
        return false;
    }
    err = hipMemcpy(h_dp, dp_old, (K+1)*sizeof(int), hipMemcpyDeviceToHost);
    if (err != hipSuccess) {
        free(h_dp); free(h_items); hipFree(dp1); hipFree(dp2);
        return false;
    }

    int total = 0;
    for (int j = 0; j <= K; j++) {
        total = (total + h_dp[j]) % 1000;
    }

    *output_cpu = total;
    hipMemcpy(output_gpu, &total, sizeof(int), hipMemcpyHostToDevice);

    free(h_dp);
    free(h_items);
    hipFree(dp1);
    hipFree(dp2);

    return true;
}