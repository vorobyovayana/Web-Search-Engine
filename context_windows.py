import shelve
import os
import re
from indexation import PositionByLine
from tokenization import ToTokenize
from tokenization import TokenWithType
from search_engine import SearchEngine

class ContextWindow:
    '''
    This class creates a context window.
    '''

    def __init__(self, position, left_cont, right_cont, line):        
        """
        Create an object of ContextWindow class. Attributes
        self.start_pattern and self.end_pattern are needed to find 
        the end and the beginning of the sentence in which a context window is situated.        
        @param 'position':  a position of the word in question;
        @param 'left_cont': the left context of the word in question;
        @param 'right_cont': the right context of the word in question;
        @param 'line': a line in which the word in question is present.
        """
        self.line = line
        self.position = position
        self.left_cont = left_cont
        self.right_cont = right_cont
        self.end_pattern = re.compile(r'[.?!]\s[A-ZА-Я]?')
        self.start_pattern = re.compile(r'[A-ZА-Я]*[.?!]')
        
    def __eq__(self, obj):
        """
        This method is needed to compare the objects of class ContextWindow.
        """
        return (self.position == obj.position and self.left_cont == obj.left_cont
                and self.line == obj.line and self.right_cont == obj.right_cont)
    
    def __repr__(self):
        """
        This method creates a string representation of a ContextWindow.
        """
        return '(' + str(self.position) + ','+ str(self.left_cont) + ',' \
               + str(self.right_cont) + ',' + self.line + ')'
    
    def make_bold(self):
        '''
        This method makes inquired words bold.
        '''
        # A slice that is equal to the context window.
        result_line = self.line[self.left_cont:self.right_cont]
        # We make words bold by adding html tags starting from the end of the line.
        # To do that we reverse the position of a word of the query
        # so that the enlargement of the line doesn't change the positions of the words in question.
        for pos in reversed(self.position):
            # This is the beginning of the word in question.
            start = pos.start - self.left_cont
            # This is the end of the word in question.
            end = pos.end - self.left_cont
            # Change the last part of the slice.
            result_line = result_line[:end] + '</b>' + result_line[end:]
            # Change the first part of the slice.
            result_line = result_line[:start] + '<b>' + result_line[start:]
            self.line = result_line
        return result_line
    
    def extend_to_sentence(self):
        '''
        This method extends a context window to the boundaries
        of a sentence it is situated in.
        '''
        # For convenienve write substrings on the left and on the right
        # of the window into single variables.
        left_substr = self.line[:self.left_cont + 1]
        right_substr = self.line[self.right_cont:]         
        # Search a substring that matches our pattern on
        # 'left_substr' and 'right_substr'.
        # For convenience write the result to variables
        # 'start' and 'end'.
        start = re.search(self.start_pattern, left_substr)
        end = re.search(self.end_pattern, right_substr)
        # If there is a substring that matches our 'end_pattern'
        # than we move the position of the right context to the
        # first character of this substring.
        if end is not None: 
            self.right_cont = self.right_cont + end.start()
        # Otherwise we move the position of the right context to the
        # end of the line in which the context window is situated.
        else:
            self.right_cont = len(self.line)
        # If there is a substring that matches our 'start_pattern'
        # than we move the position of the left context to the
        # first character of this substring.
        if start is not None:
            self.left_cont = self.left_cont - start.start()
        # Otherwise we move the position of the left context to the
        # start of the line in which the context window is situated.
        else:
            self.left_cont = 0
            
            
class Contexter:
    '''
    This class creates an object that provides a context window.
    '''        
    def get_one_cw(self, window_size, file_path, p):        
        '''
        This method creates a context window for a one-word query.
        param@ 'window_size': window size.
        param@ 'file_path': a path to the file.
        param@ 'p': position of the word in question.
        return@: a context window.
        '''
        if not isinstance(window_size, int):
            raise TypeError        
        if not isinstance(file_path, str):
            raise TypeError        
        if not isinstance(p, PositionByLine):
            raise TypeError        
        # Create an empty list and append position of the word into it
        # because later we will need to extend this list when we will
        # unite windows.
        position =[]
        position.append(p)
        # Create an object of ToTokenize().
        tokenizer = ToTokenize()
        # Open a given file.
        file = open(file_path, 'r')
        # For convenience write position in these variables.
        st = p.start
        end = p.end
        line_num = p.line        
        # In the file find a line in which the word of the query is,
        # and write it to 'line'.
        for i, line in enumerate(file):
            if i == line_num:
                break
        file.close()
        # Write a tokenized substring into the variable 'right_tokens'
        right_tokens = list(tokenizer.tokenize_reduced(line[st:]))
        
        # If the window_size is bigger than the right substring,
        # than reduce the window size to the length of the substring.
        if window_size > len(right_tokens)-1:
            window_size = len(right_tokens)        
        # For each token in enumerated 'right_tokens'.
        for i, token in enumerate(right_tokens):            
            if i == window_size:
                break           
        # Write end.
        right_border =  st + token.start + len(token.wordform)      
        # This is a left substring. We write it to 'left_sub_line'
        # for our convenience.
        left_tokens = list(tokenizer.tokenize_reduced(line[:end]))
        if window_size > len(left_tokens):
                window_size = len(left_tokens) 
        # Tokenize the left sub line in reversed order until it is
        # bigger than a context size and write the index
        # of the end of the last one in 'left_border'.
        for i, token in enumerate(left_tokens[::-1]):
            if i == window_size:
                break
        left_border = token.start              
        cw = ContextWindow(position, left_border, right_border, line)
        return cw

    def get_several_cws(self, search_results, window_size): 
        '''
        This method gets context windows for each position in a given dictionary.
        @param 'search_results': results of the search.
        @param 'window_size': a size of the future windows.
        @return: a dictionary of united context windows.
        '''
        if search_results == {}:
            return{}
        if not isinstance(search_results, dict):
            raise TypeError
        if not isinstance(window_size, int):
            raise TypeError
        # Create an empty dictionary that we will fill in later.
        # Its keys will be file names and values -- list of the context windows.
        cws = {}
        for file_name in search_results:
            # Create an empty list for context_windows.
            cws[file_name] = []            
            # For each position get a context window.
            for position in search_results[file_name]:
                cw = self.get_one_cw(window_size, file_name, position)
                cws[file_name].append(cw)                
        return cws

    
    def check_intersection(self, cw_1, cw_2):
        '''
        This method checks if two windows are intersected.
        @param 'cw_1': the first window.
        @param 'cw_2': the second window.
        @return: a boolean variable that is 'True' if the windows are intersected.
        '''
        intersection = False
        # If the left context of the window is bigger than that of
        # the another one,
        # and the line of the window is same as that of
        # the another one, then the windows are intersected.
        if(cw_1.right_cont > cw_2.left_cont and cw_1.line == cw_2.line):
            intersection = True            
        return intersection     

    def unite_windows(self, cw_1, cw_2):  
        '''
        This method unites two intersected windows.
        @param 'cw_1': the first window.
        @param 'cw_2': the second window.
        @return: a united window
        '''        
        # Add the position of the second window to that of the
        # first one.
        cw_1.position.extend(cw_2.position)
        # Write right context of the second window tothat of the
        # first one.
        cw_1.right_cont = cw_2.right_cont
        return cw_1

    def unite_cws(self, cws):
        '''
        This method unites intersected context windows.
        @param 'cws': a dictionary of context windows.
        @return: a list of context windows with united intersections.
        '''        
                    
        # This is a counter to allow us perform iterations.
        i = 0
        # For our convenience write a list of context windows
        # in 'array_windows'
        array_windows = cws

        while i < len(cws) - 1:
            #print(array_windows[i])
            # If context windows are intersected, unite them.                
            if self.check_intersection(array_windows[i], array_windows[i + 1]):                    
                array_windows[i] = self.unite_windows(array_windows[i], array_windows[i + 1])
                # Delete the second window.
                del array_windows[i + 1]
            i += 1           
        return array_windows

    def get_united_cws(self, search_results, window_size):
        '''
        This method provides context windows for a multi-word query
        and unite intersected windows.
        @param 'window_size': window size.
        @param 'search_results': results of the search.
        @return: a dictionary of united context windows.
        '''        
        if search_results == {}:
            return{}
        if not isinstance(search_results, dict):
            raise TypeError
        if not isinstance(window_size, int):
            raise TypeError
        cws = self.get_several_cws(search_results, window_size)
        for file_name in cws:
            cws[file_name] = self.unite_cws(cws[file_name])
        return cws

    def get_extended_cws(self, search_results, window_size):
        '''
        This method gets a context window for each position in search_results
        and extends a context window to the boundaries of a sentence it is situated in.
        @param 'window_size': window size.
        @param 'search_results' : results of the search.
        @return: a dictionary of extended context windows without intersections.
        '''
        if search_results == {}:
            return{}
        if not isinstance(search_results, dict):
            raise TypeError
        if not isinstance(window_size, int):
            raise TypeError
        
        # Get a context window for each word of the query.
        cws = self.get_several_cws(search_results, window_size)
        for file_name in cws:            
            for cw in cws[file_name]:
                # Extend the context to the boundaries of the sentence.
                cw.extend_to_sentence()
                #print(cw)
            # Unite intersected windows.
            cws[file_name] = self.unite_cws(cws[file_name])                
        return cws
         
    def get_bold_cws(self, search_results, window_size):
        '''
        This method creates a context window for a multi-word query
        and makes words of the query bold.
        @param 'search_results': results of the search.
        @param 'window_size': a size of the future windows.
        @return: a dictionary of context windows with bold query words
        and without intersections.
        '''
        if search_results == {}:
            return{}
        if not isinstance(search_results, dict):
            raise TypeError
        if not isinstance(window_size, int):
            raise TypeError
        cws = self.get_united_cws(search_results, window_size)
        for file_name in cws:
            for cw in cws[file_name]:
                cw.make_bold()                
        return cws
    
    def get_several_cws_limited(self, search_results, window_size, doclimit, docoffset): 
        '''
        This method gets context windows for each position in a given dictionary for
        the documents required by a user.
        @param 'search_results': results of the search.
        @param 'window_size': a size of the future windows.
        @param 'doclimit': the limit of documents on the page.
        @param 'docoffset': the number of the first document on the page.
        @return: a dictionary of united context windows within the limit
        established by the user.
        '''
        if search_results == {}:
            return{}
        if not isinstance(search_results, dict):
            raise TypeError
        if not isinstance(window_size, int):
            raise TypeError
        if not isinstance(doclimit, int):
            raise TypeError
        if not isinstance(docoffset, int):
            raise TypeError
        # Create an empty dictionary that we will fill in later.
        # Its keys will be file names and values -- list of the context windows.
        cws = {}
        sorted_file_names = sorted(search_results)
        print(sorted_file_names)
        for i, file_name in enumerate(sorted_file_names):            
            # Exit the cycle if 'i' is out of limit.
            if i >= docoffset + doclimit:
                break
            if i >= docoffset:
                cws[file_name] = []
                # For each position get a context window.
                for position in search_results[file_name]:                    
                    cws[file_name].append(self.get_one_cw(window_size, file_name, position))                
        return cws

    def get_united_cws_limited(self, search_results, window_size, doclimit, docoffset):
        '''
        This method provides context windows for a multi-word query
        and unite intersected windows for the documents required by a user.
        @param 'window_size': window size.
        @param 'search_results': results of the search.
        @param 'doclimit': the limit of documents on the page.
        @param 'docoffset': the number of the first document on the page.
        @return: a dictionary of united context windows
        within the limit established by the user.
        '''        
        if search_results == {}:
            return{}
        if not isinstance(search_results, dict):
            raise TypeError
        if not isinstance(window_size, int):
            raise TypeError
        if not isinstance(doclimit, int):
            raise TypeError
        if not isinstance(docoffset, int):
            raise TypeError
        cws = self.get_several_cws_limited(search_results, window_size, doclimit, docoffset)        
        for file_name in cws:
            print(file_name)
            cws[file_name] = self.unite_cws(cws[file_name])
        return cws


    def get_extended_cws_limited(self, search_results, window_size, doclimit, docoffset):
        '''
        This method gets a context window for each position in the documents
        required by a user and extends a context window to the boundaries
        of a sentence it is situated in.
        @param 'window_size': window size.
        @param 'search_results' : results of the search.
        @param 'doclimit': the limit of documents on the page.
        @param 'docoffset': the number of the first document on the page.
        @return: a dictionary of extended context windows without intersections
        within the limit established
        by the user.
        '''
        if search_results == {}:
            return{}
        if not isinstance(search_results, dict):
            raise TypeError
        if not isinstance(window_size, int):
            raise TypeError
        if not isinstance(doclimit, int):
            raise TypeError
        if not isinstance(docoffset, int):
            raise TypeError
        # Get a context window for each word of the query.
        cws = self.get_several_cws_limited(search_results, window_size, doclimit, docoffset)
        for file_name in cws:            
            for cw in cws[file_name]:
                # Extend the context to the boundaries of the sentence.
                cw.extend_to_sentence()
            # Unite intersected windows.
            cws[file_name] = self.unite_cws(cws[file_name])
        return cws

    def get_bold_cws_limited(self, search_results, window_size, doclimit, docoffset, lim_of_pairs):
        '''
        This method creates multi-query, bold context windows so that they
        conform to a user's limit and offset.
        @param 'search_results': results of the search.
        @param 'window_size': a size of the future windows.
        @param 'doclimit': the limit of documents on the page.
        @param 'docoffset': the number of the first document on the page.
        @param 'lim_of_pairs': the number of the first quote on the page,
        and the number of quotes on the page in general for a certain document.
        @return: a dictionary of multi-query, bold context windows within the limit established
        by the user.
        '''
        if search_results == {}:
            return{}
        if not isinstance(search_results, dict):
            raise TypeError
        if not isinstance(window_size, int):
            raise TypeError
        if not isinstance(doclimit, int):
            raise TypeError
        if not isinstance(docoffset, int):
            raise TypeError
        if not isinstance(lim_of_pairs, list):
            raise TypeError
        for pair in lim_of_pairs:
            if not isinstance(pair, tuple):
                raise TypeError
            for tuple_element in pair:
                if not isinstance(tuple_element, int):
                    raise TypeError
        # Getting united context windows
        cws = self.get_united_cws_limited(search_results, window_size, doclimit, docoffset)
        # Sorting file names in the chronological order.
        sorted_file_names = sorted(cws)
        # Creating an empty dictionary for required quotes only.
        # It is to be returned.
        result = {}
        # Iterating through the file names.
        for i, sorted_fn in enumerate(sorted_file_names):
            # Exit the cycle if 'i' is out of limit.
            if i >= docoffset + doclimit:
                break
            if i >= docoffset:
                # Creating an empty list for required context windows only, belonging
                # to the file at hand.
                result[sorted_fn] = []
                # Iterating through the pairs offsets and limits.
                for lim_of_pair in lim_of_pairs:
                    # Iterating through the context windows belonging to the file at hand.
                    for t, cw in enumerate(cws[sorted_fn]):
                        # Exit the cycle if 't' is out of limit.
                        if t >= lim_of_pair[0] + lim_of_pair[1]:
                            break
                        if t >= lim_of_pair[0]:
                            # Append the bold context window in the resulting list.
                            result[sorted_fn].append(cw.make_bold())               
        return result
if __name__ == '__main__':
    a = SearchEngine('database')
    c = Contexter()
    #print(c.get_one_cw(5, 'tolstoy_reduced.txt', PositionByLine(40, 44, 0)))
    #print(c.get_several_cws_limited(a.multi_search('Анна Павловна'), 1, 2, 0))
    #print(c.get_several_cws(a.multi_search('Анна Павловна'), 3))
    #print(c.get_united_cws_limited(a.multi_search('Анна Павловна'), 1, 1, 0))
    #print(c.get_united_cws(a.multi_search('Анна Павловна'), 1))
    #print(c.get_extended_cws(a.multi_search('Анна Павловна'), 2))
    #print(c.get_extended_cws_limited(a.multi_search('Анна Павловна'), 1, 1, 0))
    #print(c.get_bold_cws(a.multi_search('Анна Павловна'), 3))
    print(c.get_bold_cws_limited(a.limited_multi_search('Анна Павловна'), 1, 4, 0, [(0,1), (0,1), (0,1), (0,1)]))
