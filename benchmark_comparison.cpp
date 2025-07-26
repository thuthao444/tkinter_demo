#include <hip/hip_runtime.h>
#include <chrono>
#include <iostream>
#include <vector>
#include <random>
#include <iomanip>

// Include các functions đã tối ưu
extern bool predict(int N, int K, int* w_cpu, int* output_cpu, int* w_gpu, int* output_gpu);
extern bool predict_optimized(int N, int K, int* w_cpu, int* output_cpu, int* w_gpu, int* output_gpu);
extern bool predict_ultra_optimized(int N, int K, int* w_cpu, int* output_cpu, int* w_gpu, int* output_gpu);
extern bool predict_ultimate_optimized(int N, int K, int* w_cpu, int* output_cpu, int* w_gpu, int* output_gpu);

class GPUTimer {
private:
    hipEvent_t start_event, stop_event;
    
public:
    GPUTimer() {
        hipEventCreate(&start_event);
        hipEventCreate(&stop_event);
    }
    
    ~GPUTimer() {
        hipEventDestroy(start_event);
        hipEventDestroy(stop_event);
    }
    
    void start() {
        hipEventRecord(start_event, 0);
    }
    
    float stop() {
        hipEventRecord(stop_event, 0);
        hipEventSynchronize(stop_event);
        
        float elapsed_time;
        hipEventElapsedTime(&elapsed_time, start_event, stop_event);
        return elapsed_time;
    }
};

struct BenchmarkResult {
    std::string method_name;
    float avg_time_ms;
    float min_time_ms;
    float max_time_ms;
    float throughput_items_per_sec;
    bool correctness;
    int result_value;
};

void generate_test_data(std::vector<int>& items, int N, int max_weight = 100) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(1, max_weight);
    
    items.resize(N);
    for (int i = 0; i < N; i++) {
        items[i] = dis(gen);
    }
}

BenchmarkResult benchmark_method(
    const std::string& method_name,
    bool (*method_func)(int, int, int*, int*, int*, int*),
    const std::vector<int>& items,
    int K,
    int num_runs = 10
) {
    int N = items.size();
    
    // Prepare GPU memory
    int *d_items, *d_output;
    hipMalloc(&d_items, N * sizeof(int));
    hipMalloc(&d_output, sizeof(int));
    hipMemcpy(d_items, items.data(), N * sizeof(int), hipMemcpyHostToDevice);
    
    // Warm up
    int cpu_output, gpu_output;
    method_func(N, K, const_cast<int*>(items.data()), &cpu_output, d_items, d_output);
    
    GPUTimer timer;
    std::vector<float> times;
    times.reserve(num_runs);
    
    bool all_correct = true;
    int reference_result = cpu_output;
    
    // Benchmark runs
    for (int run = 0; run < num_runs; run++) {
        timer.start();
        
        bool success = method_func(N, K, const_cast<int*>(items.data()), &cpu_output, d_items, d_output);
        
        float elapsed = timer.stop();
        times.push_back(elapsed);
        
        if (!success || (run > 0 && cpu_output != reference_result)) {
            all_correct = false;
        }
    }
    
    // Calculate statistics
    float sum = 0, min_time = times[0], max_time = times[0];
    for (float t : times) {
        sum += t;
        min_time = std::min(min_time, t);
        max_time = std::max(max_time, t);
    }
    float avg_time = sum / num_runs;
    
    // Cleanup
    hipFree(d_items);
    hipFree(d_output);
    
    BenchmarkResult result;
    result.method_name = method_name;
    result.avg_time_ms = avg_time;
    result.min_time_ms = min_time;
    result.max_time_ms = max_time;
    result.throughput_items_per_sec = (N * 1000.0f) / avg_time; // items per second
    result.correctness = all_correct;
    result.result_value = cpu_output;
    
    return result;
}

void print_device_info() {
    hipDeviceProp_t prop;
    hipGetDeviceProperties(&prop, 0);
    
    std::cout << "\n=== GPU Device Information ===" << std::endl;
    std::cout << "Device Name: " << prop.name << std::endl;
    std::cout << "Compute Capability: " << prop.major << "." << prop.minor << std::endl;
    std::cout << "Global Memory: " << prop.totalGlobalMem / (1024*1024*1024.0) << " GB" << std::endl;
    std::cout << "Shared Memory per Block: " << prop.sharedMemPerBlock / 1024.0 << " KB" << std::endl;
    std::cout << "Max Threads per Block: " << prop.maxThreadsPerBlock << std::endl;
    std::cout << "Multiprocessor Count: " << prop.multiProcessorCount << std::endl;
    std::cout << "Memory Clock Rate: " << prop.memoryClockRate / 1000.0 << " MHz" << std::endl;
    std::cout << "Memory Bus Width: " << prop.memoryBusWidth << " bits" << std::endl;
    std::cout << "Peak Memory Bandwidth: " << 
        2.0 * prop.memoryClockRate * (prop.memoryBusWidth / 8) / 1e6 << " GB/s" << std::endl;
    std::cout << "==============================\n" << std::endl;
}

void print_benchmark_results(const std::vector<BenchmarkResult>& results) {
    std::cout << std::fixed << std::setprecision(3);
    std::cout << "\n=== Benchmark Results ===" << std::endl;
    std::cout << std::left;
    std::cout << std::setw(25) << "Method"
              << std::setw(12) << "Avg Time(ms)"
              << std::setw(12) << "Min Time(ms)"
              << std::setw(12) << "Max Time(ms)"
              << std::setw(15) << "Throughput(K/s)"
              << std::setw(10) << "Correct"
              << std::setw(10) << "Result" << std::endl;
    std::cout << std::string(100, '-') << std::endl;
    
    float best_time = std::numeric_limits<float>::max();
    for (const auto& result : results) {
        if (result.correctness) {
            best_time = std::min(best_time, result.avg_time_ms);
        }
    }
    
    for (const auto& result : results) {
        std::cout << std::setw(25) << result.method_name
                  << std::setw(12) << result.avg_time_ms
                  << std::setw(12) << result.min_time_ms
                  << std::setw(12) << result.max_time_ms
                  << std::setw(15) << result.throughput_items_per_sec / 1000.0
                  << std::setw(10) << (result.correctness ? "YES" : "NO")
                  << std::setw(10) << result.result_value;
        
        if (result.correctness && std::abs(result.avg_time_ms - best_time) < 0.001) {
            std::cout << " <- FASTEST";
        }
        
        if (result.correctness && best_time > 0) {
            float speedup = best_time / result.avg_time_ms;
            if (speedup < 1.0) {
                std::cout << " (Speedup: " << std::setprecision(2) << speedup << "x)";
            }
        }
        
        std::cout << std::endl;
    }
    
    std::cout << "========================\n" << std::endl;
}

void comprehensive_benchmark() {
    print_device_info();
    
    // Test cases with different problem sizes
    std::vector<std::pair<int, int>> test_cases = {
        {50, 1000},      // Small problem
        {100, 5000},     // Medium problem  
        {200, 10000},    // Large problem
        {500, 20000},    // Very large problem
        {1000, 50000}    // Extreme problem
    };
    
    for (auto [N, K] : test_cases) {
        std::cout << "\n=== Testing N=" << N << ", K=" << K << " ===" << std::endl;
        
        // Generate test data
        std::vector<int> items;
        generate_test_data(items, N, std::min(K/10, 100));
        
        std::vector<BenchmarkResult> results;
        
        // Benchmark all methods
        try {
            results.push_back(benchmark_method("Original", predict, items, K));
        } catch (...) {
            std::cout << "Original method failed" << std::endl;
        }
        
        try {
            results.push_back(benchmark_method("Optimized", predict_optimized, items, K));
        } catch (...) {
            std::cout << "Optimized method failed" << std::endl;
        }
        
        try {
            results.push_back(benchmark_method("Ultra Optimized", predict_ultra_optimized, items, K));
        } catch (...) {
            std::cout << "Ultra optimized method failed" << std::endl;
        }
        
        try {
            results.push_back(benchmark_method("Ultimate Optimized", predict_ultimate_optimized, items, K));
        } catch (...) {
            std::cout << "Ultimate optimized method failed" << std::endl;
        }
        
        print_benchmark_results(results);
        
        // Memory usage analysis
        size_t dp_memory = (K + 1) * sizeof(int) * 2; // Two DP arrays
        size_t items_memory = N * sizeof(int);
        size_t total_memory = dp_memory + items_memory;
        
        std::cout << "Memory Usage Analysis:" << std::endl;
        std::cout << "  DP Arrays: " << dp_memory / (1024.0 * 1024.0) << " MB" << std::endl;
        std::cout << "  Items Array: " << items_memory / (1024.0 * 1024.0) << " MB" << std::endl;
        std::cout << "  Total GPU Memory: " << total_memory / (1024.0 * 1024.0) << " MB" << std::endl;
        
        // Theoretical performance analysis
        long long total_operations = (long long)N * K;
        if (!results.empty() && results[0].correctness) {
            float best_time_sec = results[0].avg_time_ms / 1000.0f;
            for (const auto& r : results) {
                if (r.correctness && r.avg_time_ms < results[0].avg_time_ms) {
                    best_time_sec = r.avg_time_ms / 1000.0f;
                }
            }
            
            float gops = (total_operations / 1e9) / best_time_sec;
            std::cout << "  Peak Performance: " << std::setprecision(2) << gops << " GOPS" << std::endl;
        }
        
        std::cout << std::endl;
    }
}

int main() {
    // Initialize HIP
    hipError_t err = hipSetDevice(0);
    if (err != hipSuccess) {
        std::cerr << "Failed to initialize HIP device" << std::endl;
        return -1;
    }
    
    std::cout << "GPU Dynamic Programming Optimization Benchmark" << std::endl;
    std::cout << "=============================================" << std::endl;
    
    comprehensive_benchmark();
    
    return 0;
}