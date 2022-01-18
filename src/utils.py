import graphistry
import pandas as pd
import logging
import streamlit as st
from collections import Counter


def setup_logger(name):
    logger = logging.getLogger(name)
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(format=FORMAT)
    logger.setLevel(logging.DEBUG)
    return logger


logger = setup_logger(__name__)

username = st.secrets["USERNAME"]
password = st.secrets["GRAPHISTRY_PASSWORD"]

graphistry.register(
    api=3,
    protocol="https",
    server="hub.graphistry.com",
    username=username,
    password=password,
)

src, dst, node_col = "to_node", "from_node", "Node"

# #################################################################################################
#
#   Preprocessing functions to make a better dataframe experience.
#
# #################################################################################################


contribution = "contribution"


def get_count(x):
    x = x.strip()
    try:
        x = int(x)
        return x
    except:
        return 1


def count_contributions(x):
    if contribution in x:
        res = x.split(contribution)
        if len(res) == 1:
            return contribution, 1
        if len(res) > 1:
            y = get_count(res[0])  # assumes the count is at the front
            return contribution, y
    else:
        return x, 0


def normalize_contributions(edf):
    t = edf.relationship_type.apply(lambda x: count_contributions(x))
    rt = [k[0] for k in t.values]
    vt = [k[1] for k in t.values]
    cnt = Counter(rt)
    print("Most Common Relationship Types")
    print("-" * 40)
    for k, c in cnt.most_common(10):
        print(f"{k}: {c:,} total")
    edf["relationship"] = rt
    edf["contribution_count"] = vt

    print("\nMost Common Contribution Counts")
    print("-" * 40)
    for k, c in Counter(edf.contribution_count).most_common(10):
        print(f"Number of Contributions {k}: {c:,} total")


def moneyify(money: str):
    from re import sub
    from decimal import Decimal

    try:
        value = Decimal(sub(r"[^\d.]", "", money))
    except:
        return 0
    return value


def get_total_value_contributions(edf):
    cdf = edf[edf.relationship == contribution]
    amounts = cdf.metadata.str.split().apply(
        lambda x: x if len(x) == 0 else moneyify(x[0])
    )
    edf["amount"] = amounts
    edf["amount"] = edf.amount.fillna(0)
    # take care of places where metadata was null, which maps to a []
    r = edf.amount.apply(lambda x: isinstance(x, list))
    edf.loc[r, "amount"] = -1  # send to unknown, here -1


def get_contributions_for_entity(entity, edf, both=False):
    if both:  # doesn't really make sense
        tdf = pd.concat(
            [
                search_to_df(entity, "to_node", edf),
                search_to_df(entity, "from_node", edf),
            ],
            axis=0,
        )
    else:
        tdf = search_to_df(entity, "to_node", edf)
    total_contributions = tdf[tdf.relationship == contribution].amount.sum()
    return total_contributions


# #################################################################################################
#
#   Finding subgraphs within a large graph.
#
# #################################################################################################


def search_to_df(word, col, df):
    """
    A simple way to retrieve entries from a given col in a dataframe
    :eg
        search_to_df('BlackRock', 'to_node', edf)

    :param word: str search term
    :param col: given column of dataframe
    :param df: pandas dataframe
    :returns
        DataFrame of results
    """
    try:
        res = df[df[col].str.contains(word, case=False)]
    except TypeError as e:
        logger.error(e)
        return df
    return res


def search_text_to_graphistry(search_term, src, dst, node_col, edf, ndf):
    res = pd.concat(
        [
            search_to_df(search_term, "Summary", ndf),
            search_to_df(search_term, "Blurb", ndf),
        ],
        axis=0,
    )
    tdf = edf[edf.to_node.isin(res.Node)]
    g = graphistry.edges(tdf, src, dst).nodes(res, node_col)
    return g


# def df_to_graph(src, dst, node_col, edf, df):
#     g = graphistry.edges(edf, src, dst).nodes(df, node_col)
#     return g
#
# def search_to_graphistry(search_term, search_col, src, dst, node_col, edf, ndf):
#     df = search_to_df(search_term, search_col, ndf)
#     return df_to_graph(src, dst, node_col, edf, df)


def get_nearest(search_term, src, dst, edf):
    """
    :param search_term:
    :param src:
    :param dst:
    :param edf:
    :return: pandas.DataFrame
    """
    logger.info(f"Finding {search_term} in both {src} and {dst} columns")
    tdf = pd.concat(
        [search_to_df(search_term, src, edf), search_to_df(search_term, dst, edf)],
        axis=0,
    )
    return tdf


def get_graphistry_from_search(search_term, src, dst, node_col, edf, ndf):
    """
        Useful helper function to get subgraph from a search term
    :param search_term: Note this retrieves all nodes that have `search_term` in it -- ie, not strict matches
    :param src:
    :param dst:
    :param node_col:
    :param edf:
    :param ndf:
    :return:
    """
    tdf = get_nearest(search_term, src, dst, edf)
    gcols = pd.concat(
        [tdf[dst], tdf[src]], axis=0
    )  # get all node entries that show up in edge graph
    ntdf = ndf[ndf[node_col].isin(gcols)]
    g = graphistry.edges(tdf, src, dst).nodes(ntdf, node_col)
    return g


# lets make simple functions to find subgraphs by search_term = a given node
def get_milieu_graph_from_search(search_term, src, dst, edf, both=False):
    """
    Can think of this as finding all 2-hop connections from a given `search_term`. It will find all direct edges to
    `search_term` as well as the edges of all those entities. It shows the `milieu graph` of the `search_term`
    :param search_term:
    :param src:
    :param dst:
    :param edf:
    :param both: to retrieve edges from both src and dst columns of dataframe -- if true, returns a larger edgeDataFrame
    :return:
    """
    # get all the entities in either column
    # tdf = pd.concat([search_to_df(search_term, src, edf), search_to_df(search_term, dst, edf)], axis=0)
    tdf = get_nearest(search_term, src, dst, edf)
    # now find all their nearest connections.
    if both:
        gcols = pd.concat([tdf[dst], tdf[src]], axis=0)
        logger.info(
            f"Then finding all edges from {search_term} in {src} and {dst} columns of full edgeDataFrame"
        )
        df = edf[(edf[src].isin(gcols) | edf[dst].isin(gcols))]
    else:
        # logger.info(f'Finding {search_term} in {src} columns')
        # tdf = search_to_df(search_term, src, edf)
        logger.info(
            f"Then finding {src} columns with edges from {search_term} in {dst} column of full edgeDataFrame"
        )
        df = edf[edf[src].isin(list(tdf[dst]) + [search_term])]
    return df


def get_graphistry_from_milieu_search(
    search_term, src, dst, node_col, edf, ndf, both=False
):
    """
        Produces large graphs of neighbors from a given search term
    :param search_term:
    :param src:
    :param dst:
    :param node_col:
    :param edf:
    :param ndf:
    :param both:
    :return:
    """
    tdf = get_milieu_graph_from_search(search_term, src, dst, edf, both=both)
    gcols = pd.concat(
        [tdf[dst], tdf[src]], axis=0
    )  # get all node entries that show up in edge graph
    ntdf = ndf[ndf[node_col].isin(gcols)]
    g = graphistry.edges(tdf, src, dst).nodes(ntdf, node_col)
    return g


if __name__ == "__main__":
    pass
