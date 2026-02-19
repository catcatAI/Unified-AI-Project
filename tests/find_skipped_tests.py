import glob
import logging
logger = logging.getLogger(__name__)

skipped_files = []
for file in glob.glob('**/*.py', recursive=True):
    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        if '@pytest.mark.skip' in content or '@unittest.skip' in content:
            skipped_files.append(file)

if skipped_files:
    print('\n'.join(skipped_files))
else:
    print('No skipped tests found')