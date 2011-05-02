import subprocess, os

def match_file_mimetype(real_filepath, mimetype):
    if os.path.islink(real_filepath):
        real_filepath = os.readlink(real_filepath)
    p = subprocess.Popen("file -ib %s" %(real_filepath), shell=True, stdout=subprocess.PIPE)
    output_file = p.stdout
    output_str = output_file.read()
    if mimetype in output_str:
        return True
    else:
        return False

def get_file_mimetype(real_filepath):
    if os.path.islink(real_filepath):
        real_filepath = os.readlink(real_filepath)
    p = subprocess.Popen("file -ib %s" %(real_filepath), shell=True, stdout=subprocess.PIPE)
    output_file = p.stdout
    output_str = output_file.read()
    output_str = output_str.strip('\n').strip().split(';')[0]
    return output_str
