# -*- coding: utf-8 -*-
"""TODO
Created on ...

Contains ...

@author: Paolo Thiran
"""
import logging
import pathlib
from pathlib import Path
import os

import numpy as np
import pandas as pd
import csv


def ampl_syntax(df: pd.DataFrame, comment=''):
    # adds ampl syntax to df
    df2 = df.copy()
    df2.rename(columns={df2.columns[df2.shape[1] - 1]: str(df2.columns[df2.shape[1] - 1]) + ' ' + ':= ' + comment},
               inplace=True)
    return df2


def print_set(my_set: list, out_path: pathlib.Path, name: str, comment=''):
    with open(out_path, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['set ' + name + ' := \t' + '\t'.join(my_set) + ';' + comment])


def print_df(df: pd.DataFrame, out_path: pathlib.Path, name='', header=True, index=True, end_table=True):
    df.to_csv(out_path, sep='\t', mode='a', header=header, index=index, index_label=name, quoting=csv.QUOTE_NONE)
    if end_table:
        with open(out_path, mode='a', newline='') as file:
            writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([';'])


def newline(out_path: pathlib.Path, comment=list()):
    with open(out_path, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([''])
        for l in comment:
            writer.writerow([l])

def end_table(out_path: pathlib.Path, comment=''):
    with open(out_path, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([';'+comment])



def print_param(param, out_path: pathlib.Path, name: str, comment=''):
    with open(out_path, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        if comment == '':
            writer.writerow(['param ' + str(name) + ' := ' + str(param) + ';'])
        else:
            writer.writerow(['param ' + str(name) + ' := ' + str(param) + '; # ' + str(comment)])


def print_header(header_file: pathlib.Path, dat_file: pathlib.Path):
    # printing signature of data file
    with open(dat_file, mode='w', newline='') as file, open(header_file, 'r') as header:
        for line in header:
            file.write(line)
