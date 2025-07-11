import os
import click
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALES_DIR = os.path.join(BASE_DIR, 'locales')
POT_FILE = os.path.join(LOCALES_DIR, 'messages.pot')
BABEL_CFG = os.path.join(BASE_DIR, 'babel.cfg')
LANGUAGES = ['en', 'ja', 'zh']

@click.group()
def cli():
    """A helper script for managing translations."""
    pass

@cli.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def extract_py(verbose):
    """Extracts translatable strings from Python files."""
    click.echo("Extracting strings from Python files...")
    cmd = [
        'pybabel', 'extract',
        '-F', BABEL_CFG,
        '-o', POT_FILE,
        '--project=Unified-AI-Project', # Add project name
        '--version=0.1', # Add version
        '--copyright-holder="Unified-AI-Project Contributors"', # Add copyright
        '--msgid-bugs-address=maintainer@example.com', # Add bug address
        '.'
    ]
    if verbose:
        click.echo(f"Running command: {' '.join(cmd)}")

    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=BASE_DIR)
        if verbose and process.stdout:
            click.echo(process.stdout)
        if process.stderr: # pybabel extract often outputs to stderr even on success
            click.echo(process.stderr)
        click.echo(f"Strings extracted to {POT_FILE}")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error during Python string extraction: {e}", err=True)
        click.echo(f"Stdout: {e.stdout}", err=True)
        click.echo(f"Stderr: {e.stderr}", err=True)
    except FileNotFoundError:
        click.echo("Error: pybabel command not found. Make sure Babel is installed and in your PATH.", err=True)


@cli.command()
@click.option('--md_dir', default=os.path.join(BASE_DIR, 'docs'), help="Directory containing Markdown files.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def extract_md(md_dir, verbose):
    """Extracts translatable strings from Markdown files (Placeholder)."""
    click.echo("Extracting strings from Markdown files (Placeholder)...")
    click.echo(f"Would scan: {md_dir}")
    # This is a placeholder. Actual Markdown extraction logic will be complex.
    # It would involve:
    # 1. Walking through md_dir.
    # 2. Reading each .md file.
    # 3. Parsing Markdown to extract text content (e.g., paragraphs, headers).
    #    - Could use a library like `markdown` or `mistune`.
    #    - Need to decide what elements to extract (e.g., ignore code blocks, frontmatter).
    # 4. Appending these strings to a temporary .pot file or directly to the main .pot file.
    #    If appending, care must be taken not to duplicate Python strings.
    #    A common strategy is to extract MD strings to a separate pot, then merge.
    # For now, we'll just acknowledge it.
    click.echo("Markdown extraction logic needs to be implemented.")
    click.echo(f"For now, ensure your POT file ({POT_FILE}) is up-to-date using extract_py, then run update.")

@cli.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def update(verbose):
    """Updates .po files from the .pot template file."""
    click.echo("Updating .po files...")
    if not os.path.exists(POT_FILE):
        click.echo(f"Error: POT file {POT_FILE} not found. Run extract first.", err=True)
        return

    for lang in LANGUAGES:
        po_file = os.path.join(LOCALES_DIR, lang, 'LC_MESSAGES', 'messages.po')
        cmd = [
            'pybabel', 'update',
            '-i', POT_FILE,
            '-d', LOCALES_DIR,
            '-l', lang
        ]
        if os.path.exists(po_file):
            click.echo(f"Updating {po_file} for language '{lang}'...")
        else:
            # This case should ideally be handled by 'pybabel init' first.
            # 'update' typically updates existing files.
            # If a .po file doesn't exist, 'update' might create it or error depending on the version/setup.
            # For robustness, we could call 'init' if 'update' fails for a new language,
            # but the plan already has an 'init' step.
            click.echo(f"Warning: {po_file} does not exist. 'update' might create it or you may need to run 'init' for new languages.", err=True)
            # Try to initialize if it doesn't exist, as update might not create it.
            init_cmd = [
                'pybabel', 'init',
                '-i', POT_FILE,
                '-d', LOCALES_DIR,
                '-l', lang
            ]
            click.echo(f"Attempting to initialize {po_file} for language '{lang}'...")
            try:
                process = subprocess.run(init_cmd, capture_output=True, text=True, check=True, cwd=BASE_DIR)
                if verbose and process.stdout:
                    click.echo(process.stdout)
                if process.stderr:
                    click.echo(process.stderr) # pybabel init often outputs to stderr
            except subprocess.CalledProcessError as e:
                click.echo(f"Error initializing {lang}.po: {e}", err=True)
                click.echo(f"Stdout: {e.stdout}", err=True)
                click.echo(f"Stderr: {e.stderr}", err=True)
                continue # Skip to next language if init fails
            except FileNotFoundError:
                click.echo("Error: pybabel command not found.", err=True)
                return


        if verbose:
            click.echo(f"Running command: {' '.join(cmd)}")
        try:
            process = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=BASE_DIR)
            if verbose and process.stdout:
                click.echo(process.stdout)
            if process.stderr: # pybabel update often outputs to stderr
                 click.echo(process.stderr)
            click.echo(f".po file for language '{lang}' updated.")
        except subprocess.CalledProcessError as e:
            click.echo(f"Error updating {lang}.po: {e}", err=True)
            click.echo(f"Stdout: {e.stdout}", err=True)
            click.echo(f"Stderr: {e.stderr}", err=True)
        except FileNotFoundError:
            click.echo("Error: pybabel command not found.", err=True)
            return


@cli.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def compile_langs(verbose): # Renamed to avoid conflict with built-in compile
    """Compiles .po files to .mo files."""
    click.echo("Compiling .po files to .mo files...")
    cmd = [
        'pybabel', 'compile',
        '-d', LOCALES_DIR,
        '--statistics' # Add statistics
    ]
    if verbose:
        click.echo(f"Running command: {' '.join(cmd)}")

    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=BASE_DIR)
        if verbose and process.stdout:
            click.echo(process.stdout)
        # compile command often outputs to stderr for stats
        if process.stderr:
             click.echo(process.stderr)
        click.echo("Compilation complete.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error during compilation: {e}", err=True)
        click.echo(f"Stdout: {e.stdout}", err=True)
        click.echo(f"Stderr: {e.stderr}", err=True)
    except FileNotFoundError:
        click.echo("Error: pybabel command not found.", err=True)

if __name__ == '__main__':
    cli()
