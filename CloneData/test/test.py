import torch

print(torch.cuda.is_available())      # Phải ra True
print(torch.cuda.get_device_name(0))  # NVIDIA GeForce RTX 4050 Laptop GPU
