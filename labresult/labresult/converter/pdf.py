import subprocess
from labresult.lib.model import get_option

class Pdf2PngException(Exception):
    pass

def toimg(pdf_data, page_num=1, thumbnail=False, frmt='png'):
    """
    Convert doc to img.
    :param pdf_data: bytes
    :param page_num: page number to convert
    :param thumbnail: false generate normal size, true generate thumbnail
    :rtype: bytes
    """
    command = '%s'
    timeout = get_option( 'timeout_pdf2png', 10 )
    if timeout > 0:
        command = 'timeout %d %%s' % timeout

    reso = 15 if thumbnail else 120
    command = command % ('gs -dQUIET -dPARANOIDSAFER -dBATCH -dNOPAUSE -dNOPROMPT -sDEVICE=png16m -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -r%s -dFirstPage=%s -dLastPage=%s -sOutputFile=- -' % (reso, page_num, page_num))

    conv = subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )

    png_data, _ = conv.communicate(pdf_data)
    ret = conv.returncode
    if ret == 124:
        raise Pdf2PngException("TIMEOUT EXPIRED")
    elif ret != 0:
        raise Pdf2PngException("GS RETURN ERROR CODE %s" % ret)
    return png_data
