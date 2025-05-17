import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(layout='wide')

def formatar_numero(valor,prefixo = ''):
    for unidade in ['','mil']:
        if valor <1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor/=1000
    return f'{prefixo} {valor:.2f} milhões'

st.title('DASHBOARD DE VENDAS :shopping_trolley:')


url = 'https://labdados.com/produtos'
regioes= ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']
st.sidebar.title('Filtros')
regiao=st.sidebar.selectbox('Região',regioes)
if regiao == 'Brasil':
    regiao=''

todos_os_anos = st.sidebar.checkbox('Dados de todo o periodo',value=True)
if todos_os_anos:
    ano=''
else:
    ano=st.sidebar.slider('ano',2020,2023)

query_string ={'regiao':regiao.lower(),'ano':ano}
response = requests.get(url,params=query_string)
if response.status_code == 200:
    pass
else:
    st.error(f"Erro ao acessar a API. Código de status: {response.status_code}")
    st.text(response.text)

dados_json = response.json()
dados = pd.DataFrame.from_dict(dados_json)
dados['Data da Compra']= pd.to_datetime(dados['Data da Compra'],format='%d/%m/%Y')

filtro_vendedores =st.sidebar.multiselect('Vendedores',dados['Vendedor'].unique())
if filtro_vendedores:
    dados=dados[dados['Vendedor'].isin(filtro_vendedores)]

###'''tabelas'''
#tabelas de receita
receita_por_Pestado = dados.groupby('Local da compra')[['Preço']].sum()
receita_por_Pestado = dados.drop_duplicates(subset='Local da compra')[['Local da compra','lat','lon']].merge(receita_por_Pestado,left_on='Local da compra',right_index=True)\
.sort_values('Preço',ascending=False)

receita_mensal =dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano']= receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes']= receita_mensal['Data da Compra'].dt.month_name()


receita_por_categoria = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço',ascending=False)
###tabelas de quantidades de vendas                                                                              
vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)

vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].count()).reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month_name()

vendas_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending = False))

###tabelas vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))  
###'''Graficos'''
fig_mapa_receita = px.scatter_geo(receita_por_Pestado,lat='lat',lon='lon',scope='south america',\
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat':False,'lon':False},
                                  title='Receita por estado')

fig_receita_mensal=px.line(receita_mensal,x='Mes',y='Preço',markers=True,
                        range_y= (0,receita_mensal.max()),
                        color='Ano',
                        line_dash='Ano',
                        title='Receita Mensal'
                        )
fig_receita_mensal.update_layout(yaxis_title = 'Receita', xaxis=dict(
        tickangle=45)
        )

fig_receita_por_estado = px.bar(receita_por_Pestado.head(),
                                x='Local da compra',
                                y='Preço',
                                text_auto=True,
                                title='Top estados por (receita)')
fig_receita_por_estado.update_layout(yaxis_title = 'Receita')

fig_receita_por_categoria=px.bar(receita_por_categoria,text_auto=True,
                                 title='Receita por categoria')
fig_receita_por_estado.update_layout(yaxis_title = 'Receita')
### Gráficos vendas
fig_mapa_vendas = px.scatter_geo(vendas_estados, 
                     lat = 'lat', 
                     lon= 'lon', 
                     scope = 'south america', 
                     #fitbounds = 'locations', 
                     template='seaborn', 
                     size = 'Preço', 
                     hover_name ='Local da compra', 
                     hover_data = {'lat':False,'lon':False},
                     title = 'Vendas por estado',
                     )

fig_vendas_estados = px.bar(vendas_estados.head(),
                             x ='Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top 5 estados'
)

fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_mensal = px.line(vendas_mensal, 
              x = 'Mes',
              y='Preço',
              markers = True, 
              range_y = (0,vendas_mensal.max()), 
              color = 'Ano', 
              line_dash = 'Ano',
              title = 'Quantidade de vendas mensal')

fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_categorias = px.bar(vendas_categorias, 
                                text_auto = True,
                                title = 'Vendas por categoria')
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')


#'''visualização no strealit'''
aba1,aba2,aba3 =st.tabs(['Receita','quantidade de vendas','Vendedores'])

with aba1:
    colun1,colun2 = st.columns(2)
    with colun1:
        st.metric("Receita",formatar_numero(dados['Preço'].sum(),'R$'))
        st.plotly_chart(fig_mapa_receita,use_countainer_width=True)
        st.plotly_chart(fig_receita_por_estado,use_countainer_width=True)
    with colun2:
        st.metric('Quantidades de vendas',formatar_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal,use_countainer_width=True)
        st.plotly_chart(fig_receita_por_categoria,use_countainer_width=True)

with aba2:
    colun1,colun2 = st.columns(2)
    with colun1:
        st.metric("Receita",formatar_numero(dados['Preço'].sum(),'R$'))
        st.plotly_chart(fig_mapa_vendas, use_container_width = True)
        st.plotly_chart(fig_vendas_estados, use_container_width = True)
    with colun2:
        st.metric('Quantidades de vendas',formatar_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width = True)
        st.plotly_chart(fig_vendas_categorias, use_container_width = True)

with aba3:
    qtd_de_vendedore = st.number_input("quntidade de vendedores",2,10,5)
    colun1,colun2 = st.columns(2)
    
    with colun1:
        st.metric("Receita",formatar_numero(dados['Preço'].sum(),'R$'))
        fig_receita_por_vendedores = px.bar(vendedores[['sum']].sort_values('sum',ascending=False).head(qtd_de_vendedore),
                                        x='sum',
                                        y=vendedores[['sum']].sort_values('sum',ascending=False).head(qtd_de_vendedore).index,
                                        text_auto=True,
                                        title=f'top {qtd_de_vendedore} vendedores (receita)'
                                        )
        st.plotly_chart(fig_receita_por_vendedores,use_countainer_width=True)
    with colun2:
        st.metric('Quantidades de vendas',formatar_numero(dados.shape[0]))
        fig_vendas_por_vendedores = px.bar(vendedores[['count']].sort_values('count',ascending=False).head(qtd_de_vendedore),
                                        x='count',
                                        y=vendedores[['count']].sort_values('count',ascending=False).head(qtd_de_vendedore).index,
                                        text_auto=True,
                                        title=f'top {qtd_de_vendedore} vendedores (quantidade por vendas)'
                                        )
        st.plotly_chart(fig_vendas_por_vendedores,use_countainer_width=True)

st.dataframe(dados)