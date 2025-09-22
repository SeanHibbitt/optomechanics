from .file_management import make_path, dated_file_maker
import pandas
from datetime import datetime





class logger():
    """
    Aim:
    Neatly made class to log data to a specified file in 
    a specified format and also to retrieve data
    in a specified format.
    Uses pandas
    """

    def __init__(self, file_name, file_path = "", headings = [""], deliminator = ",", read_file = True):
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
        creates file in specified location
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

    



    