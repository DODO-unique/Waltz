'''
docstring for logger.py
This is a shared instance. One for each run. Good luck.
'''

from pathlib import Path
from datetime import datetime


# log file path (absolute because of resolve)

def create_file(date: str, time:str) -> str:
    path = Path(__file__).resolve().parent.parent / "logs" / date 
    path.mkdir(parents=True, exist_ok=True)
    return str(path / f"{time}.log")

class Logger:
    '''
    Docstring for Logger
    This is a shared instance. One for each run. Good luck.
    '''
    def __init__(self):
        try: 
            self.now = datetime.now().isoformat()
            self.date = datetime.now().strftime(r"%Y-%m-%d")
            self.time = datetime.now().strftime("%H-%M-%S")
            with open(create_file(self.date, self.time), 'x') as logs:
                logs.write(f'{self.now} -> Created logs\n')

        except FileExistsError:
            # noisy but would help when debugging for the grand flow:
            self.entry("control", "Attempted adding a new log file. Caught under explicit file creation")
        

    def entry(self, local: str, log: str) -> None:
        
        # open the file
        with open(create_file(self.date, self.time), 'a') as logs:
            logs.write(f'{local} at {datetime.now().isoformat()} :\n')
            logs.write(f'\t{log}\n')

# This instance is shared, so all the files can add their logs.
Hebu = Logger()



# ------------ This entire section is subject to revision during documentation ----------


# suggestion, try storing it as logs when importing elsewhere. Like `logs = Hebu.entry`, then going logs("Heyo!"). Wait, let me add that here itself:
'''logs = Hebu.entry'''
# now, simply `from main import logs` or better:
def loggy(local: str, log: str) -> None:
    Hebu.entry(local=local, log=log)
# same thing, but no one dies during debugging.


# this is mandatory for every file to define before using the logger, for example
# def _log(log:str) -> None:
#     loggy("control", log)


# ------------------ The section ends here ------------------