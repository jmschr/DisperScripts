network_device = {i:i for i in range(10)}

for key in network_device:
    if key==5:
        network_device.update({11: 11})

print(network_device)
