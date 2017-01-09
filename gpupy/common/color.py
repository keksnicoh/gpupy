import struct

def hex_to_rgba(hexstr):
    try:
        return [float(i)/255 for i in struct.unpack('BBBB', hexstr.decode('hex'))]
    except:
        return [float(i)/255 for i in struct.unpack('BBBB', bytes.fromhex(hexstr))]