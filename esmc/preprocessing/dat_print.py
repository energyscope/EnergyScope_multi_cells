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
from esmc.common import AMPL_SEPARATOR


def ampl_syntax(df: pd.DataFrame, comment=''):
    """

    Parameters
    ----------
    df
    comment

    Returns
    -------

    """
    # adds ampl syntax to df
    df2 = df.copy()
    df2.rename(columns={df2.columns[df2.shape[1] - 1]: str(df2.columns[df2.shape[1] - 1]) + ' ' + ':= ' + comment},
               inplace=True)
    return df2


def print_set(my_set: list, out_path: pathlib.Path, name: str, comment=''):
    with open(out_path, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter=AMPL_SEPARATOR, quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['set ' + name + ' := \t' + '\t'.join(my_set) + ';' + comment])


def print_df(df: pd.DataFrame, out_path: pathlib.Path, name='', mode='a', header=True, index=True, end_table=True):
    df.to_csv(out_path, sep='\t', mode=mode, header=header, index=index, index_label=name, quoting=csv.QUOTE_NONE)
    if end_table:
        with open(out_path, mode='a', newline='') as file:
            writer = csv.writer(file, delimiter=AMPL_SEPARATOR, quotechar=' ', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([';'])


def newline(out_path: pathlib.Path, comment=list()):
    with open(out_path, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter=AMPL_SEPARATOR, quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([''])
        for l in comment:
            writer.writerow([l])

def end_table(out_path: pathlib.Path, comment=''):
    with open(out_path, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter=AMPL_SEPARATOR, quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([';'+comment])



def print_param(param, out_path: pathlib.Path, name: str, comment=''):
    with open(out_path, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter=AMPL_SEPARATOR, quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        if comment == '':
            writer.writerow(['param ' + str(name) + ' := ' + str(param) + ';'])
        else:
            writer.writerow(['param ' + str(name) + ' := ' + str(param) + '; # ' + str(comment)])


def print_header(dat_file: pathlib.Path, header_file=None, header_txt=''):
    """

    Parameters
    ----------
    dat_file : pathlib.Path
    Path to the file to print, if file already exist, it will be overwritten

    header_file : pathlib.Path
    Path to the header file to copy as header of the new file.
    If None (default) is given, print the header_txt as header

    header_txt : str
    If no header_file is given, text to print as header (default: '')

    Returns
    -------

    """

    if header_file is None:
        with open(dat_file, mode='w', newline='') as file :
            file.write('# ' + header_txt)
            file.write('\n')

    else:
        # printing signature of data file
        with open(dat_file, mode='w', newline='') as file, open(header_file, 'r') as header:
            for line in header:
                file.write(line)
