from urllib.parse import urljoin, quote

import streamlit as st


def icon(icon_name):
    st.markdown(f'<i class="material-icons">{icon_name}</i>', unsafe_allow_html=True)


def display_graph(g):
    if len(g._nodes) > 0:
        url = g.settings(url_params={'strongGravity': True}).plot(render=False)
        st.markdown(
            f'<iframe width=1000 height=800 src="{url}"></iframe>',
            unsafe_allow_html=True,
        )
    else:
        st.write("No results found, try another search term")
        
        
def tag_boxes(search: str, tags: list) -> str:
    """HTML scripts to render tag boxes.
    st.write(tag_boxes(search, results['sorted_tags'][:10], ''),
                 unsafe_allow_html=True)
    """
    html = ""
    search = quote(search)
    for tag in tags:
        html += f"""
            <a id="tags" href="?search={search}&tags={tag}">
                {tag.replace('-', ' ')}
            </a>
            """
    html += "<br><br>"
    return html


def pretty_pandas(i, node, url, blurb, summary, website):
    littlesis = "https://littlesis.org/"
    url = urljoin(littlesis, url)
    if website != "":
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
    tdf = tdf.sort_values(by="pagerank", ascending=False)
    for i, (_, row) in enumerate(tdf.iterrows()):
        if i >= topN:
            break
        st.write(
            pretty_pandas(i, row.Node, row.link, row.Blurb, row.Summary, row.Website),
            unsafe_allow_html=True,
        )
        # tags = row.Types.split(',')
        # tags = [t.strip() for t in tags]
        # st.write(tag_boxes(search, tags), unsafe_allow_html=True)

