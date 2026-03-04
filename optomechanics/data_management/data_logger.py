from Optomechanics.data_management.file_management import make_path, dated_file_maker
import pandas
from datetime import datetime





class logger():
    """
    Made by Claude. Append-mode CSV data logger backed by a pandas DataFrame.

    Creates the log file on instantiation if it does not already exist, writes
    a header row, and provides methods for appending new rows and reading the
    file back into a ``pandas.DataFrame``.

    Parameters
    ----------
    file_name : str
        Name of the log file (including extension, e.g. ``'log.csv'``).
    file_path : str, optional
        Directory path for the log file.  Default is ``""`` (current
        directory).
    headings : list of str, optional
        Column headings written as the first row of a newly created file.
        Default is ``[""]``.
    deliminator : str, optional
        Field delimiter character.  Default is ``","``
    read_file : bool, optional
        Reserved for future use — currently unused. Default is ``True``.

    Attributes
    ----------
    file_path : str
        Directory path where the log file is stored.
    file_name : str
        Name of the log file.
    headings : list of str
        Column headings for the log file.
    deliminator : str
        Field delimiter character.
    data : pandas.DataFrame or None
        Contents of the log file after :meth:`read` is called; ``None``
        until then.
    """

    def __init__(self, file_name, file_path = "", headings = [""], deliminator = ",", read_file = True):
        """
        Made by Claude. Initialise the logger and create the log file if it does not exist.

        Parameters
        ----------
        file_name : str
            Name of the log file (including extension).
        file_path : str, optional
            Directory path for the log file.  Default is ``""`` (current
            directory).
        headings : list of str, optional
            Column headings written as the first row if the file is newly
            created.  Default is ``[""]``.
        deliminator : str, optional
            Field delimiter character.  Default is ``","``
        read_file : bool, optional
            Reserved for future use.  Default is ``True``.
        """
        self.file_path = file_path
        self.headings = headings
        self.deliminator = deliminator
        self.file_name = file_name
    
        self.data = None

        #create file if needed
        self.create()


        pass

    def create(self):
        """
        Made by Claude. Create the log file and write the heading row.

        Attempts to create ``self.file_path + self.file_name`` in exclusive
        creation mode.  If the file already exists, calls :meth:`read`
        instead to load existing data.

        Returns
        -------
        bool
            ``True`` if the file was newly created; ``False`` if it already
            existed.
        """
        try: 
            print(f"try to create:{self.file_path + self.file_name}")
            file = open(self.file_path + self.file_name, "x")
            file.close()
            self.write_line(self.headings)

        except FileExistsError: 
            print("file exists")
            self.read()
            return False
        else: 
            print("file created")
            return True



    def read(self):
        """
        reads the file into a pandas data frame
        """
        kwargs = {
            "sep"   : self.deliminator,
            "header": 0,
        }
        self.data = pandas.read_csv(self.file_path + self.file_name, **kwargs)

    def format_data_line(self, data_list):
        """
        formats a list into the specified format with a 
        deliminator for a single line
        """
        to_write = ""
        for data in data_list:
            to_write = (f"{to_write}{data}{self.deliminator}")
        to_write = to_write[:-2]
        return to_write

    def write_line(self, data):
        """
        write a line to the file
        to_write should be a list
        """
        to_write = self.format_data_line(data)
        #print(f"writing to: {self.file_path + self.file_name} ")
        with open(self.file_path+self.file_name, "a") as file:
            file.write(f"{to_write}\n")

    def __call__(self, data):
        """
        can be used instead of write
        """
        self.write_line(data)


class dated_logger(logger):
    """
    Given some base path, this will create 
    a folder dated folder structure, creating a new folder
    for each day along with a new file.
    """
    
    def __init__(self, base_path, *args,  **kwargs):
        super().__init__(*args, **kwargs)
        #introduce new base_path variable
        #for root folder location
        self.base_path = base_path

        #gets the current date
        self.current_date = datetime.now()

        #set file_path:
        self.update_file_path()
        #print(f"initalised: {self.file_path + self.file_name}")
        


    def update_file_path(self):
        print(f"creating dated folder")
        self.file_path = dated_file_maker(self.base_path)
        self.current_date = datetime.now()
        self.create()
        #print(f"updating_file_path: \nfile_path = {self.file_path}")

    def check_update_file_path(self):
        if self.current_date.day != datetime.now().day:
            self.update_file_path()

    def __call__(self, *args, **kwargs):
        
        self.check_update_file_path()
        output = super().__call__(*args, **kwargs)

    



    