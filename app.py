import streamlit as st
import pandas as pd
from PIL import Image
from urllib.parse import urljoin, quote

from src.utils import (
    search_text_to_graphistry,
    get_graphistry_from_search,
    get_graphistry_from_milieu_search,
    setup_logger, contribution

)

logger = setup_logger(__name__)

src, dst, node_col = "to_node", "from_node", "Node"
good_node_cols = ['Node', 'link', 'Blurb', 'Summary', 'Website']
good_node_tags = ['Types', 'Revenue', 'Aliases', 'pagerank']

@st.cache(suppress_st_warning=True)
def get_data(dummy_variable=True):
    logger.info("Loading Data")
    edges = pd.read_csv("data/edges.csv", index_col=0)
    edges = edges.fillna("")
    st.write(f'Number of total relationships {len(edges):,}')
    
    nodes = pd.read_csv("data/nodes.csv", index_col=0)
    nodes = nodes.fillna("")
    st.write(f'Number of total entities {len(nodes):,}')

    return edges, nodes


def icon(icon_name):
    st.markdown(f'<i class="material-icons">{icon_name}</i>', unsafe_allow_html=True)


def display_graph(g):
    if len(g._nodes)>0:
        url = g.plot(render=False)
        st.markdown(
            f'<iframe width=1000 height=800 src="{url}"></iframe>', unsafe_allow_html=True
        )
    else:
        st.write('No results found, try another search term')

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


def tag_boxes(search: str, tags: list) -> str:
    """ HTML scripts to render tag boxes.
    st.write(tag_boxes(search, results['sorted_tags'][:10], ''),
                 unsafe_allow_html=True)
    """
    html = ''
    search = quote(search)
    for tag in tags:
            html += f"""
            <a id="tags" href="?search={search}&tags={tag}">
                {tag.replace('-', ' ')}
            </a>
            """
    html += '<br><br>'
    return html

def pretty_pandas(i, node, url, blurb, summary, website):
    littlesis = 'https://littlesis.org/'
    url = urljoin(littlesis, url)
    if website !='':
        res = f"""
            <div style="font-size:122%;">
                {i + 1}.
                <a href="{url}">
                    {node}
                </a>
            </div>
            <div style="font-size:95%;">
                <div style="color:grey;font-size:85%;">
                    <a href="{website}">
                    {website[:90]}
                    </a>
                </div>
                <div style="font-size:112%;float:left;font-style:italic;">
                    {blurb} ·&nbsp;
                </div>
                <div style="float:left;font-style:normal;">
                    {summary} ·&nbsp;
                </div>
            </div>
        """
    else:
        res = f"""
               <div style="font-size:122%;">
                   {i + 1}.
                   <a href="{url}">
                       {node}
                   </a>
               </div>
               <div style="font-size:95%;">
                   <div style="font-size:112%;float:left;font-style:italic;">
                       {blurb} ·&nbsp;
                   </div>
                   <div style="float:left;font-style:normal;">
                       {summary} ·&nbsp;
                   </div>
               </div>
           """
    return res

def print_results(search, ndf, topN=100):
    tdf = ndf.drop_duplicates()
    tdf = tdf.sort_values(by='pagerank', ascending=False)
    for i, (_, row) in enumerate(tdf.iterrows()):
        if i>=topN:
            break
        st.write(pretty_pandas(i, row.Node, row.link, row.Blurb, row.Summary, row.Website), unsafe_allow_html=True)
        # tags = row.Types.split(',')
        # tags = [t.strip() for t in tags]
        # st.write(tag_boxes(search, tags), unsafe_allow_html=True)
        
        
etdf, ndf = get_data(True)
edf = etdf
# search bar
st.sidebar.header("Influence & Power Networks")
st.sidebar.subheader("Search Network")

drop_contributors = st.sidebar.checkbox("Drop Contributors", value=True)

if drop_contributors:
    edf = etdf[etdf.relationship != contribution]
    #st.write(f'Number of total relationships after removing "{contribution}" data is {len(edf):,}')

rand = st.sidebar.checkbox("Get Random Entity")
if rand:
    entity_options = ndf.Node
    entity = entity_options.sample(1).values[0]
else:
    entity = "BlackRock"

options = ['Search Text', 'Milieu', 'Nearest']
option = st.sidebar.selectbox('Search Type', options)

if rand: # for random entity need Milieu or Local, since they search Nodes
    option = options[1]

search_term = st.sidebar.text_input("", entity, key="search")

# get the graph
if option==options[0]:
    st.sidebar.write(f'Searching Summary and Blurb for {search_term}')
    g = text_search(search_term)
if option==options[1]:
    st.sidebar.write(f'Searching node entities for milieu graph of {search_term}')
    g = milieu_search(search_term)
if option==options[2]:
    st.sidebar.write(f'Searching node entities for nearest connections to {search_term}')
    g = simple_search(search_term)
    
# The main frontend calls
this_df = g._nodes
display_graph(g)
print_results(search_term, this_df)

# logo
st.sidebar.write("-" * 40)
image = Image.open("./tensorml.png")
st.sidebar.image(image, use_column_width=True)
# st.markdown("[[TensorML](./tensorml.png)](http://www.tensorML.com)")

