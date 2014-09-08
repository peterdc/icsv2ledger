import os
from PIL import Image
from icsv2ledger import prompt_for_value
# import readline
# import rlcompleter
import Tkinter, tkFileDialog
import pyinsane.abstract as pyinsane
from pyinsane.abstract import SaneException

canon_driver_options = {'resolution': 300, 'deskew detection': 1, 'auto scan': 1, 'Size': 'Auto Size'}
floss_driver_options = {'resolution': 300, 'rollerdeskew': 1, 'swdeskew': 1, 'mode': 'Gray', 'swcrop': 1, 'source': 'ADF Duplex', 'page-height': 66182092, 'br-y': 66182092}
onesided_no_swdeskew = {'resolution': 300, 'rollerdeskew': 1, 'mode': 'Gray', 'swcrop': 1, 'source': 'ADF Front', 'page-height': 66182092, 'br-y': 66182092}

def set_device_options(options, device):
    for key in options:
        device.options[key].value = options[key]
    return device

def setup_scanner(options):
    devices = pyinsane.get_devices()
    if len(devices) <= 0:
        print('no scanner available')
        return None
    device = devices[0]
    print("I'm going to use the following scanner: %s" % (str(device)))
    device = set_device_options(options, device)
    return device

def try_scan(entry, payee, device, directory, attempts=3):
    attempt = 0
    receipt = None
    while attempt < attempts:
        try:
            receipt = scan_receipt(entry, payee, device, directory)
            break
        except SaneException:
            attempts += 1
            print('Got SaneException, trying attempt {0} of 3'.format(attempts))
    return receipt

def scan_receipt(entry, payee, device, directory):
    # http://docs.python.org/2/library/shutil.html
    value = prompt_for_value('(S)can, (C)hoose, or (P)ass', ['Scan', 'Choose', 'Pass'], 'Pass')
    file_extension = ".jpg"
    file_is_pdf = False
    if value:
        value = value.upper()
    else:
        value = 'PASS'

    if value == 'CHOOSE' or value == 'C':
        root = Tkinter.Tk()
        root.withdraw()

        orig_image_path = tkFileDialog.askopenfilename()
        file_name, file_extension = os.path.splitext(orig_image_path)
        if file_extension.upper() == ".PDF":
            file_is_pdf = True
            img = orig_image_path
        else:
            img = Image.open(orig_image_path)
    elif value == 'SCAN' or value == 'S':
        scan_session = device.scan(multiple=False)
        try:
            while True:
                scan_session.scan.read()
        except SaneException:
            scan_session.scan.cancel()
            raise
        except EOFError:
            pass
        img = scan_session.images[0]
    elif value == 'PASS' or value == 'P':
        return
    else:
        raise ValueError('Must be one of: Scan, Choose, or Pass')

    amount = entry.credit if entry.credit else entry.debit
    for ch in ['-', '.']:
        if ch in amount:
            amount = amount.replace(ch, '')

    output_file_name = '{0}_{1}_{2}{3}'.format(entry.date, payee, amount, file_extension)
    output_file_path = os.path.join(directory, output_file_name)
    if file_is_pdf:
        os.rename(orig_image_path, output_file_path)
    else:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(output_file_path, "JPEG")
    return(output_file_path)

# def prompter(prompt, values, default):
#
#     def completer(text, state):
#         for val in values:
#             if text.upper() in val.upper():
#                 if not state:
#                     return val
#                 else:
#                     state -= 1
#         return None
#
#     # There are no word deliminators as each account name
#     # is one word.  eg ':' and ' ' are valid parts of account
#     # name and don't indicate a new word
#     readline.set_completer_delims("")
#     readline.set_completer(completer)
#     if 'libedit' in readline.__doc__:
#         readline.parse_and_bind("bind ^I rl_complete")
#     else:
#         readline.parse_and_bind("tab: complete")
#
#     return raw_input('{0} [{1}] > '.format(prompt, default))
