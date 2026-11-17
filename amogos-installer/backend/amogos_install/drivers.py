# Present the hardware coverage already supplied by the Arch image.
def recommendations(runner):
    return [
        dict(device='Linux Zen',packages=['linux-zen','linux-firmware'],note='Kernel and Wi-Fi firmware'),
        dict(device='Intel and AMD graphics',packages=['mesa','vulkan-intel','vulkan-radeon'],note='Kernel modesetting and Mesa'),
        dict(device='NVIDIA graphics',packages=['nvidia-open-dkms','linux-zen-headers'],note='Zen modules for supported NVIDIA GPUs'),
    ]
