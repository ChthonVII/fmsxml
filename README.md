# fmsxml
Python scripts for converting Criware .fms files to easily editable xml and back again.

### Dependencies
The only dependencies are standard libraries:
- codecs
- xml.etree.ElementTree
- zlib

This was written using Python 3.11, but it might run on some earlier versions.

### Installation and Usage

**To install:**

First, activate the python virtual enviroment you want to install to, then:

`python setup.py install`

or alternatively

`pip install .`

**To convert .fms to .xml:**
```
from fmsxml import *
fms_to_xml("infile.fms", "outfile.xml")
```

**To convert .xml back to .fms:**
```
from fmsxml import *
xml_to_fms("infile.xml", "outfile.fms")
```

You can also verify that roundtrip conversion of a given .fms file yields output that is bit-for-bit identical with the original:
```
from fmsxml import *
fms_to_xml_roundtrip_test("infile.fms", "outfile1.xml", "outfile2.fms")
```

**To use without installing:**

Copy fmsxml.py to the working directory, then
```
import fmsxml

# to convert .fms to .xml:
fmsxml.fms_to_xml("infile.fms", "outfile.xml")

# to convert .xml back to .fms:
fmsxml.xml_to_fms("infile.xml", "outfile.fms")

# to do roundtrip test:
fmsxml.fms_to_xml_roundtrip_test("infile.fms", "outfile1.xml", "outfile2.fms")
```

### XML Structure & Notes

The .xml output files should look like this:

```
<?xml version="1.0" encoding="UTF-8"?>
<fms>
    <metadata>
        <headermagicword>FMSB</headermagicword>
        <datasize>1200</datasize>
        <headersize>32</headersize>
        <unknown1>0</unknown1>
        <unknown2>0</unknown2>
        <stringcount>68</stringcount>
        <unknown3>3</unknown3>
        <unknown4>0</unknown4>
        <footermagicword>FEOC</footermagicword>
        <unknown5>0</unknown5>
        <footersize>16</footersize>
        <unknown6>0</unknown6>
    </metadata>
    <stringlist>
        <stringdata>
            <index>0</index>
            <props1>0</props1>
            <props2>0</props2>
            <text>Alain</text>
        </stringdata>
        <stringdata>
            <index>1</index>
            <props1>0</props1>
            <props2>0</props2>
            <text>Ilenia</text>
        </stringdata>

        ... 66 more <stringdata> elements ...
        
    </stringlist>
</fms>
```

**XML Notes:**
- **fms** -- Root node
- **metadata** -- Data fields from the .fms file's header and footer 
  - **headermagicword** -- Anything other than FMSB will result in error. If absent, will default to FMSB.
  - **datasize** -- Informational only. Ignored by parser.
  - **headersize** -- Anything other than 32 will result in error. If absent, will default to 32.
  - **stringcount** -- Zero will result in error. A value that doesn't match the number of \<stringdata\> elements in \<stringlist\> will result in a stern warning. If absent, the parser will just count the number of \<stringdata\> elements in \<stringlist\>. (**Important note:** The program that consumes the .fms file probably expects specific strings at specific indices, so *you probably should not change the number of strings in a file* unless you are really, really sure what you're doing.)
  - **footermagicword** -- Anything other than FEOC will result in error. If absent, will default to FEOC.
  - **footersize** -- Anything other than 16 will result in error. If absent, will default to 16.
  - **unknown1** through **unknown6** -- Unknown data fields that were constant across all observed sample .fms files. If absent, will default to 3 for unknown3 and 0 for the others.
- **stringlist** -- The list of strings.
- **stringdata** -- Container node for each individual string.
  - **index** -- Informational only. Ignored by parser.
  - **props1** and **props2** -- The .fms file contains 8 bytes of additional data for each string. The function of these bytes is unknown because they are all 0 in all observed sample .fms files. They are treated here as two 4-byte unsigned integers. If absent, will default to 0.
  - **text** -- The text of the string itself. See below for notes. If absent, will default to an empty string, with a stern warning.
  - **nullrepeatcount** -- Indicates a series of multiple empty strings in a row. Makes xml files more readable when substantive entries are separated by long stretches of empty strings. The count *includes* the containing \<stringdata\> element. (E.g., \<nullrepeatcount\>8\</nullrepeatcount\> means "this empty string, followed by 7 more empty strings.") Do not add this property to non-empty strings.

**String Notes:**
- Strings are utf-8 encoded. Make sure your text editor is set to utf-8.
- Certain characters that may appear in .fms strings have to be escaped to produce valid xml. When editing, use the escape sequences for these characters. They will be automatically unescaped when converting back to .fms.

| FMS Character | XML Escape Sequence |
| -- | -- |
| &amp; | \&amp; |
| &lt; | \&lt; |
| &gt; | \&gt; |
| &quot; | \&quot; |
| &apos; | \&apos; |
| \\n | \&#xA; |

- Only Unix-style \\n linebreaks have been observed in sample .fms files (escaped to \&#xA; in xml). Windows-style \\r\\n has not been observed and is not presently supported.

### FMS File Structure Documentation

| Offset | Length | Type | Const | What |
| ------------- | ------------- | ------------- | ------------- | ------------- | 
| 0x0 | 4 bytes | magic | 0x464D5342 | magic word = FMSB |
| 0x4 | 4 bytes | int | | length of data section in bytes (*little endian*) (equals file size minus 48) |
| 0x8 | 4 bytes | int | 0x20 | header size in bytes, seems to always be 0x20 (=32) (*little endian*) |
| 0xc | 4 bytes | ? | 0x0 | unknown, seems to always be zero |
| 0x10 | 4 bytes | ? | 0x0 | unknown, seems to always be zero |
| 0x14 | 4 bytes | int | | number of strings (*little endian*) |
| 0x18 | 4 bytes | int | 0x3 | unknown, seems to always be 0x3 (=3) (*little endian*) |
| 0x1c | 4 bytes | ? | 0x0 | unknown, seems to always be zero |
| 0x20 | varies | ? | 0x0 | unknown, 8 bytes per string, seems to always be zero |
| varies | varies | strings | | the strings themselves, stored end-to-end. see format below |
| varies | varies | bytes | 0x0 | zero padding to make the file length at this point an even multiple of 16 bytes |
| end - 0x10 | 4 bytes | magic | 0x46454F43 | magic word = FEOC |
| end - 0xc | 4 bytes | ? | 0x0 | unknown, seems to always be zero |
| end - 0x8 | 4 bytes | int | 0x10 | footer size in bytes, seems to always be 0x10 (=16) (*little endian*) |
| end - 0x4 | 4 bytes | ? | 0x0 | unknown, seems to always be zero |

**String Format:**
- UTF-8 character encoding.
- Strings are terminated with a single zero byte.
- Strings are just placed end-to-end within the file, separated by their terminating zero bytes.
