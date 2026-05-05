import sounddevice as sd

def list_devices():
    print("--- Audio Devices Detected ---")
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        device_type = []
        if d['max_input_channels'] > 0:
            device_type.append("Input")
        if d['max_output_channels'] > 0:
            device_type.append("Output")
        
        type_str = "/".join(device_type) if device_type else "None"
        default = "*" if i == sd.default.device[1] else " "
        print(f"{default} {i}: {d['name']} ({type_str}) - Sample Rate: {d['default_samplerate']}")

    print("\nDefault Output Device:", sd.default.device[1])
    
    if sd.default.device[1] < 0:
        print("\n!!! WARNING: No default output device detected. !!!")
        print("Possible fixes:")
        print("1. Ensure pulseaudio is installed: sudo apt install pulseaudio")
        print("2. Start pulseaudio: pulseaudio --start")
        print("3. Check if WSLg is working or if you need a Windows PulseAudio server.")
    else:
        print("\nSuccess: Output device(s) found.")

if __name__ == "__main__":
    try:
        list_devices()
    except Exception as e:
        print(f"Error listing devices: {e}")
