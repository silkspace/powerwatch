import pandas as pd

def get_powerwatch_dataframe():
    print('returning dict of edges and nodes dataframes')
    edges, nodes = pd.read_csv('data/edges.csv'), pd.read_csv('data/nodes.csv')
    return {'nodes': nodes, 'edges': edges}
