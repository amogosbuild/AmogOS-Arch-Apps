# Build the installed Zen initramfs after removing the live-only Archiso hooks.
def prepare_kernels(runner, target, medium):
    conf=target/'etc/mkinitcpio.conf.d/10-amogos.conf'
    conf.write_text('# Plymouth and normal disk boot hooks.\nHOOKS=(base udev autodetect microcode modconf kms keyboard keymap consolefont block plymouth filesystems fsck)\n')
    runner.run(['chroot',str(target),'mkinitcpio','-p','linux-zen'],timeout=1800)
