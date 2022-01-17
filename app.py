import streamlit as st
import pandas as pd
from PIL import Image
import graphistry

from src.utils import (
    search_to_df,
    get_graphistry_from_search,
    get_graphistry_from_milieu_search,
    setup_logger,
)


logger = setup_logger(__name__)

src, dst, node_col = "to_node", "from_node", "Node"


@st.cache
def get_data(dummy_variable):
    logger.info("Loading Data")
    edges = pd.read_csv("data/edges.csv", index_col=0)
    edges = edges.fillna("")
    nodes = pd.read_csv("data/nodes.csv", index_col=0)
    nodes = nodes.fillna("")
    return edges, nodes


def icon(icon_name):
    st.markdown(f'<i class="material-icons">{icon_name}</i>', unsafe_allow_html=True)


def display_graph(g):
    url = g.plot(render=False)
    st.markdown(
        f'<iframe width=1000 height=800 src="{url}"></iframe>', unsafe_allow_html=True
    )


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


edf, ndf = get_data(True)

# search bar
st.sidebar.header("Influence & Power Networks")
st.sidebar.subheader("Search Network")

rand = st.sidebar.checkbox("Get Random")
if rand:
    entity_options = ndf.Node
    entity = entity_options.sample(1).values[0]
else:
    entity = "BlackRock"

local_or_milieu = st.sidebar.checkbox("Local or Milieu Search")
search_summary_and_blurb = st.sidebar.checkbox("Search Text", value=~local_or_milieu)

search_term = st.sidebar.text_input("", entity, key="search")

# get the graph
if search_summary_and_blurb:
    g = text_search(search_term)
    st.write(g._nodes)
elif local_or_milieu:
    g = simple_search(search_term)
else:
    g = milieu_search(search_term)

display_graph(g)

# logo
st.sidebar.write("-" * 40)
image = Image.open("./tensorml.png")
st.sidebar.image(image, use_column_width=True)
