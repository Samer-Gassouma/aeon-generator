FROM nvidia/cuda:12.1-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    wget \
    curl \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install PyTorch with CUDA support
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Install Hunyuan3D-2 dependencies
RUN pip install trimesh numpy pillow transformers diffusers accelerate

# Clone and install Hunyuan3D-2 (optional - can be done at runtime)
# RUN git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2.git /tmp/hunyuan3d && \
#     cd /tmp/hunyuan3d && \
#     pip install -e . && \
#     cd /app && \
#     rm -rf /tmp/hunyuan3d

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p generated_weapons static

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Command to run the application
CMD ["python", "main.py"]