import os
from PIL import Image
import icsv2ledger
import pyinsane2

floss_driver_options = {'resolution': 300, 'rollerdeskew': 1, 'swdeskew': 1, 'mode': 'Gray', 'swcrop': 1, 'source': 'ADF Duplex', 'page-height': 66182092, 'br-y': 66182092}
onesided_no_swdeskew = {'resolution': 300, 'rollerdeskew': 1, 'mode': 'Gray', 'swcrop': 1, 'source': 'ADF Front', 'page-height': 66182092, 'br-y': 66182092}

def set_device_options(options, device):
    for key in options:
        # print(key)
        # print(device.options[key].constraint)
        # print(options[key])
        device.options[key].value = options[key]
    return device

def setup_scanner(options):
    pyinsane2.init()
    try:
        devices = pyinsane2.get_devices()
        if len(devices) <= 0:
            print('no scanner available')
            return None
        device = devices[0]
        # device = pyinsane2.Scanner(name="canon_dr:libusb:020:008")
        print("I'm going to use the following scanner: %s" % (str(device)))
    except PyinsaneException:
            print("No scanner found")
            return
    device = set_device_options(options, device)
    return device

def try_scan(entry, payee, device, directory, attempts=3):
    attempt = 1
    receipt = None
    while attempt <= attempts:
        try:
            receipt = scan_receipt(entry, payee, device, directory)
            break
        except:
            attempt += 1
            if attempt <= attempts:
                print('Got Exception, trying attempt {0} of 3'.format(attempt))
            else:
                print('Too many exceptions, bailing')
                raise
    return receipt

def scan_receipt(entry, payee, device, directory):
    # http://docs.python.org/2/library/shutil.html
    amount = entry.credit if entry.credit else entry.debit
    for ch in ['-', '.']:
        if ch in amount:
            amount = amount.replace(ch, '')

    value = icsv2ledger.prompt_for_value('(S)can, (M)ult or (P)ass', ['Scan', 'Mult', 'Pass'], 'Pass')
    file_extension = ".jpg"
    file_is_pdf = False
    if value:
        value = value.upper()
    else:
        value = 'PASS'

    if value == 'SCAN' or value == 'S':
        pyinsane2.maximize_scan_area(device)
        scan_session = device.scan(multiple=False)
        try:
            while True:
                scan_session.scan.read()
        except EOFError:
            pass
        except PyinsaneException:
            scan_session.scan.cancel()
            raise
        img = scan_session.images[0]
    elif value == 'MULT' or value == 'M':
        pages = int(raw_input("Number of pages: [2] > ") or "2")
        images = []
        for page in range(pages):
            pyinsane2.maximize_scan_area(device)
            scan_session = device.scan(multiple=False)
            try:
                while True:
                    scan_session.scan.read()
            except EOFError:
                pass
            except PyinsaneException:
                scan_session.scan.cancel()
                raise
            images.append(scan_session.images[0]) 
            if page < pages - 1:
                raw_input('Page {0} ready?'.format(str(page+2)))
        img = images[0]
        for page in range(1, pages):
            image = images[page]
            output_file_name = '{0}_{1}_{2}_Page_{4}{3}'.format(entry.date, payee, amount, file_extension, str(page+1))
            output_file_path = os.path.join(directory, output_file_name)
            image.save(output_file_path, "JPEG")

    elif value == 'PASS' or value == 'P':
        return
    else:
        raise ValueError('Must be one of: Scan, Mult, or Pass')

    output_file_name = '{0}_{1}_{2}{3}'.format(entry.date, payee, amount, file_extension)
    output_file_path = os.path.join(directory, output_file_name)
    img.save(output_file_path, "JPEG")
    return(output_file_path)

