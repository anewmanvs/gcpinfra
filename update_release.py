"""
Finds and uploads version to affect the whole repo.

Alex Newman - 19/02/2020

Prints cant only be used when a sys.exit(1) is called (meaning it failed).
The only exception to this rule is the new version print at the end of the file
to output the new version to be used.
"""

import sys
from re import compile
from operator import add

setupfilename = 'setup.py'

params = sys.argv[1:]
tam = len(params) 
if tam < 1 or tam > 2:
    print("Supported args are 'major', 'minor' or 'patch'. Choose ONE.")
    print("Usage ex: python update_release.py patch")
    sys.exit(1)

skip_questions = False
if tam == 2:
    if params[1] not in ['-y', '--yes']:
        print("The only supported option is '-y' or '--yes' to activate "
              "the 'no questions asked' mode")
        sys.exit(1)
    skip_questions = True

param = params[0]
suppargs = ['major', 'minor', 'patch']
if param not in suppargs:
    print("Well... I guess I don't know what to do with '{}'".format(param))
    print("Could you please provide a supported arg, like 'major', 'minor' or"
          " 'patch'?")
    sys.exit(1)

if not skip_questions:
    try:
        answer = input("This will update the release version and upload to PyPi.\n"
                       "That means that 'setup.py' file will be changed\nIt's a "
                       "path with no return, kid. Tell me, are you positive? "
                       "[yes/no]: ")
    except KeyboardInterrupt:
        print('\nI will take that as a no')
        answer = 'no'

    means_yes = ['yes', 'y', 'yep', 'yeah', 'sim', 's', 'ja', 'da', 'si',
                 'hell yeah']

    if answer.lower() not in means_yes:
        print('Aborting')
        sys.exit(1)

with open(setupfilename, 'r') as _f:
    content = _f.read()

pttn = compile(r'version\s*=\s*\'((?:[0-9]+\.?)+)\'')
version = pttn.findall(content)[0]

# find new version
updtmask = map(lambda x: int(x == param), suppargs)
lnversion = list(map(add, map(int, version.split('.')), updtmask))
nversion = '{}.{}.{}'.format(*lnversion)

# writing new setup.py
with open(setupfilename, 'w') as _f:
    _f.write(pttn.sub("version='{}'".format(nversion), content))

print(nversion)
sys.exit(0)
