with open('apps/backend/src/hsp/types.py', 'rb') as f:
    data = f.read()
    print('Length:', len(data))
    print('Null bytes:', data.count(0))
    print('Last 100 bytes:', repr(data[-100:]))