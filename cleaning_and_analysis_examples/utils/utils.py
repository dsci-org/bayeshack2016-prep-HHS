#author : steeve laquitaine modified from everett wetchler
#purpose Helpers functions to check dataset

#Setup
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

#Helper functions
def percentify_axis(ax, which):
    which = which.lower()
    if which in ('x', 'both'):
        ax.set_xticklabels(['%.0f%%' % (t*100) for t in ax.get_xticks()])
    if which in ('y', 'both'):
        ax.set_yticklabels(['%.0f%%' % (t*100) for t in ax.get_yticks()])

color_idx = 0
CYCLE_COLORS = sns.color_palette()
def next_color():
    global color_idx
    c = CYCLE_COLORS[color_idx] 
    color_idx = (color_idx + 1) % len(CYCLE_COLORS)
    return c

def count_unique(s):
    values = s.unique()
    return sum(1 for v in values if pd.notnull(v))

def missing_pct(s,N):
    missing = N - s.count()
    return missing * 100.0 / N

def complete_pct(s,N):
    return 100 - missing_pct(s,N)

def summarize_completeness_uniqueness(df,N):
    print '*** How complete is each feature? How many different values does it have? ***'
    rows = []
    for col in df.columns:
        rows.append([col, '%.0f%%' % complete_pct(df[col],N), count_unique(df[col])])
    dframe = pd.DataFrame(rows, columns=['Column Name', 'Complete (%)','Unique Values'])
    pd.set_option('display.max_colwidth',999,'display.max_row',999)
    return dframe

def summarize_completeness_over_time(df, time_col, transpose=True):
    print '*** Data completeness over time per column ***'
    x = df.groupby(time_col).count()
    x = x.div(df.groupby(time_col).size(), axis=0)
    for col in x.columns:
        x[col] = x[col].apply(lambda value: '%.0f%%' % (value * 100))
    if transpose:
        return x.T
    pd.set_option('display.max_colwidth',999,'display.max_row',999)
    return x

def plot_top_hist(df, col, top_n=10, skip_below=.01):
    '''Plot a histogram of a categorical dataframe column, limiting to the most popular.'''
    counts = df[col].value_counts(True, ascending=True)
    if counts.max() < skip_below:
        print 'Skipping "%s" histogram -- most common value is < %.0f%% of all cases' % (col, skip_below*100)
        return
    fig, ax = plt.subplots(1)
    explanation = ''
    if len(counts) > top_n:
        explanation = ' (top %d of %d)' % (top_n, len(counts))
        counts = counts.iloc[-top_n:]
    explanation += ' -- %.0f%% missing' % (missing_pct(df[col]))
    counts.plot(kind='barh', ax=ax, color=next_color())
    ax.set_title('Rows by "%s"%s' % (col, explanation))
    ax.set_xticklabels(['%.0f%%' % (t*100) for t in ax.get_xticks()])
    
def checkObsValsMatchExpectedVals(df,myvars,expectedVals):

    #author: steeve laquitaine <steeve@stanford.edu>    
    #purpose: check that the data observed match expected values
              #stored in a dictionary
        
    #inputs:    
             #df: pandas dataframe
             #myvars: variable names = ['BusinessYear','StateCode',....'Age']
             #expectedVals: expected values for each variable: 
             #     e.g., expectedVals["StateCode"] =['AK','AL','AZ,......,'WA','WV','WI','WY']
    
    print '*** Are there any values outside their expected range ? ***'
    rows = []

    #Check validity
    for col in myvars:    
        #check among existing string values    
        if isinstance(np.unique(df[col][pd.notnull(df[col])])[0],basestring):
            s = pd.Series(list(df[col].str.lower()))
            
            #expected are lower case strings        
            exp = map(lambda x:x.lower(),expectedVals[col])
            
            #set all entries to lower case
            df[col] = df[col].str.lower()
        else:
            #...or numerical values
            s = pd.Series(list(df[col]))        
            
            #expected are numbers
            exp = expectedVals[col]
            
        s_exist = s[pd.notnull(s)]
        numValid = np.sum(s_exist.isin(exp))    
        percValid = numValid*100/len(s_exist)
        rows.append([col,'%.0f%%' % percValid,numValid])
    
    #table
    tab = pd.DataFrame(rows,columns=['Column Name', 'Valid value(%)','Unique Valid Values'])        
    
    #cleaned dataset
    return (df,tab)

def checkObsValsAreIntegers(df,myvars,numerics):
    #author: steeve laquitaine <steeve@stanford.edu>    
    #purpose: check that the data values are numerical                     
    #inputs:    
             #df: pandas dataframe
             #myvars: variable names = 'BusinessYear'
             #numerics 
                #e.g., ['int16', 'int32', 'int64']        
    print len(df.select_dtypes(include=numerics)[myvars])*100/df.shape[0],'% of', myvars, 'are numerics as expected'
    
def checkDataFramesVarMatch(df1,df2):    
    #author: steeve laquitaine <steeve@stanford.edu>
    #purpose: check that data column variables match
    print sum(df1.columns==df2.columns)*100/len(df2.columns), '% of the variables matched'
    
def concatDataFrames(df1,df2,df3):   
    #author: steeve laquitaine <steeve@stanford.edu>
    #purpose: concatenate three pandas dataframes
    df = pd.concat([df1,df2,df3]).reset_index(drop=True)
    N = len(df)
    print 'Read %d rows %d cols\n' % df.shape 
    tab = df.head(3) 
    return (df,N,tab)
   
def checkDataMatchBetweenVars(df,var1,var2): 
    #author: steeve laquitaine <steeve@stanford.edu>    
    #purpose: check that the data for two columns of a panda dataframe match
    print sum(df[var1]==df[var2])*100/df.shape[0],'% of the rows match between the two variables so I dropped the second'
    
def checkDataPositiveNumbers(df,df_cleaned,VarDollars):
    #author: steeve laquitaine <steeve@stanford.edu>
    #purpose: check positive numbers, remove '$' signs and convert to float,
    #         write missing as NaN       
    #Remove dollar signs, format all numbers as floats and check
    rows = []
    #loop through variables
    for col in VarDollars:         
        exst = df[col][:]
        rows_j = []
        #remove '$' signs and convert to float
        for j in exst:            
            #case not missing and not written'Not Applicable'
            if pd.notnull(j) and j!='Not Applicable' and isinstance(j,basestring):
                stripped = j.strip('$').replace(',','')
                stripAndFloat = float(stripped)
                #case number
            elif isinstance(j,int) or isinstance(j,float):
                stripAndFloat = j
            else:
                #missing
                stripAndFloat = np.nan            
            rows_j.append(stripAndFloat)

        #fill with cleaned data    
        df_cleaned[col] = rows_j

        #check how many values are >=0
        numExist = len(df_cleaned[col][pd.notnull(df_cleaned[col])])
        numValid = sum(df_cleaned.loc[:,col]>=0)
        percValid = numValid*100/numExist
        rows.append([col,percValid,numValid])  
    #table
    tab = pd.DataFrame(rows,columns=['Column Name', 'Valid value(%)','Unique valid values'])
    return(df_cleaned,tab)

def checkDataLengthMatchExpected(df,var,expected_len):  
    #author: steeve laquitaine <steeve@stanford.edu>    
    #purpose: check that the data has the expected length
    df.colnm = df[var]
    lenByRow = df.colnm.str.len()
    print sum(lenByRow==expected_len)*100/df.shape[0],'% of the data matched the expected length'
    