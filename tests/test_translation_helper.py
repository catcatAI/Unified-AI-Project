import os
import subprocess
import shutil
import pytest
from click.testing import CliRunner
from scripts import translation_helper # Assuming scripts module can be imported

# Define a temporary directory for test artifacts
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_translation_data')
TEST_LOCALES_DIR = os.path.join(TEST_DATA_DIR, 'locales')
TEST_SRC_DIR = os.path.join(TEST_DATA_DIR, 'src')
TEST_BABEL_CFG = os.path.join(TEST_DATA_DIR, 'babel.cfg')
TEST_POT_FILE = os.path.join(TEST_LOCALES_DIR, 'messages.pot')


@pytest.fixture(scope="module")
def setup_test_environment():
    """Set up a temporary environment for testing translation tools."""
    # Clean up before starting, if anything from previous run
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)

    os.makedirs(TEST_LOCALES_DIR, exist_ok=True)
    os.makedirs(os.path.join(TEST_LOCALES_DIR, 'en', 'LC_MESSAGES'), exist_ok=True)
    os.makedirs(os.path.join(TEST_LOCALES_DIR, 'de', 'LC_MESSAGES'), exist_ok=True) # Using 'de' for a distinct test lang
    os.makedirs(TEST_SRC_DIR, exist_ok=True)

    # Create a dummy babel.cfg
    with open(TEST_BABEL_CFG, 'w') as f:
        f.write("[python: src/**.py]\n")
        f.write("encoding = utf-8\n")
        f.write("[extractors]\n") # Ensure extractors section exists if needed by other parts of babel
        f.write("python = babel.messages.extract:extract_python\n")


    # Create a dummy Python file with translatable strings
    with open(os.path.join(TEST_SRC_DIR, 'dummy_module.py'), 'w') as f:
        f.write("import gettext\n")
        f.write("_ = gettext.gettext\n")
        f.write("print(_('Hello Test'))\n")
        f.write("print(_('Another string for testing'))\n")

    # Override paths in translation_helper for testing
    original_base_dir = translation_helper.BASE_DIR
    original_locales_dir = translation_helper.LOCALES_DIR
    original_pot_file = translation_helper.POT_FILE
    original_babel_cfg = translation_helper.BABEL_CFG
    original_langs = translation_helper.LANGUAGES

    translation_helper.BASE_DIR = TEST_DATA_DIR
    translation_helper.LOCALES_DIR = TEST_LOCALES_DIR
    translation_helper.POT_FILE = TEST_POT_FILE
    translation_helper.BABEL_CFG = TEST_BABEL_CFG
    translation_helper.LANGUAGES = ['en', 'de']


    yield

    # Teardown: remove the temporary directory
    shutil.rmtree(TEST_DATA_DIR)

    # Restore original paths
    translation_helper.BASE_DIR = original_base_dir
    translation_helper.LOCALES_DIR = original_locales_dir
    translation_helper.POT_FILE = original_pot_file
    translation_helper.BABEL_CFG = original_babel_cfg
    translation_helper.LANGUAGES = original_langs


def test_extract_py(setup_test_environment):
    """Test the extract-py command."""
    runner = CliRunner()
    # Pointing '.' to TEST_DATA_DIR for pybabel extract context
    # The actual source files are in TEST_DATA_DIR/src/ as per babel.cfg

    # Modify babel.cfg in translation_helper to use relative path for this test context
    # This is tricky because pybabel is run with cwd=TEST_DATA_DIR
    # The babel.cfg inside TEST_DATA_DIR should refer to 'src/**.py' relative to TEST_DATA_DIR

    # The script itself changes its internal BASE_DIR to TEST_DATA_DIR.
    # The pybabel extract command is run with cwd=TEST_DATA_DIR.
    # The babel.cfg is at TEST_DATA_DIR/babel.cfg
    # The source is at TEST_DATA_DIR/src/dummy_module.py
    # The pybabel command in extract_py uses '.' as the input directory for scanning.
    # So, when cwd is TEST_DATA_DIR, '.' means TEST_DATA_DIR.
    # Babel will look for 'src/**.py' starting from TEST_DATA_DIR, which is correct.

    result = runner.invoke(translation_helper.cli, ['extract-py'])
    print(f"extract-py output: {result.output}")
    print(f"extract-py exception: {result.exception}")
    assert result.exit_code == 0
    assert os.path.exists(TEST_POT_FILE)
    with open(TEST_POT_FILE, 'r') as f:
        content = f.read()
        assert "Hello Test" in content
        assert "Another string for testing" in content

def test_update_po(setup_test_environment):
    """Test the update command."""
    runner = CliRunner()
    # First, ensure .pot exists by running extract-py
    result_extract = runner.invoke(translation_helper.cli, ['extract-py'])
    assert result_extract.exit_code == 0
    assert os.path.exists(TEST_POT_FILE)

    result_update = runner.invoke(translation_helper.cli, ['update'])
    print(f"update output: {result_update.output}")
    print(f"update exception: {result_update.exception}")
    assert result_update.exit_code == 0

    for lang in ['en', 'de']:
        po_file = os.path.join(TEST_LOCALES_DIR, lang, 'LC_MESSAGES', 'messages.po')
        assert os.path.exists(po_file)
        with open(po_file, 'r') as f:
            content = f.read()
            assert "Hello Test" in content # Check if new strings are added
            if lang == 'de': # Check header for language
                 assert 'Language: de' in content


def test_compile_langs(setup_test_environment):
    """Test the compile-langs command."""
    runner = CliRunner()
    # Ensure .po files exist and have some content
    result_extract = runner.invoke(translation_helper.cli, ['extract-py'])
    assert result_extract.exit_code == 0
    result_update = runner.invoke(translation_helper.cli, ['update'])
    assert result_update.exit_code == 0

    # Manually add a dummy translation to one .po file to ensure compilation does something
    de_po_file = os.path.join(TEST_LOCALES_DIR, 'de', 'LC_MESSAGES', 'messages.po')
    with open(de_po_file, 'r') as f:
        de_content = f.read()

    # Add a dummy translation
    # A bit fragile if the exact string format from babel changes, but good for a basic test
    if 'msgid "Hello Test"\nmsgstr ""' in de_content:
        de_content = de_content.replace('msgid "Hello Test"\nmsgstr ""', 'msgid "Hello Test"\nmsgstr "Hallo Test"')
        with open(de_po_file, 'w') as f:
            f.write(de_content)
    else:
        print("Warning: Could not find 'msgid \"Hello Test\"\\nmsgstr \"\"' in de.po for dummy translation.")


    result_compile = runner.invoke(translation_helper.cli, ['compile-langs'])
    print(f"compile-langs output: {result_compile.output}")
    print(f"compile-langs exception: {result_compile.exception}")
    assert result_compile.exit_code == 0

    for lang in ['en', 'de']:
        mo_file = os.path.join(TEST_LOCALES_DIR, lang, 'LC_MESSAGES', 'messages.mo')
        assert os.path.exists(mo_file)
        assert os.path.getsize(mo_file) > 0 # .mo files should not be empty

# Placeholder for extract_md tests - would require more setup (dummy md files, actual md parsing)
# def test_extract_md(setup_test_environment):
#     runner = CliRunner()
#     result = runner.invoke(translation_helper.cli, ['extract-md'])
#     assert result.exit_code == 0
#     assert "Markdown extraction logic needs to be implemented." in result.output
