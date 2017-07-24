import ast
import getopt
import re
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def print_usage():
    print('usage: python inc_uwp_build_num.py ')
    print('         -c <commit> -f <manifest file> -p <product> -s <server>')

try:
    parsed_args = getopt.getopt(sys.argv[1:], 'c:f:p:s:')
except getopt.GetoptError as e:
    print('error: ' + e.msg)
    print_usage()
    sys.exit(1)

commit = ''
filename = ''
product = ''
server = ''
for opt, optarg in parsed_args[0]:
    if opt == '-c': commit = optarg
    elif opt == '-f': filename = optarg
    elif opt == '-p': product = optarg
    elif opt == '-s': server = optarg

if not server:
    print('error: missing required server parameter')
    sys.exit(1)

if not filename:
    print('error: missing required file parameter')
    sys.exit(1)

try:
    infile = open(filename)
except:
    print('error opening file for read: {0}'.format(filename))
    print(sys.exc_info()[0])
    sys.exit(1)

manifest_content = infile.read()
infile.close()

file_parts = re.match(r'(.*)(Version="\d+\.\d+\.\d+\.\d+")(.*)',
    manifest_content, re.MULTILINE | re.DOTALL)
if not file_parts:
    print('error: could not find the version string')
    sys.exit(1)

version_tag = file_parts.group(2)

version_parts = re.match(r'Version="(\d+\.\d+\.\d+)\.\d+"', version_tag)
version_num = version_parts.group(1)

if server[-1] == '/':
    server = server[0:-1]
url = server + '/cmd/next_build_num'

post_fields = {'product': product, 'version': version_num, 'commit': commit}
request = Request(url, urlencode(post_fields).encode())
result = urlopen(request).read().decode()

try:
    # Use literal_eval() for safety since we're eval'ing untrusted code.
    result = ast.literal_eval(result)
except SyntaxError as e:
    err = "syntax error at line {0}, offset {1}: '{2}'".format(
        e.lineno, e.offset, e.text.rstrip())
    sys.exit(1)
except ValueError:
    err = 'illegal value used. (Is the resulting text not a pure literal?)'
    sys.exit(1)
except:
    err = 'unknown parse error'
    sys.exit(1)

server_err = result.get('error')
if server_err:
    print('error getting next version num: {0}'.format(server_err))
    sys.exit(1)

next_build_num = result.get('next_build_num')
if not next_build_num:
    print('error getting next version num: no next build num provided')
    sys.exit(1)

new_version = '{0}.{1}'.format(version_num, next_build_num)
new_version_tag = 'Version="{0}"'.format(new_version)

new_file = file_parts.group(1) + new_version_tag + file_parts.group(3)

try:
    outfile = open(filename, 'w')
except:
    print('error opening file for write: {0}'.format(filename))
    print(sys.exc_info()[0])
    sys.exit(1)

outfile.write(new_file)
outfile.close()

print('Updated file "{0}" with version "{1}"'.format(filename, new_version))
