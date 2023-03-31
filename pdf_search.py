
"""
    Requires the following folders be added to the application's modules folder:
    - pdfminer/
    - chardet/
    - six.py
"""

from io import StringIO
import os
import sqlite3

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

try:
    from gluon.contrib.appconfig import AppConfig
    configuration = AppConfig(reload=True)
    environment = str(configuration.get('cama_config.environment'))
    DB_PATH = fr'C:\Users\xxxx\applications\{environment}\databases\storage.sqlite'
except:
    # Will only allow for fall back in test!
    environment = "TEST"
    DB_PATH = fr'C:\Users\xxx\applications\TEST\databases\storage.sqlite'

def _convert(fname, pages=None):
    """ Converts the contents of a PDF into a Text Object (in memory not stored anywhere) """
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)

    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    if os.path.exists(fname):
        infile = open(fname, 'rb')
    else:
        return False

    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)

    infile.close()
    converter.close()
    text = output.getvalue()
    output.close
    return text

def remSpace(directory, filename):
    filePath = os.path.join(directory, filename)
    try:
        file = os.rename(filePath, os.path.join(directory, filename.replace(' ', '_')))
        return file
    except FileExistsError: 
        os.remove(filePath)
        return False

def convertMultiple(pdfDir, tag):
    """ 
        Puts the converted PDF's and its text into the CAMAHub DB to be parsed later
    """
    with sqlite3.connect(DB_PATH) as conn:
        record_count = conn.execute("SELECT COUNT(*) FROM journals_fts WHERE tag=:tag", dict(tag=tag)).fetchone()
    if record_count[0] != len(os.listdir(pdfDir)):
        missing_pdfs = findMissing(tag, pdfDir, 'pdf')
        for pdf in missing_pdfs:
            fileExtension = pdf.split(".")[-1]
            if fileExtension == "pdf":
                if ' ' in pdf: pdf = remSpace(pdfDir, pdf) # Convert spaces to underscores
                pdfFilename = pdfDir + '\\' + str(pdf)
                with sqlite3.connect(DB_PATH) as conn:
                    cur = conn.execute('SELECT title FROM journals_fts WHERE title=:title AND tag=:tag', dict(title=pdf, tag=tag))
                    if not cur.fetchone() and pdf != None:
                        print(f"Converting PDF: {pdf}")
                        text = _convert(pdfFilename)
                        try:
                            conn.execute("INSERT INTO journals_fts ('tag', 'title', 'text') VALUES(:tag, :pdf, :text);", dict(tag=tag, pdf=pdf, text=text)
                            )
                            print(f"Done converting {pdf}")
                        except Exception as e:
                            print(f"{environment}: pdf_search > convertMultiple: {e}")

def searchDB(tag, searchTerm):
    """ Searches the xxxx DB for the contents requested by the user """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            searchResults = conn.execute('''SELECT title, snippet(journals_fts, 2, '<b style="background-color: var(--text-color-complementary);">', '</b>', '...', 64) text FROM journals_fts WHERE tag=:tag AND text MATCH :search ORDER BY rank''', dict(tag=tag, search=searchTerm)).fetchall()
        return searchResults
    except:
        return None

def isNotJournal(journal):
    """ To be used by Filter to find which Journal(s) are not in the DB """
    if journal not in PDF_SEARCH_DB_TAG_RECORDS:
        return True
        
def isNotInFolder(record):
    """ To be used by Filter to find which Record(s) are not in the DB but not in the folder """
    if record not in PDF_SEARCH_TAG_PDFS:
        return True
        
def findMissing(tag, pdfDir, *args):
    """ Finds which PDF's are present in the folder but not in the DB 
        Returns an iterable
    """
    with sqlite3.connect(DB_PATH) as conn:
        records = conn.execute('SELECT title FROM journals_fts WHERE tag=:tag', 
            dict(tag=tag)
        ).fetchall()
    records = [i[0] for i in records]
    pdfs = os.listdir(pdfDir)
    globals()['PDF_SEARCH_DB_TAG_RECORDS'] = records
    globals()['PDF_SEARCH_TAG_PDFS'] = pdfs
    
    if 'pdf' in args: return filter(isNotJournal, pdfs)
    if 'record' in arGs: return filter(isNotInFolder, records) 

if __name__ == "__main__":
    journals = fr'C:\Users\xxxx\applications\{environment}\static\files\journals'
    tag = 'Journals'
    #convertMultiple(journals, tag)
    searchTerm = "Jesus"
    print(searchDB(tag, searchTerm))