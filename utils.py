import hashlib
import zlib
import base64
import json
import urllib.request as urllib2


def serialize_sub(encoded_data, output_file_path):
    decoded_data = base64.b64decode(encoded_data)
    decompressed_data = zlib.decompress(decoded_data, 16 + zlib.MAX_WBITS)
    with open(output_file_path, "wb") as f:
        f.write(decompressed_data)


def get_md5(file_path):
    return hashlib.md5(open(file_path, 'rb').read()).hexdigest()  # memory inefficient, but ok for small files, like srt


def download_file_from_url(url, file_path):
    u = urllib2.urlopen(url)

    with open(file_path, 'wb') as f:
        meta = u.info()
        meta_func = meta.getheaders if hasattr(meta, 'getheaders') else meta.get_all
        meta_length = meta_func("Content-Length")
        file_size = None
        if meta_length:
            file_size = int(meta_length[0])
        print("Downloading: {0} Bytes: {1}".format(url, file_size))

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(buffer)
            f.write(buffer)

            status = "{0:16}".format(file_size_dl)
            if file_size:
                status += "   [{0:6.2f}%]".format(file_size_dl * 100 / file_size)
            status += chr(13)
            print(status, end="")
        print()

    return file_path


def pretty_format(data):
    return json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))