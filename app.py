import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import openai
from typing import Dict, List, Optional
import requests

# Configurazione pagina
st.set_page_config(
    page_title="GSC Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class GSCAnalytics:
    def __init__(self):
        self.service = None
        self.credentials = None
        self.client_config = {
            "web": {
                "client_id": st.secrets.get("GOOGLE_CLIENT_ID", ""),
                "client_secret": st.secrets.get("GOOGLE_CLIENT_SECRET", ""),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8501"]
            }
        }
        
    def authenticate(self):
        """Autentica con Google Search Console"""
        if 'credentials' not in st.session_state:
            st.warning("⚠️ Configurazione OAuth richiesta")
            st.info("""
            **Setup richiesto:**
            1. Vai su Google Cloud Console
            2. Abilita Search Console API
            3. Crea credenziali OAuth 2.0
            4. Aggiungi le credenziali in secrets.toml
            """)
            return False
            
        # Simulazione per demo - in produzione usare OAuth flow completo
        st.session_state.authenticated = True
        return True
        
    def get_properties(self) -> List[str]:
        """Ottieni lista proprietà GSC"""
        # Demo data - sostituire con chiamata API reale
        return [
            "https://example.com/",
            "https://blog.example.com/",
            "https://shop.example.com/"
        ]
        
    def get_search_analytics(self, property_url: str, start_date: str, end_date: str, 
                           dimensions: List[str] = None, filters: List[Dict] = None) -> pd.DataFrame:
        """Ottieni dati analytics da GSC"""
        # Demo data - sostituire con chiamata API reale
        import random
        from datetime import datetime, timedelta
        
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        data = []
        
        for date in dates:
            for i in range(random.randint(10, 50)):
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'query': f"keyword {i}",
                    'page': f"https://example.com/page-{i}",
                    'clicks': random.randint(1, 100),
                    'impressions': random.randint(100, 1000),
                    'ctr': random.uniform(0.01, 0.15),
                    'position': random.uniform(1, 50)
                })
        
        return pd.DataFrame(data)
    
    def get_index_status(self, property_url: str) -> Dict:
        """Ottieni stato indicizzazione"""
        # Demo data
        return {
            'total_pages': 1250,
            'indexed_pages': 1180,
            'not_indexed': 70,
            'errors': 15,
            'warnings': 25
        }
    
    def get_performance_summary(self, property_url: str, days: int = 30) -> Dict:
        """Ottieni riassunto performance"""
        # Demo data
        return {
            'total_clicks': 15420,
            'total_impressions': 234560,
            'avg_ctr': 6.57,
            'avg_position': 8.3,
            'keywords_count': 2340
        }

class AIAnalyzer:
    def __init__(self):
        self.client = None
        if st.secrets.get("OPENAI_API_KEY"):
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            
    def analyze_data(self, data: pd.DataFrame, query: str) -> str:
        """Analizza dati con OpenAI"""
        if not st.secrets.get("OPENAI_API_KEY"):
            return "⚠️ OpenAI API key non configurata. Aggiungi OPENAI_API_KEY in secrets.toml"
            
        # Prepara summary dei dati
        summary = self._prepare_data_summary(data)
        
        prompt = f"""
        Sei un esperto di SEO e digital marketing. Analizza i seguenti dati di Google Search Console:

        {summary}

        Domanda dell'utente: {query}

        Fornisci un'analisi dettagliata e actionable insights in italiano.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Sei un esperto SEO analyst che fornisce insights basati su dati."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Errore nell'analisi AI: {str(e)}"
    
    def _prepare_data_summary(self, data: pd.DataFrame) -> str:
        """Prepara summary dei dati per l'AI"""
        if data.empty:
            return "Nessun dato disponibile"
            
        summary = f"""
        Periodo analizzato: {data['date'].min()} - {data['date'].max()}
        Total clicks: {data['clicks'].sum():,}
        Total impressions: {data['impressions'].sum():,}
        CTR medio: {data['ctr'].mean():.2%}
        Posizione media: {data['position'].mean():.1f}
        Query uniche: {data['query'].nunique()}
        Top 5 query per clicks: {data.groupby('query')['clicks'].sum().sort_values(ascending=False).head().to_dict()}
        """
        return summary

def main():
    st.title("🔍 Google Search Console Analytics Dashboard")
    st.markdown("---")
    
    # Inizializza classi
    gsc = GSCAnalytics()
    ai_analyzer = AIAnalyzer()
    
    # Sidebar per configurazione
    st.sidebar.header("⚙️ Configurazione")
    
    # Autenticazione
    if not gsc.authenticate():
        st.stop()
    
    # Selezione proprietà
    properties = gsc.get_properties()
    selected_property = st.sidebar.selectbox(
        "Seleziona Proprietà",
        properties,
        help="Scegli la proprietà GSC da analizzare"
    )
    
    # Selezione date
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Data inizio",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now()
        )
    with col2:
        end_date = st.date_input(
            "Data fine",
            value=datetime.now(),
            max_value=datetime.now()
        )
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔍 Performance", "📈 Indexing", "🤖 AI Analysis"])
    
    with tab1:
        st.header("📊 Overview Performance")
        
        # Metriche principali
        perf_data = gsc.get_performance_summary(selected_property)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Clicks", f"{perf_data['total_clicks']:,}")
        with col2:
            st.metric("Total Impressions", f"{perf_data['total_impressions']:,}")
        with col3:
            st.metric("CTR Medio", f"{perf_data['avg_ctr']:.2f}%")
        with col4:
            st.metric("Posizione Media", f"{perf_data['avg_position']:.1f}")
        
        # Grafici
        data = gsc.get_search_analytics(
            selected_property, 
            start_date.strftime('%Y-%m-%d'), 
            end_date.strftime('%Y-%m-%d')
        )
        
        if not data.empty:
            # Trend giornaliero
            daily_data = data.groupby('date').agg({
                'clicks': 'sum',
                'impressions': 'sum',
                'ctr': 'mean'
            }).reset_index()
            
            fig = px.line(daily_data, x='date', y=['clicks', 'impressions'], 
                         title="Trend Clicks vs Impressions")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("🔍 Analisi Performance Dettagliata")
        
        if not data.empty:
            # Top queries
            st.subheader("Top Query per Clicks")
            top_queries = data.groupby('query').agg({
                'clicks': 'sum',
                'impressions': 'sum',
                'ctr': 'mean',
                'position': 'mean'
            }).sort_values('clicks', ascending=False).head(10)
            
            st.dataframe(top_queries.style.format({
                'clicks': '{:,}',
                'impressions': '{:,}',
                'ctr': '{:.2%}',
                'position': '{:.1f}'
            }))
            
            # Distribuzione posizioni
            st.subheader("Distribuzione Posizioni")
            fig = px.histogram(data, x='position', bins=20, title="Distribuzione Posizioni SERP")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("📈 Stato Indicizzazione")
        
        index_data = gsc.get_index_status(selected_property)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pagine Totali", f"{index_data['total_pages']:,}")
        with col2:
            st.metric("Pagine Indicizzate", f"{index_data['indexed_pages']:,}")
        with col3:
            st.metric("Non Indicizzate", f"{index_data['not_indexed']:,}")
        
        # Grafico a torta
        fig = go.Figure(data=[go.Pie(
            labels=['Indicizzate', 'Non Indicizzate', 'Errori'],
            values=[index_data['indexed_pages'], index_data['not_indexed'], index_data['errors']]
        )])
        fig.update_layout(title="Stato Indicizzazione")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.header("🤖 Analisi AI")
        
        # Input per domande AI
        user_query = st.text_area(
            "Fai una domanda sui tuoi dati GSC:",
            placeholder="Es: Quanto traffico di brand abbiamo ottenuto negli ultimi 3 mesi rispetto ai 3 mesi precedenti?",
            height=100
        )
        
        if st.button("🔍 Analizza con AI", type="primary"):
            if user_query:
                with st.spinner("Analizzando i dati..."):
                    analysis = ai_analyzer.analyze_data(data, user_query)
                    st.write(analysis)
            else:
                st.warning("Inserisci una domanda per l'analisi")
        
        # Suggerimenti di domande
        st.subheader("💡 Domande Suggerite")
        suggestions = [
            "Quali sono le query con il miglior potenziale di crescita?",
            "Come sta performando il traffico branded vs non-branded?",
            "Quali pagine hanno perso più traffico nell'ultimo mese?",
            "Identifica opportunità di ottimizzazione basate sui dati CTR",
            "Analizza la cannibalizzazione delle keyword"
        ]
        
        for suggestion in suggestions:
            if st.button(f"❓ {suggestion}", key=suggestion):
                with st.spinner("Analizzando..."):
                    analysis = ai_analyzer.analyze_data(data, suggestion)
                    st.write(analysis)

if __name__ == "__main__":
    main()
