# Makefile for GPU Dynamic Programming Optimization
# Requires ROCm/HIP installation

# Compiler
CXX = hipcc
NVCC = nvcc

# Compiler flags
HIP_FLAGS = -O3 -std=c++17 -march=native
CUDA_FLAGS = -O3 -std=c++17 -arch=sm_70 # Adjust arch for your GPU

# Include directories
INCLUDES = -I/opt/rocm/include

# Libraries
LIBS = -L/opt/rocm/lib -lhip_hcc

# Source files
ORIGINAL_SRC = original_implementation.hip
OPTIMIZED_SRC = optimized_gpu_dp.hip
ADVANCED_SRC = advanced_gpu_optimizations.hip
BENCHMARK_SRC = benchmark_comparison.cpp

# Output binaries
BENCHMARK_BIN = gpu_dp_benchmark

# Detect GPU vendor
GPU_VENDOR := $(shell lspci | grep -i "vga\|3d\|display" | head -n1)

ifeq ($(findstring AMD,$(GPU_VENDOR)),AMD)
    COMPILER = $(CXX)
    FLAGS = $(HIP_FLAGS)
    LIBS += -lhip_hcc
else ifeq ($(findstring NVIDIA,$(GPU_VENDOR)),NVIDIA)
    COMPILER = $(NVCC)
    FLAGS = $(CUDA_FLAGS)
    LIBS = -lcudart
else
    # Default to HIP
    COMPILER = $(CXX)
    FLAGS = $(HIP_FLAGS)
endif

# Default target
all: $(BENCHMARK_BIN)

# Build benchmark
$(BENCHMARK_BIN): $(OPTIMIZED_SRC) $(ADVANCED_SRC) $(BENCHMARK_SRC)
	$(COMPILER) $(FLAGS) $(INCLUDES) -o $@ $^ $(LIBS)

# Individual targets
optimized: $(OPTIMIZED_SRC)
	$(COMPILER) $(FLAGS) $(INCLUDES) -c $< -o optimized_gpu_dp.o

advanced: $(ADVANCED_SRC)
	$(COMPILER) $(FLAGS) $(INCLUDES) -c $< -o advanced_gpu_optimizations.o

# Test targets
test_small: $(BENCHMARK_BIN)
	./$(BENCHMARK_BIN) --size=small

test_medium: $(BENCHMARK_BIN)
	./$(BENCHMARK_BIN) --size=medium

test_large: $(BENCHMARK_BIN)
	./$(BENCHMARK_BIN) --size=large

# Performance profiling
profile: $(BENCHMARK_BIN)
	rocprof --hip-trace ./$(BENCHMARK_BIN)

profile_nvidia: $(BENCHMARK_BIN)
	nvprof ./$(BENCHMARK_BIN)

# Memory check
memcheck: $(BENCHMARK_BIN)
	rocm-dbgapi ./$(BENCHMARK_BIN)

memcheck_nvidia: $(BENCHMARK_BIN)
	cuda-memcheck ./$(BENCHMARK_BIN)

# Clean
clean:
	rm -f *.o $(BENCHMARK_BIN) *.csv *.json

# Install dependencies (Ubuntu/Debian)
install_deps:
	sudo apt update
	sudo apt install rocm-dev hip-dev

# Show GPU info
gpu_info:
	rocm-smi
	hipcc --version

# Optimization flags for different scenarios
debug: FLAGS += -g -DDEBUG
debug: $(BENCHMARK_BIN)

release: FLAGS += -DNDEBUG -funroll-loops
release: $(BENCHMARK_BIN)

# Platform-specific optimizations
amd_optimized: FLAGS += -mcpu=native -mtune=native
amd_optimized: $(BENCHMARK_BIN)

nvidia_optimized: FLAGS += -gencode arch=compute_70,code=sm_70 -gencode arch=compute_80,code=sm_80
nvidia_optimized: $(BENCHMARK_BIN)

# Help target
help:
	@echo "Available targets:"
	@echo "  all              - Build benchmark executable"
	@echo "  optimized        - Compile optimized implementation"
	@echo "  advanced         - Compile advanced optimizations"
	@echo "  test_small       - Run small problem size tests"
	@echo "  test_medium      - Run medium problem size tests"  
	@echo "  test_large       - Run large problem size tests"
	@echo "  profile          - Profile with ROCm tools"
	@echo "  profile_nvidia   - Profile with NVIDIA tools"
	@echo "  memcheck         - Check for memory errors (ROCm)"
	@echo "  memcheck_nvidia  - Check for memory errors (NVIDIA)"
	@echo "  clean            - Remove built files"
	@echo "  install_deps     - Install ROCm dependencies"
	@echo "  gpu_info         - Show GPU information"
	@echo "  debug            - Build with debug symbols"
	@echo "  release          - Build optimized release"
	@echo "  amd_optimized    - Build with AMD-specific optimizations"
	@echo "  nvidia_optimized - Build with NVIDIA-specific optimizations"

.PHONY: all clean test_small test_medium test_large profile memcheck gpu_info help debug release amd_optimized nvidia_optimized install_deps