"""
This module was made to index tokens.
It consists of two classes: class Position and class ToIndex.
"""
from tokenization import ToTokenize
from tokenization import TokenWithType
import shelve
import os

class Position:
    """
    The class is needed to define the start and the end of a token being indexed.
    """
    
    def __init__(self, start, end):
        """
        The method is needed to create positions of tokens --
        objects that have two attributes:
        @param: the start of the token
        @param: the end of the token
        """
        self.start = start
        self.end = end
        
    def __repr__(self):
        """
        This method creates a string representation of a position.
        """
        return str(self.start) + ', ' + str(self.end)

    def __eq__(self, obj):
        """
        This method is needed to compare the objects of class Position
        """
        return self.start == obj.start and self.end == obj.end

class PositionByLine:
    
    def __init__(self, start, end, line):
        """
        The method is needed to create positions of tokens --
        objects that have two attributes:
        @param: 'self.start' - the start of the token
        @param: 'self.end' - the end of the token
        @param: 'self.line' - the number of the line
        """
        self.start = start
        self.end = end
        self.line = line

    def __repr__(self):
        """
        This method creates a string representation of a position.
        """
        return "(" + str(self.start) + ', ' + str(self.end) + ', ' + str(self.line) + ")"

    def __eq__(self, obj):
        """
        This method is needed to compare the objects of class Position.
        """
        return self.start == obj.start and self.end == obj.end and self.line == obj.line

    def __lt__(self, obj):
        """
        We need this method to sort objects of class PositionByLine.
        """
        less = False
        if self.line < obj.line:
            less = True
        if self.line == obj.line:
            if self.start < obj.line:
                less = True
        return less
        
    

class ToIndex:
    """
    The class is needed to index a file. 
    """
    def __init__(self, db_name):
        """
        In this method we create a database where indexed tokens
        are going to be stored.
        """
        self.db = shelve.open(db_name, writeback=True)

    def __del__(self):
        """
        In this method we close the database.
        """
        self.db.close()
               
    def index(self, file_name):
        """
        This method gets indexes for the tokens in a file.
        @param: the name of the file
        """

        # Raise TypeError if the input type is not string      
        if not isinstance(file_name, str):
            raise(TypeError)
        # Raise ValuError if filename doesn't exist.
        files = os.listdir()
        if file_name not in files:
            raise(ValueError)
        # Create an object of ToTokenize.
        tokenizer = ToTokenize()
        # Open file
        text_file = open(file_name, 'r')
        # Read file and save as a string
        text_string = text_file.read()
        # Close the file.
        text_file.close()
        # Tokenize the string and write resulting tokens (only alphabetical
        # and digital ones) to the list 'tokens'
        tokens = tokenizer.tokenize_reduced(text_string)
        
        
        for token in tokens:
            # For each token in the list create an object of Position.
            position = Position(token.start, token.start + len(token.wordform))
            # Use method '.setdefault()' to write the token, its file_name
            # and position to the database.
            self.db.setdefault(token.wordform, {}).setdefault(file_name, []).append(position)
            
        # Use '.sync()' to save the database.
        self.db.sync()

    def index_by_line(self, file_name):
        """
        This method index a file by strings.
        param@: the name of the file
        """

        # Raise TypeError if the input type is not string      
        if not isinstance(file_name, str):
            raise(TypeError)
        
        # Raise ValuError if filename doesn't exist.
        files = os.listdir()
        if file_name not in files:
            raise(ValueError)

        
        # Create an object of ToTokenize.
        tokenizer = ToTokenize()
        # Open file
        text_file = open(file_name, 'r')
        # Read the file by line
        for num, string in enumerate(text_file):
            #Tokenize each string of the file and 
            # save resulting tokens to the list 'tokens'
            tokens = tokenizer.tokenize_reduced(string)
        
        
            for token in tokens:
                # For each token in the list create an object of Position.
                position = PositionByLine(token.start, token.start + len(token.wordform), num)
            
                # Use method '.setdefault()' to write the token, its file_name
                # and position to the database.
                self.db.setdefault(token.wordform, {}).setdefault(file_name, []).append(position)
                
        # Close the file.
        text_file.close()
        # Use '.sync()' to save the database.
        self.db.sync()
        
        



                
                    
if __name__ == '__main__':
    a = ToIndex('database')
    a.index_by_line("tolstoy1.txt")
    #a.index_by_line("tolstoy2.txt")
    #a.index_by_line("tolstoy3.txt")
    #a.index_by_line("tolstoy4.txt")
    
    db= shelve.open('database')
    print(db['Анна'])
    #a.index("text.txt")
    #a.index("text2.txt")
