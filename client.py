import requests
import psutil
import socket
import threading
import time
import os
import subprocess
import platform

SERVER_URL = 'http://192.168.68.124:5001'

def get_device_info():
    return {
        'name': socket.gethostname(),
        'cpu_usage': psutil.cpu_percent(),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent
    }

def register_device():
    data = get_device_info()
    response = requests.post(f'{SERVER_URL}/register', json=data)
    print(response.json())

def auto_update():
    while True:
        register_device()
        time.sleep(60)  # Update every 60 seconds

def perform_action(action):
    if action == 'shutdown':
        if platform.system() == 'Windows':
            os.system('shutdown /s /t 1')
        else:
            os.system('shutdown now')
    elif action == 'restart':
        if platform.system() == 'Windows':
            os.system('shutdown /r /t 1')
        else:
            os.system('reboot')
    elif action == 'sleep':
        if platform.system() == 'Windows':
            os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
        else:
            os.system('systemctl suspend')
    elif action == 'lock':
        if platform.system() == 'Windows':
            os.system('rundll32.exe user32.dll,LockWorkStation')
        else:
            os.system('xdg-screensaver lock')
    elif action == 'remote_desktop':
        if platform.system() == 'Windows':
            # Implement remote desktop functionality for Windows
            print("Remote Desktop action requested for Windows. Please ensure RDP is enabled.")
        else:
            # Start VNC server for Unix/Linux systems
            subprocess.run(['vncserver', ':1'])

def check_for_actions():
    while True:
        response = requests.get(f'{SERVER_URL}/get_action?device_name={socket.gethostname()}')
        if response.status_code == 200:
            action = response.json().get('action')
            if action:
                perform_action(action)
        time.sleep(10)  # Check for actions every 10 seconds

if __name__ == '__main__':
    update_thread = threading.Thread(target=auto_update)
    update_thread.daemon = True
    update_thread.start()

    action_thread = threading.Thread(target=check_for_actions)
    action_thread.daemon = True
    action_thread.start()

    update_thread.join()
    action_thread.join()