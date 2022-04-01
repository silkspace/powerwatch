import streamlit as st
import pandas as pd

from src.utils import (
    search_text_to_graphistry,
    get_graphistry_from_search,
    get_graphistry_from_milieu_search,
    setup_logger,
    contribution,
)
from utils import *

logger = setup_logger(__name__)

src, dst, node_col = "to_node", "from_node", "Node"
good_node_cols = ["Node", "link", "Blurb", "Summary", "Website"]
good_node_tags = ["Types", "Revenue", "Aliases", "pagerank"]


@st.cache(suppress_st_warning=True)
def get_data(dummy_variable=True):
    logger.info("Loading Data")
    edges = pd.read_csv("data/edges.csv", index_col=0)
    edges = edges.fillna("")
    st.write(f"Number of total relationships {len(edges):,}")

    nodes = pd.read_csv("data/nodes.csv", index_col=0)
    nodes = nodes.fillna("")
    st.write(f"Number of total entities {len(nodes):,}")

    return edges, nodes



@st.cache
def simple_search(search_term):
    g = get_graphistry_from_search(search_term, src, dst, node_col, edf, ndf)
    return g


@st.cache
def milieu_search(search_term, both=False):
    g = get_graphistry_from_milieu_search(
        search_term, src, dst, node_col, edf, ndf, both=both
    )
    return g


@st.cache
def text_search(search_term):
    g = search_text_to_graphistry(search_term, src, dst, node_col, edf, ndf)
    return g


etdf, ndf = get_data(True)
edf = etdf
# search bar
st.sidebar.header("Influence & Power Networks")
st.sidebar.subheader("Search Network")

drop_contributors = st.sidebar.checkbox("Drop Contributors", value=True)

if drop_contributors:
    edf = etdf[etdf.relationship != contribution]
    # st.write(f'Number of total relationships after removing "{contribution}" data is {len(edf):,}')

rand = st.sidebar.checkbox("Get Random Entity")
if rand:
    entity_options = ndf.Node
    entity = entity_options.sample(1).values[0]
else:
    entity = "BlackRock"

options = ["Search Text", "Milieu", "Nearest"]
option = st.sidebar.selectbox("Search Type", options)

if rand:  # for random entity need Milieu or Local, since they search Nodes
    option = options[1]

search_term = st.sidebar.text_input("", entity, key="search")

# get the graph
if option == options[0]:
    st.sidebar.write(f"Searching Summary and Blurb for {search_term}")
    g = text_search(search_term)
if option == options[1]:
    st.sidebar.write(f"Searching node entities for milieu graph of {search_term}")
    g = milieu_search(search_term)
if option == options[2]:
    st.sidebar.write(
        f"Searching node entities for nearest connections to {search_term}"
    )
    g = simple_search(search_term)

#
# layouts = st.multiselect(
#      'Layout Settings',
#      ['Dissuade Hubs'], ['Strong Gravity'])
#
# st.write(layouts)

# g = g.settings(url_params={
#                        'pointSize': 70.,
#                        'edgeCurvature': 0.2,
#                        'edgeOpacity': 0.5,
#                        'dissuadeHubs': True,
#                        'strongGravity': True,
#                        'pointsOfInterestMax': 7})


# The main frontend calls
display_graph(g)
this_df = g._nodes
print_results(search_term, this_df)

# logo
st.sidebar.write("-" * 40)
# image = Image.open("./tensorml.png")
# st.sidebar.image(image, use_column_width=True)
