import codecs
import xml.etree.ElementTree as ET
import zlib

def escape_for_xml(instring: str):
    """Escape characters that may appear in .fms strings but are illegal in xml.

    (&, <, >, \", \', \\n)
    """
    instring = instring.replace("&", "&amp;")
    instring = instring.replace("<", "&lt;")
    instring = instring.replace(">", "&gt;")
    instring = instring.replace("\"", "&quot;")
    instring = instring.replace("'", "&apos;")
    instring = instring.replace("\n", "&#xA;")
    return instring

    
def unescape_from_xml(instring: str):
    """Unescape characters that were previously escaped for xml.

    (&amp; &lt; &gt; &quot; &apos; &#xA;)
    """
    instring = instring.replace("&amp;", "&")
    instring = instring.replace("&lt;", "<")
    instring = instring.replace("&gt;", ">")
    instring = instring.replace("&quot;", "\"")
    instring = instring.replace("&apos;", "'")
    instring = instring.replace("&#xA;", "\n")
    return instring


def crc32(filename, chunksize=65536):
    """Compute the CRC-32 checksum of the contents of the given filename"""
    with open(filename, "rb") as f:
        checksum = 0
        while (chunk := f.read(chunksize)) :
            checksum = zlib.crc32(chunk, checksum)
        return checksum


class FMS:
    """Python object for representing a Criware .fms file, with methods for reading/writing as .fms and .xml"""

    def __init__(self):
        """Initialize the python FMS object."""
        self.filesize = 0
        self.headermagicword = 0
        self.datasize = 0
        self.headersize = 0
        self.unknown1 = 0
        self.unknown2 = 0
        self.stringcount = 0
        self.unknown3 = 0
        self.unknown4 = 0
        self.prop1list = []
        self.prop2list = []
        self.stringdata = []
        self.footermagicword = 0
        self.unknown5 = 0
        self.footersize = 0
        self.unknown6 = 0
        self.validflag = False
        self.zerocounts = []
        self.skips = []

        
    def read_fms(self, infilename):
        """Parse and read a .fms file, saving its content within the python FMS object."""
        
        with open(infilename, "rb") as infile:
            
            # figure out the file size
            infile.seek(0, 2)
            self.filesize = infile.tell()
            infile.seek(0, 0)
            
            # check header magic word FMSB
            self.headermagicword = infile.read(4)
            assert self.headermagicword == b"\x46\x4D\x53\x42", "Magic word not found in header. Not a FMS file."

            # read data size
            self.datasize = int.from_bytes(infile.read(4), "little", signed=False)
            assert (self.filesize - 48) == self.datasize, "File size does not match data size reported in header. Bad file."
            
            # read header size
            self.headersize = int.from_bytes(infile.read(4), "little", signed=False)
            assert self.headersize == 32, "Header size is not 32. I don't know how to parse this. Maybe bad file."
            
            # read unknown 1
            self.unknown1 = int.from_bytes(infile.read(4), "little", signed=False)
            if self.unknown1 != 0:
                print("Unknown1 is", unknown1, "but 0 was expected.")
                
            # read unknown 2
            self.unknown2 = int.from_bytes(infile.read(4), "little", signed=False)
            if self.unknown2 != 0:
                print("Unknown2 is", unknown2, "but 0 was expected.")
                
            # read string count
            self.stringcount = int.from_bytes(infile.read(4), "little", signed=False)
            
            # read unknown 3
            self.unknown3 = int.from_bytes(infile.read(4), "little", signed=False)
            if self.unknown3 != 3:
                print("Unknown3 is", unknown3, "but 3 was expected.")
                
            # read unknown 4
            self.unknown4 = int.from_bytes(infile.read(4), "little", signed=False)
            if self.unknown4 != 0:
                print("Unknown4 is", unknown4, "but 0 was expected.")
                
            # we've now read all 32 bytes of the header
            
            # read the string properties (well, I assume they're some kind of string properties, but I don't have any non-zero examples)
            for i in range(self.stringcount):
                self.prop1list.append(int.from_bytes(infile.read(4), "little", signed=False))
                if self.prop1list[i] != 0:
                    print("Prop1 for string", i, "is", self.prop1list[i], "but 0 was expected.")
                self.prop2list.append(int.from_bytes(infile.read(4), "little", signed=False))
                if self.prop2list[i] != 0:
                    print("Prop2 for string", i, "is", self.prop2list[i], "but 0 was expected.")
                    
            # now read the strings themselves
            stringsread = 0
            bytesread = (8 * self.stringcount)
            tempbuffer = []
            while (stringsread < self.stringcount) and (bytesread < self.datasize):
                somebyte = infile.read(1)
                bytesread += 1
                tempbuffer.append(somebyte)
                if int.from_bytes(somebyte, "little", signed=False) == 0:
                    self.stringdata.append(tempbuffer.copy())
                    tempbuffer.clear()
                    stringsread += 1
            
            # now let's sanity check
            # (python doesn't seem have an easy way to print variables in assertion messages...)
            if self.stringcount != stringsread:
                print("Expected", self.stringcount, "strings, but read", stringsread)
            assert self.stringcount == stringsread, "Did not read expected number of strings."
            
            # read the padding at the end of the data section
            expectedpadding = 0
            currentposition = infile.tell()
            overage = currentposition % 16
            if overage:
                expectedpadding = 16 - overage
            if expectedpadding:
                for i in range(expectedpadding):
                    somebyte = infile.read(1)
                    assert int.from_bytes(somebyte, "little", signed=False) == 0, "Found non-zero byte in expected padding"
                    bytesread += 1
            # (python doesn't seem have an easy way to print variables in assertion messages...)
            if bytesread != self.datasize:
                print("expected", self.datasize , "bytes, but read", bytesread, "bytes")
            assert bytesread == self.datasize, "Did not read expected number of bytes."
            
            # read the footer magic word FEOC
            self.footermagicword = infile.read(4)
            assert self.footermagicword == b"\x46\x45\x4F\x43", "Footer magic word not found where expected."
            
            # read unknown 5
            self.unknown5 = int.from_bytes(infile.read(4), "little", signed=False)
            if self.unknown5 != 0:
                print("Unknown5 is", unknown5, "but 0 was expected.")
            
            # read footer size
            self.footersize = int.from_bytes(infile.read(4), "little", signed=False)
            assert self.footersize == 16, "Footer size is not 16. I don't know how to parse this. Maybe bad file."
            
            # read unknown 6
            self.unknown6 = int.from_bytes(infile.read(4), "little", signed=False)
            if self.unknown6 != 0:
                print("Unknown6 is", unknown6, "but 0 was expected.")
            
            # sanity check that were are at end of file
            assert infile.tell() == self.filesize, "End of file not where expected."
            
            # flag that we've read data in with no errors
            self.validflag = True
            
        #print("Success!")

    def check_empty_strings(self):
        """Iterates through a python FMS object and flags instances of multiple empty strings in a row."""
        
        assert self.validflag, "This object has not been initialized with valid data."
        
        countingstate = False
        firstindex = -1
        emptycount = 0
        emptysample = []
        emptysample.append((0).to_bytes(1, byteorder="little", signed=False))
        for i in range(self.stringcount):
            self.zerocounts.append(0)
            if self.stringdata[i] == emptysample:
                emptycount += 1
                if not countingstate:
                    countingstate = True
                    firstindex = i
                    self.skips.append(False)
                else:
                    self.skips.append(True)
            else:
                self.skips.append(False)
                if countingstate:
                    #print(f"Found series of {emptycount} empty strings starting at index {firstindex}")
                    countingstate = False
                    self.zerocounts[firstindex] = emptycount
                    firstindex = -1
                    emptycount = 0
        #if we got to the end during a series of empty strings, note the count
        if countingstate:
            self.zerocounts[firstindex] = emptycount
                    
        

    def screen_blarf(self):
        """Print the values saved in the python FMS object to the screen."""
        
        assert self.validflag, "This object has not been initialized with valid data."
        print("Header magic word:", self.headermagicword)
        print("Data section size:", self.datasize)
        print("Header size:", self.headersize)
        print("Unknown1 (expect 0): ", self.unknown1)
        print("Unknown2 (expect 0): ", self.unknown2)
        print("String count:", self.stringcount)
        print("Unknown3 (expect 0): ", self.unknown3)
        print("Unknown4 (expect 0): ", self.unknown4)
        print("Footer magic word:", self.footermagicword)
        print("Unknown5 (expect 0): ", self.unknown5)
        print("Footer size:", self.footersize)
        print("Unknown6 (expect 0): ", self.unknown6)
        for i in range(self.stringcount):
            print("String index:", i)
            print("Props1 (expect 0):", self.prop1list[i])
            print("Props2 (expect 0):", self.prop2list[i])
            print("String:", b"".join(self.stringdata[i]).decode("utf-8"))

            
    def write_fms(self, outfilename):
        """Write a .fms file using the values saved in the python FMS object."""
        
        assert self.validflag, "This object has not been initialized with valid data."
        
        with open(outfilename, "wb") as outfile:
            
            # write the header
            outfile.write(self.headermagicword)
            #we will fill in the datasize later
            outfile.write((0).to_bytes(4, byteorder="little", signed=False))
            outfile.write(self.headersize.to_bytes(4, byteorder="little", signed=False))
            outfile.write(self.unknown1.to_bytes(4, byteorder="little", signed=False))
            outfile.write(self.unknown2.to_bytes(4, byteorder="little", signed=False))
            outfile.write(self.stringcount.to_bytes(4, byteorder="little", signed=False))
            outfile.write(self.unknown3.to_bytes(4, byteorder="little", signed=False))
            outfile.write(self.unknown4.to_bytes(4, byteorder="little", signed=False))
            
            # write the string properties (well, I assume they're some kind of string properties, but I don't have any non-zero examples)
            for i in range(self.stringcount):
                outfile.write(self.prop1list[i].to_bytes(4, byteorder="little", signed=False))
                outfile.write(self.prop2list[i].to_bytes(4, byteorder="little", signed=False))
            
            # write the strings themselves
            for i in range(self.stringcount):
                for somebyte in self.stringdata[i]:
                    outfile.write(somebyte)
                
            # figure out how much padding is needed
            neededpadding = 0
            currentposition = outfile.tell()
            overage = currentposition % 16
            if overage:
                neededpadding = 16 - overage
            if neededpadding:
                for i in range(neededpadding):
                    outfile.write((0).to_bytes(1, byteorder="little", signed=False))
                    
            # write the footer
            outfile.write(self.footermagicword)
            outfile.write(self.unknown5.to_bytes(4, byteorder="little", signed=False))
            outfile.write(self.footersize.to_bytes(4, byteorder="little", signed=False))
            outfile.write(self.unknown6.to_bytes(4, byteorder="little", signed=False))
            
            # compute the data size
            newdatasize = outfile.tell() - 48
            outfile.seek(4, 0)
            outfile.write(newdatasize.to_bytes(4, byteorder="little", signed=False))
            
        #print("Success!")


    def write_xml(self, outfilename):
        """Write an .xml file using the values saved in the python FMS object."""
        
        assert self.validflag, "This object has not been initialized with valid data."
        
        self.check_empty_strings()
        
        with open(outfilename, "w", encoding="utf-8", newline="\u000A") as outfile:
            
            # write a prologue
            outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            
            # python's parser gets pissy if we don't have a single root
            outfile.write("<fms>\n")
            
            # write the metadata
            outfile.write("    <metadata>\n")
            outfile.write("".join(["        <headermagicword>", str(self.headermagicword, "utf-8"), "</headermagicword>\n"]))
            outfile.write(f"        <datasize>{self.datasize}</datasize>\n")
            outfile.write(f"        <headersize>{self.headersize}</headersize>\n")
            outfile.write(f"        <unknown1>{self.unknown1}</unknown1>\n")
            outfile.write(f"        <unknown2>{self.unknown2}</unknown2>\n")
            outfile.write(f"        <stringcount>{self.stringcount}</stringcount>\n")
            outfile.write(f"        <unknown3>{self.unknown3}</unknown3>\n")
            outfile.write(f"        <unknown4>{self.unknown4}</unknown4>\n")
            outfile.write("".join(["        <footermagicword>", str(self.footermagicword, "utf-8"), "</footermagicword>\n"]))
            outfile.write(f"        <unknown5>{self.unknown5}</unknown5>\n")
            outfile.write(f"        <footersize>{self.footersize}</footersize>\n")
            outfile.write(f"        <unknown6>{self.unknown6}</unknown6>\n")
            outfile.write("    </metadata>\n")
            
            #write the strings
            outfile.write("    <stringlist>\n")
            for i in range(self.stringcount):
                if not self.skips[i]:
                    outfile.write("        <stringdata>\n")
                    outfile.write(f"            <index>{i}</index>\n")
                    outfile.write(f"            <props1>{self.prop1list[i]}</props1>\n")
                    outfile.write(f"            <props2>{self.prop2list[i]}</props2>\n")
                    # trim the null terminator since xml is allergic to them
                    if int.from_bytes(self.stringdata[i][-1], "little", signed=False) == 0:
                        workingstring = b"".join(self.stringdata[i][:-1]).decode("utf-8")
                    else:
                        workingstring = b"".join(self.stringdata[i]).decode("utf-8")
                    workingstring = escape_for_xml(workingstring);
                    outfile.write("".join(["            <text>", workingstring, "</text>\n"]))
                    if self.zerocounts[i] > 1:
                        outfile.write(f"            <nullrepeatcount>{self.zerocounts[i]}</nullrepeatcount>\n")
                    outfile.write("        </stringdata>\n")
            outfile.write("    </stringlist>\n")

            outfile.write("</fms>")


    def read_xml(self, infilename):
        """Parse and read an .xml file with a particular structure, saving its content within the python FMS object."""
        
        xmltree = ET.parse(infilename)
        if xmltree is None:
            raise Exception("Total xml parse fail. No tree.")
        
        xmlroot = xmltree.getroot()
        if xmlroot is None:
            raise Exception("Total xml parse fail. No root.")
        
        # get the header/footer data
        xmlmeta = xmlroot.find("metadata")
        if xmlmeta is None:
            raise Exception("XML parse fail. No <metadata>.")
        
        # expecting a bytes object for magic words, and int for everything else
        
        someelement = xmlmeta.find("headermagicword")
        if someelement is not None:
            self.headermagicword = someelement.text.encode("utf-8")
            assert self.headermagicword == b"\x46\x4D\x53\x42", "Bad header magic word. Must be FMSB"
        else:
            # default to the only value observed in samples
            self.headermagicword = b"\x46\x4D\x53\x42"
        
        # skip datasize since we're going to recompute it anyway
        
        someelement = xmlmeta.find("headersize")
        if someelement is not None:
            self.headersize = int(someelement.text)
            assert self.headersize == 32, "Header size is not 32. The only header I know how to write is 32 bytes."
        else:
            # default to the only value observed in samples
            self.headersize = 32
        
        someelement = xmlmeta.find("unknown1")
        if someelement is not None:
            self.unknown1 = int(someelement.text)
        else:
            # default to the only value observed in samples
            self.unknown1 = 0
        
        someelement = xmlmeta.find("unknown2")
        if someelement is not None:
            self.unknown2 = int(someelement.text)
        else:
            # default to the only value observed in samples
            self.unknown2 = 0
        
        mustcountstrings = True
        someelement = xmlmeta.find("stringcount")
        if someelement is not None:
            self.stringcount = int(someelement.text)
            assert self.stringcount > 0, "<stringcount> is zero. Can't produce a valid file with no strings..."
            mustcountstrings = False
        else:
            # we will count the strings that we read
            mustcountstrings = True
            print("<stringcount> not found. Strings will be counted as they are read in.")
        
        someelement = xmlmeta.find("unknown3")
        if someelement is not None:
            self.unknown3 = int(someelement.text)
        else:
            # default to the only value observed in samples (unknown3 is 3; the other unknowns are 0)
            self.unknown3 = 3
        
        someelement = xmlmeta.find("unknown4")
        if someelement is not None:
            self.unknown4 = int(someelement.text)
        else:
            # default to the only value observed in samples
            self.unknown4 = 0
        
        someelement = xmlmeta.find("footermagicword")
        if someelement is not None:
            self.footermagicword = someelement.text.encode("utf-8")
            assert self.footermagicword == b"\x46\x45\x4F\x43", "Bad footer magic word. Must be FEOC"
        else:
            # default to the only value observed in samples
            self.footermagicword = b"\x46\x45\x4F\x43"
        
        someelement = xmlmeta.find("unknown5")
        if someelement is not None:
            self.unknown5 = int(someelement.text)
        else:
            # default to the only value observed in samples
            self.unknown5 = 0
        
        someelement = xmlmeta.find("footersize")
        if someelement is not None:
            self.footersize = int(someelement.text)
            assert self.footersize == 16, "Footer size is not 16. The only footer I know how to write is 16 bytes."
        else:
            # default to the only value observed in samples
            self.footersize = 16 
            
        someelement = xmlmeta.find("unknown6")
        if someelement is not None:
            self.unknown6 = int(someelement.text)
        else:
            # default to the only value observed in samples
            self.unknown6 = 0
        
        # now lets try to read the string data itself
        xmlstringlist = xmlroot.find("stringlist")
        if xmlstringlist is None:
            raise Exception("XML parse fail. No <stringlist>.")
        
        stringsread = 0
        for thisstring in xmlstringlist.findall("stringdata"):
            
            thisindex = "[missing]"
            someelement = thisstring.find("index")
            if someelement is not None:
                thisindex = someelement.text
            
            someelement = thisstring.find("props1")
            if someelement is not None:
                self.prop1list.append(int(someelement.text))
            else:
                print(f"Missing <props1> at <stringdata> entry {stringsread} (index: {thisindex}). Assuming 0.")
                self.prop1list.append(0)
                
            someelement = thisstring.find("props2")
            if someelement is not None:
                self.prop2list.append(int(someelement.text))
            else:
                print(f"Missing <props2> at <stringdata> entry {stringsread} (index: {thisindex}). Assuming 0.")
                self.prop2list.append(0)
            
            someelement = thisstring.find("text")
            if someelement is not None:
                stringtext = someelement.text
                # we might have an empty string, so we just need a list containing the null terminator
                if stringtext is None:
                    tempbuffer = []
                    tempbuffer.append((0).to_bytes(1, byteorder="little", signed=False))
                    self.stringdata.append(tempbuffer.copy())
                else:
                    stringtext = unescape_from_xml(stringtext)
                    # OK, python kinda sucks with hiding the data types making it very hard to get back to a list of byte objects 
                    bytetext = stringtext.encode("utf-8")
                    bytelist = [bytes([b]) for b in bytetext]
                    # add the null terminator
                    bytelist.append((0).to_bytes(1, byteorder="little", signed=False))
                    self.stringdata.append(bytelist.copy())
            else:
                print(f"Missing <text> at <stringdata> entry {stringsread} (index: {thisindex}). Assuming empty string, but your input and output files are probably garbage. ")
                tempbuffer = []
                tempbuffer.append((0).to_bytes(1, byteorder="little", signed=False))
                self.stringdata.append(tempbuffer.copy())
            
            stringsread += 1
            
            someelement = thisstring.find("nullrepeatcount")
            if someelement is not None:
                repeatcount = int(someelement.text)
                if repeatcount > 1:
                    #subtract 1 since we already pushed the entry for this string
                    for i in range(repeatcount - 1):
                        self.prop1list.append(0)
                        self.prop2list.append(0)
                        tempbuffer = []
                        tempbuffer.append((0).to_bytes(1, byteorder="little", signed=False))
                        self.stringdata.append(tempbuffer.copy())
                        stringsread += 1
            
        # double check the string count
        if mustcountstrings:
            self.stringcount = stringsread
        else:
            if self.stringcount != stringsread:
                print(f"String count mismatch! {self.stringcount} strings declared in <stringcount>, but {stringsread} strings found in xml file. Setting stringcount to {stringsread}, but your input and output files are probably garbage.")
                self.stringcount = stringsread

        # flag that we've read data in with no errors
        self.validflag = True

    
def fms_to_xml(infilename, outfilename):
    """Convert a .fms file to an .xml file."""
        
    someFMS = FMS()
    someFMS.read_fms(infilename)
    someFMS.write_xml(outfilename)
    
    
def xml_to_fms(infilename, outfilename):
    """Convert an .xml file with a particular structure to a .fms file."""
        
    someFMS = FMS()
    someFMS.read_xml(infilename)
    someFMS.write_fms(outfilename)

def fms_to_xml_roundtrip_test(infilename, xmloutfilename, fmsoutfilename):
    """Convert .fms to .xml to .fms again, then check if the output's checksum matches the original file"""
    
    someFMS = FMS()
    someFMS.read_fms(infilename)
    someFMS.write_xml(xmloutfilename)
    anotherFMS = FMS()
    anotherFMS.read_xml(xmloutfilename)
    anotherFMS.write_fms(fmsoutfilename)
    originalchecksum = crc32(infilename)
    newchecksum = crc32(fmsoutfilename)
    if originalchecksum == newchecksum:
        print("Roundtrip successful! The checksums match! (Both:", originalchecksum, ")")
    else:
        print("Failure! Checksums do not match! Original:", originalchecksum, "Output file:", newchecksum)
