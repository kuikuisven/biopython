# Copyright 2010 by Tiago Antao.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

"""
This class provides code to parse BIG GenePop files.

The difference between this class and the standard Bio.PopGen.GenePop.Record
class is that this one does not read the whole file to memory.
It provides an iterator interface, slower but consuming much mess memory.
Should be used with big files (Thousands of markers and individuals).

See http://wbiomed.curtin.edu.au/genepop/ , the format is documented
here: http://wbiomed.curtin.edu.au/genepop/help_input.html .

Classes:
FileRecord           Holds GenePop data.

Functions:


"""
from copy import deepcopy
from Bio.PopGen.GenePop import get_indiv

def read(fname):
    """Parses a file containing a GenePop file.

       fname is a file name that contains a GenePop record.
    """
    record = FileRecord(fname)
    return record


class FileRecord:
    """Holds information from a GenePop record.

    Members:
    marker_len         The marker length (2 or 3 digit code per allele).    
    
    comment_line       Comment line.

    loci_list          List of loci names.

    Functions:
    get_individual     Returns the next individual of the current population.

    skip_population    Skips the current population.
    
    skip_population skips the individuals of the current population, returns
    True if there are more populations.

    get_individual returns an individual of the current population (or None
    if the list ended).
    Each individual is a pair composed by individual
    name and a list of alleles (2 per marker or 1 for haploid data).
    Examples
            ('Ind1', [(1,2),    (3,3), (200,201)]
            ('Ind2', [(2,None), (3,3), (None,None)]
            ('Other1', [(1,1),  (4,3), (200,200)]

    
    """
    def __init__(self, fname):
        self.comment_line    = ""
        self.loci_list       = []
        self.fname           = fname
        self.start_read()

    def __str__(self):
        """Returns (reconstructs) a GenePop textual representation.

           This might take a lot of memory.
           Marker length will be 3.
        """
        marker_len = 3
        rep  = [self.comment_line + '\n']
        rep.append('\n'.join(self.loci_list) + '\n')
        current_pop = self.current_pop
        current_ind = self.current_ind
        self._handle.close()
        self._handle = open(self.fname)
        self.skip_header()
        rep.append('Pop\n')
        more = True
        while more:
            res = self.get_individual()
            if res == True:
                rep.append('Pop\n')
            elif res == False:
                more = False
            else:
                name, markers = res
                rep.append(name)
                rep.append(',')
                for marker in markers:
                    rep.append(' ')
                    for al in marker:
                        if al == None:
                            al = '0'
                        aStr = str(al)
                        while len(aStr)<marker_len:
                            aStr = "".join(['0', aStr])
                        rep.append(aStr)
                rep.append('\n')
        self.seek_position(current_pop, current_ind)
        return "".join(rep)


    def start_read(self):
        """Starts parsing a file containing a GenePop file.
        """
        self._handle = open(self.fname)
        self.comment_line = self._handle.next().rstrip()
        #We can now have one loci per line or all loci in a single line
        #separated by either space or comma+space...
        #We will remove all commas on loci... that should not be a problem
        sample_loci_line = self._handle.next().rstrip().replace(',', '')
        all_loci = sample_loci_line.split(' ')
        self.loci_list.extend(all_loci)
        for line in self._handle:
            line = line.rstrip()
            if line.upper()=='POP':
                break
            self.loci_list.append(line)
        else:
            raise ValueError('No population data found, file probably not GenePop related')
        #self._after_pop = True
        self.current_pop = 0
        self.current_ind = 0

    def skip_header(self):
        """Skips the Header. To be done after a re-open."""
        self.current_pop = 0
        self.current_ind = 0
        for line in self._handle:
            if line.rstrip().upper()=="POP":
                return

    def seek_position(self, pop, indiv):
        """Seeks a certain position in the file.

           pop   - pop position (0 is first)
           indiv - individual in pop
        """
        self._handle.close()
        self._handle = open(self.fname)
        self.skip_header()
        while pop>0:
            self.skip_population()
            pop -= 1
        while indiv>0:
            self.get_individual()
            indiv -= 1

    def skip_population(self):
        "Skips the current population. Returns true if there is another pop."
        for line in self._handle:
            if line=="":
                return False
            line = line.rstrip()
            if line.upper()=='POP':
                self.current_pop += 1
                self.current_ind = 0
                return True

    def get_individual(self):
        """Gets the next individual.

           Returns individual information if there are more individuals
           in the current population.
           Returns True if there are no more individuals in the current
           population, but there are more populations. Next read will
           be of the following pop.
           Returns False if at end of file.
        """
        marker_len = None
        for line in self._handle:
            line = line.rstrip()
            if line.upper()=='POP':
                self.current_pop += 1
                self.current_ind = 0
                return True
            else:
                self.current_ind += 1
                indiv_name, allele_list, ignore = get_indiv(line)
                return (indiv_name, allele_list)
        return False

    def remove_population(self, pos):
        """Removes a population (by position).

           pos - position
           fw  - A file handle (write enabled) to write the new record
        """
        del self.populations[pos]
    
    def remove_locus_by_position(self, pos, fw):
        """Removes a locus by position.

           pos - position
           fw  - A file handle (write enabled) to write the new record
        """
        del self.loci_list[pos]
        for pop in self.populations:
            for indiv in pop:
                name, loci = indiv
                del loci[pos]

    def remove_locus_by_name(self, name, fw):
        """Removes a locus by name.

           name - name
           fw   - A file handle (write enabled) to write the new record
        """
        for i in range(len(self.loci_list)):
            if self.loci_list[i] == name:
                self.remove_locus_by_position(i, fw)
                return
        #If here than locus not existent... Maybe raise exception?
        #   Although it should be Ok... Just a boolean return, maybe?
    

