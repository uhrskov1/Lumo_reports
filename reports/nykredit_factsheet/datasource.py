from os.path import abspath, dirname


def curate_data(fund_name: str):
    factsheet = dirname(abspath(__file__)) + f'\\utils\\{fund_name}.png'

    return {'factsheet': factsheet}
