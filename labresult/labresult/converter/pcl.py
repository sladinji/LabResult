import subprocess
from labresult.lib.model import get_option

class ConverterException(Exception):
    pass

def fix_fr_accent(asciiText):
    """ Fix french accent. """
    pcl_char_convertion = {
        '@': 'à',
        '[': '°',
        '\\': 'ç',
        ']': '§',
        '{': 'é',
        '|': 'ù',
         '}': 'è',
        '\x7e': '\xa8',
        '\xe9': 'é',
        '\xc2\xb0': '°',
        '\x82': 'é',
    }
    for char, repl in pcl_char_convertion.items():
        asciiText = asciiText.replace(char, repl)
    return asciiText

def topdf(data):
    """
    :param data: pcl data (str)
    :rtype: pdf data (str)
    """
    option = ''
    try :
        option = get_option("pcl_conversion", '-J"@PJL SET PAPER=A4"',
        'Ajustement pour la conversion PDF')
    except :
        pass
    if not data :
        raise ConverterException("data = None")
    cmd = 'timeout 10 pcl6 -dNOPAUSE -dBATCH -sDEVICE=pdfwrite %s '\
          '-sOutputFile=- -' % option
    proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE )
    pdf, _ = proc.communicate(data)
    if proc.returncode == 124:
        raise ConverterException("PCL6 TIMEOUT")
    elif proc.returncode != 0:
        raise ConverterException("PCL6 ERROR :\n * code :{code}\n * option ="
                " {option}\n * command = {command}".format(code=proc.returncode,
                    command=cmd, option=option)
              )
    return pdf
