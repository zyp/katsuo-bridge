import urllib
import urllib.parse

def open_url(url):
    u = urllib.parse.urlparse(url)
    match u.scheme:
        case 'jtag+ftdi':
            from .jtag import FtdiJtagTransport
            return FtdiJtagTransport(url[5:])

        case 'usb': # TODO: specify control/bulk?
            from .usb import UsbTransport
            return UsbTransport(url)
        
        case _:
            raise ValueError(f"Unsupported URL scheme: {u.scheme}")
