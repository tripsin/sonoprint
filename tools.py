import socket


def try_port(port):
    """ Return True if *port* free """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = False
    try:
        sock.bind(("0.0.0.0", port))
        result = True
    except Exception as e:
        print('Port {} is busy.'.format(port))
        print(e)
    finally:
        sock.close()
    return result
