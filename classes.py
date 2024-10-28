class F_File:
    def __init__(self, name:str ,new_filepath:str, old_filepath:str ,diff:str, added:int,current_lines:int, deleted:int):
        self.name = name
        self.new_filepath = new_filepath
        self.old_filepath = old_filepath
        self.diff = diff
        self.added_lines = added
        self.deleted_lines = deleted
        self.nloc = current_lines
        self.commit_count = 0
        self.pkg_name = None

    def __eq__(self, other) -> bool:
        return isinstance(other, F_File) and self.name == other.name
    
    def add_comm(self, count: int):
        self.commit_count += count 

    def add_package(self, pkg_name):
        self.pkg_name = pkg_name

    def __hash__(self) -> int:
        return hash(self.name)
    
    def to_dict(self):
        return {
            'filename': self.name,
            'old_path': self.old_filepath,
            'new_path': self.new_filepath,
            'added_lines': self.added_lines,
            'deleted_lines': self.deleted_lines,
            'diff_text': self.diff
        }
    
    def add_date(self, date):
        self.creation_date = date
        self.current_date = date
    
    def update_date(self, date):
        self.current_date = date

class F_Commit:
    def __init__ (self, hash:str, msg:str, date, author:str, commiter:str, lines:int, number_files:int, is_refactor:bool = False, previous_hash:str = None):
        self.hash = hash
        self.msg = msg
        self.date = date
        self.author = author
        self.commiter = commiter
        self.total_lines = lines
        self.total_files = number_files
        self.previous_hash = previous_hash
        self.is_refactor:bool = is_refactor
        self.files = []


    def __eq__(self, other) -> bool:
        return isinstance(other, F_Commit) and self.hash == other.hash
    
    def __hash__(self) -> int:
        return hash(self.hash)
    
    def add_Files(self, files):
        self.files = sorted(files, key=lambda f: f.name.lower())
        
    def to_dict(self):
        return {
            'current_hash':self.hash,
            'previous_hash': self.previous_hash,
            'msg':self.msg,
            'diff_stats': [f.to_dict() for f in self.files]
        }

class General_Metric:
    def __init__(self) -> None:
        self.nadev = 0
        self.ammount_adevs = set()

        self.nddev = 0
        self.ammount_ddevs = set()

        self.ncomm = 0
        self.exp = 0

        self.nf = 0
        self.la = 0
        self.ld = 0

        self.cexp = 0
        self.rexp = 0
        self.nd = 0

        self.fix = False

        self.ns = 0


    def to_dict(self):
        return{
            'NADEV': self.nadev,
            'NDDEV': self.nddev,
            'NCOMM': self.ncomm,
            'EXP': self.exp,
            'ND': self.nd,
            'NS': self.ns,
            'NF' :self.nf,
            'FIX': self.fix,
            'CEXP': self.cexp,
            'REXP': self.rexp
        }

class File_Metric:
    #Add metrics one by one
    def __init__(self, name:str, old_path: str, new_path:str, pkg_name:str):
        self.name = name
        self.old_path = old_path
        self.new_path = new_path
        self.pkg_name = pkg_name
        
        self.comm_count = 0

        self.ammount_ddevs = set()
        self.ammount_adevs = set()
        self.adev_count = 0
        self.ddev_count = 0

        self.added_lines = 0
        self.deleted_lines = 0
        self.add = 0
        self.deleted = 0

        self.total_lines = 0
        self.all_devs_commits = {}
        self.all_devs_lines = {}
        self.high_contributer :str = ''

        self.own = 0
        self.minor = 0

        self.oexp = 0
        self.la = 0
        self.ld = 0

        self.ndev = 0
        self.nuc = 0

        self.lt = 0

        self.dates = []
        self.days = []
        self.age = 0

        self.sexp = 0
        self.entropy = 0

    def get_minor(self):
        total_lines = sum(self.all_devs_commits.values())
        self.minor = sum(1 for lines in self.all_devs_commits.values() if lines / total_lines < 0.05)

    def add_adev(self, name: str):
        self.ammount_adevs.add(name)
        self.adev_count = len(self.ammount_adevs)
        

    def add_ddev(self, name: str):
        self.ammount_ddevs.add(name)
        self.ddev_count = len(self.ammount_ddevs)
        if name in self.all_devs_commits:
            self.all_devs_commits[name] += 1 
        else:
            self.all_devs_commits[name] = 1
        self.high_contributer, _ = max(self.all_devs_commits.items(), key=lambda x: x[1])
        self.ndev = self.adev_count
            
    def calc_lines(self, add:int, del_lines:int, author:str):
        self.la = add
        self.ld = del_lines
        self.added_lines += add
        self.deleted_lines += del_lines
        if self.added_lines > 0:
            self.add = round(add / self.added_lines, 2)
        if self.deleted_lines > 0:
            self.deleted = round(del_lines / self.deleted_lines, 2)
        
        self.total_lines += add + del_lines

        self.all_devs_lines[author] = self.all_devs_lines.get(author, 0) + add + del_lines

        if self.total_lines > 0:
            self.own = round(self.all_devs_lines[self.high_contributer] / self.total_lines, 2)

    def increase_comm(self):
        self.comm_count += 1

    def to_dict(self):
        return{
            'new_path': self.new_path,
            'old_path': self.old_path,
            'filename': self.name,
            'COMM': self.comm_count, # Does not count current commit
            'ADEV': self.adev_count, # Does not count current commit
            'DDEV': self.ddev_count, # Does count current commit
            'ADD': self.add, # Does count current commit
            'DEL': self.deleted, # Does count current commit
            'OWN': self.own, # Does count current commit
            'MINOR': self.minor, # Does count current commit
            'OEXP': self.oexp,
            'ENTROPY': self.entropy,
            'LA': self.la,
            'LD': self.ld,
            'NDEV': self.ndev,
            'NUC': self.nuc,
            'LT': self.lt,
            'AGE': self.age,
            'SEXP': self.sexp
        }

class Commit_Metric:
    def __init__(self, hash, date, msg):
        self.commit_hash = hash
        self.date = date
        self.msg = msg
        self.file_metrics = []
        self.general_metric = General_Metric()
    
    def add_metrics(self, file_metrics):
        self.file_metrics= [f.to_dict() for f in file_metrics]

    def to_dict(self):
        return {
            'refactor_hash': self.commit_hash,
            'file_metrics': self.file_metrics,
            'general_metrics': self.general_metric
        }

    def __eq__(self, other) -> bool:
        return isinstance(other, Commit_Metric) and self.commit_hash == other.commit_hash
    
    def __hash__(self) -> int:
        return hash(self.commit_hash)
