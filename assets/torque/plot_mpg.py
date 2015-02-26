# -*- coding: utf-8 -*-
import pandas as pd
import sqlalchemy
import oursql
import matplotlib.pyplot as plt
import seaborn as sns


def load_from_mysql():
    conn = sqlalchemy.create_engine("mysql+oursql://steve:zissou@localhost/torque")
    df = pd.read_sql('raw_logs',conn)
    return df

def load_from_file():
    df = pd.read_csv('/home/aahu/chinar/ryancompton.net/assets/torque/torque_data.tsv',
                      sep='\t')
    return df

def main():
    df = load_from_file()

if __name__=='__main__':
    main()

"""
#pull out the mpg column
mpg = df['kff1201'].map(float)
mpg = mpg[mpg>0]
mpg = mpg[mpg<150]

#plot
sns.set_style('dark')
plt.hist(mpg, 100)
plt.title('Instantaneous MPG measurements, 2003 Suzuki Aerio SX 5sp manual')
plt.savefig('mpg_hist.png')

print(mpg.mean())
print(mpg.median())
"""
