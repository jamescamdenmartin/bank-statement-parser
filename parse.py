import re
import argparse
import os
from PathType import PathType
import csv

transactionpattern  = '(\d{1,2}/\d{1,2} .*? \d{1,9}\.\d{2}\-?)'
yearpattern ='Date\s+\d{1,2}/\d{1,2}/(\d{2})\s+Page\s+1'

outwriter = []

def formatinfobuffer(str):
    infobuffer=str.replace('\n', '\\n').replace('\r', '\\r')
    infobuffer=str.replace('* Denotes check numbers out of sequence', '')
    infobuffer=re.sub(' +',' ',infobuffer)
    infobuffer=infobuffer.strip()
    return infobuffer

def parsefile(filepath):
    outputbuffer=[] # format: list of lists [date, transaction info string, amount]
    infobuffer="" # the transaction info on the statements span multiple lines
                  # in order to parse this out, assume lines between valid transaction matches
                  # are part of the transaction info, stripping whitespace.
                  # hbar lines also 
    lines =[]
    opentransaction = 0
    year = None
    
    with open(filepath, 'r') as f:
       # Read the file contents and generate a list with each line
       lines = f.readlines()

    # Iterate over each line in the statement
    for line in lines:
        # Parse the year from the date at the top of the statement
        if year==None:
            match=re.search(yearpattern, line)
            if match:
                year=match.group(1)
                print("Found year")
            
        # Regex applied to each line 
        matches = re.finditer(transactionpattern, line) # Can be more than one transaction per line in the check section
        at_least_one_match=0
        while 1:
            match = next(matches, None)
            if match:
                at_least_one_match=1
                
                # Close out any pending multiline transactions
                if (len(outputbuffer)-1) > 0:
                  infobuffer=formatinfobuffer(infobuffer)
                  outputbuffer[len(outputbuffer)-1][1]=outputbuffer[len(outputbuffer)-1][1]+infobuffer
                  print(infobuffer)
                  infobuffer=""
                  opentransaction=0
                
                # Print transaction console for debugging
                transaction = match.group() + '\n'
                print(transaction)
                
                # Parse out the date and amount by trimming excess whitespace and exploding on it
                # the date should then be the first set of characters, and the amount the last
                temp = transaction.strip()
                temp=temp.split(' ')
                t_date=temp[0]+"/"+year
                del temp[0]
                t_amount=temp[len(temp)-1]
                
                # negative sign is at the end of the number in the statements, fix that
                if t_amount[-1]=="-":
                  t_amount="-" + t_amount[0:-1]
                
                del temp[len(temp)-1]
                t_info=' '.join(temp).strip() + '\n'
                
                # If it's a check spent from the account, set the sign to debit
                if re.match('\d{3,5}\n$', t_info):
                    t_amount="-" + t_amount[0:-1]
                
                outputbuffer.append([t_date,t_info,t_amount])
                
                opentransaction=1
            else:
                break
        
        if at_least_one_match==0: # handle multiline transaction info
            if len(line.strip()) > 0 and opentransaction:
                infobuffer = infobuffer + line
            else: # empty lines denote the start of the next section in the statement txts
                  # so also close out transaction info on these
                if (len(outputbuffer)-1) >0 :
                  infobuffer=formatinfobuffer(infobuffer)
                  outputbuffer[len(outputbuffer)-1][1]=outputbuffer[len(outputbuffer)-1][1]+infobuffer
                  infobuffer=""
                  opentransaction=0

    outwriter.writerows(outputbuffer)
     
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Parse RBT .txt bank statements')
  
  parser.add_argument('--indir', type=PathType(exists=True, type='dir'), required=True)
  parser.add_argument('--outfile', type=argparse.FileType('w+', encoding='UTF-8'), 
                      required=True)
  args = parser.parse_args()
  
  print(args)
  
  args.outfile.close()
  
  with open(args.outfile.name, 'w+', newline='') as csvfile:
      outwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
      for statement in os.listdir(args.indir):
        if os.path.isfile(os.path.join(args.indir,statement)): 
          print ("Parsing "+statement)
          parsefile(os.path.join(args.indir,statement))

  