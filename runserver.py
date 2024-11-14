import subprocess


def run_concurrent_commands(commands):
    processes = []
    for command in commands:
        process = subprocess.Popen(command, shell=True)
        processes.append(process)

    # Wait for all processes to finish
    for process in processes:
        process.wait()


if __name__ == "__main__":
    commands = [
        "pip install -r requirements.txt",
        "python manage.py makemigrations",
        "python manage.py migrate",
        "python manage.py runserver",
        "celery -A blendjoy worker --loglevel=info --pool=eventlet",
    ]
    run_concurrent_commands(commands)
