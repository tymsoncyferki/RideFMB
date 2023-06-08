import subprocess


def run_commands():
    # Run 'update' command
    subprocess.run(['python', 'manage.py', 'update'], check=True)

    # Run 'collectstatic' command and confirm automatically
    subprocess.run(['python', 'manage.py', 'collectstatic', '--noinput'], check=True, input=b'yes\n')


if __name__ == '__main__':
    run_commands()
