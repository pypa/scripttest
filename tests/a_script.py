import sys


def main(args):
    if args == ['error']:
        sys.stderr.write('stderr output\n')
        return
    if args[:1] == ['exit']:
        sys.exit(int(args[1]))
    if args == ['stdin']:
        print(sys.stdin.read().upper())
        return
    for arg in args:
        print('Writing %s' % arg)
        open(arg, 'w').write('test')


if __name__ == '__main__':
    main(sys.argv[1:])
