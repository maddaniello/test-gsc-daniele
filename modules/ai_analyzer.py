"""
Modulo per l'analisi AI dei dati GSC
"""

import streamlit as st
import pandas as pd
import openai
from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta

class AIAnalyzer:
    """Analizzatore AI per i dati di Google Search Console"""
    
    def __init__(self):
        self.client = None
        self.setup_openai()
        
    def setup_openai(self):
        """Configura OpenAI"""
        try:
            api_key = st.secrets.get("OPENAI_API_KEY")
            if api_key:
                openai.api_key = api_key
                self.client = openai
            else:
                st.warning("⚠️ OpenAI API key non configurata")
        except Exception as e:
            st.error(f"Errore configurazione OpenAI: {str(e)}")
    
    def analyze_traffic_trends(self, data: pd.DataFrame, period_days: int = 30) -> str:
        """Analizza i trend del traffico"""
        if data.empty or not self.client:
            return "Dati non disponibili per l'analisi"
        
        # Prepara i dati per l'analisi
        daily_data = data.groupby('date').agg({
            'clicks': 'sum',
            'impressions': 'sum',
            'ctr': 'mean',
            'position': 'mean'
        }).reset_index()
        
        # Calcola statistiche
        stats = {
            'total_clicks': daily_data['clicks'].sum(),
            'avg_daily_clicks': daily_data['clicks'].mean(),
            'clicks_trend': self._calculate_trend(daily_data['clicks']),
            'ctr_avg': daily_data['ctr'].mean(),
            'position_avg': daily_data['position'].mean(),
            'best_day': daily_data.loc[daily_data['clicks'].idxmax(), 'date'].strftime('%Y-%m-%d'),
            'worst_day': daily_data.loc[daily_data['clicks'].idxmin(), 'date'].strftime('%Y-%m-%d')
        }
        
        prompt = f"""
        Analizza questi dati di traffico SEO per gli ultimi {period_days} giorni:
        
        📊 STATISTICHE PRINCIPALI:
        - Clicks totali: {stats['total_clicks']:,}
        - Clicks medi giornalieri: {stats['avg_daily_clicks']:.0f}
        - Trend clicks: {stats['clicks_trend']}
        - CTR medio: {stats['ctr_avg']:.2%}
        - Posizione media: {stats['position_avg']:.1f}
        - Giorno migliore: {stats['best_day']}
        - Giorno peggiore: {stats['worst_day']}
        
        Fornisci un'analisi dettagliata in italiano che includa:
        1. Valutazione delle performance generali
        2. Identificazione di pattern e trend
        3. Possibili cause dei picchi/cali
        4. Raccomandazioni actionable per migliorare
        
        Usa un tono professionale ma accessibile.
        """
        
        return self._get_ai_response(prompt)
    
    def analyze_keyword_opportunities(self, data: pd.DataFrame, min_impressions: int = 100) -> str:
        """Analizza opportunità di keyword"""
        if data.empty or not self.client:
            return "Dati non disponibili per l'analisi"
        
        # Filtra e analizza le query
        query_data = data.groupby('query').agg({
            'clicks': 'sum',
            'impressions': 'sum',
            'ctr': 'mean',
            'position': 'mean'
        }).reset_index()
        
        # Identifica opportunità
        opportunities = query_data[
            (query_data['impressions'] >= min_impressions) &
            (query_data['position'] > 3) &
            (query_data['ctr'] < 0.05)
        ].sort_values('impressions', ascending=False).head(10)
        
        high_potential = query_data[
            (query_data['position'] <= 10) &
            (query_data['position'] > 3) &
            (query_data['impressions'] >= min_impressions)
        ].sort_values(['impressions', 'position'], ascending=[False, True]).head(10)
        
        opportunities_text = opportunities[['query', 'impressions', 'position', 'ctr']].to_string(index=False)
        high_potential_text = high_potential[['query', 'impressions', 'position', 'ctr']].to_string(index=False)
        
        prompt = f"""
        Analizza queste opportunità di keyword SEO:
        
        🎯 QUERY CON BASSO CTR MA ALTE IMPRESSIONI:
        {opportunities_text}
        
        🚀 QUERY AD ALTO POTENZIALE (posizione 4-10):
        {high_potential_text}
        
        Fornisci un'analisi che includa:
        1. Prioritizzazione delle opportunità
        2. Strategie specifiche per migliorare il ranking
        3. Stima del potenziale traffico aggiuntivo
        4. Azioni concrete da implementare
        
        Rispondi in italiano con suggerimenti pratici.
        """
        
        return self._get_ai_response(prompt)
    
    def analyze_content_performance(self, data: pd.DataFrame) -> str:
        """Analizza performance dei contenuti"""
        if data.empty or not self.client:
            return "Dati non disponibili per l'analisi"
        
        # Analizza le pagine
        page_data = data.groupby('page').agg({
            'clicks': 'sum',
            'impressions': 'sum',
            'ctr': 'mean',
            'position': 'mean'
        }).reset_index()
        
        # Identifica top e bottom performers
        top_pages = page_data.nlargest(10, 'clicks')[['page', 'clicks', 'impressions', 'ctr', 'position']]
        bottom_pages = page_data[page_data['clicks'] > 0].nsmallest(10, 'ctr')[['page', 'clicks', 'impressions', 'ctr', 'position']]
        
        prompt = f"""
        Analizza le performance dei contenuti:
        
        🏆 TOP 10 PAGINE PER CLICKS:
        {top_pages.to_string(index=False)}
        
        ⚠️ PAGINE CON BASSO CTR:
        {bottom_pages.to_string(index=False)}
        
        Fornisci un'analisi che includa:
        1. Valutazione delle pagine top performer
        2. Identificazione di problemi nelle pagine con basso CTR
        3. Suggerimenti per ottimizzare i contenuti
        4. Strategie per migliorare la user experience
        
        Rispondi in italiano con consigli pratici.
        """
        
        return self._get_ai_response(prompt)
    
    def compare_periods(self, current_data: pd.DataFrame, previous_data: pd.DataFrame) -> str:
        """Confronta due periodi di dati"""
        if current_data.empty or previous_data.empty or not self.client:
            return "Dati non disponibili per il confronto"
        
        # Calcola metriche per entrambi i periodi
        current_stats = self._calculate_period_stats(current_data)
        previous_stats = self._calculate_period_stats(previous_data)
        
        # Calcola variazioni
        changes = {}
        for key in current_stats:
            if key in previous_stats and previous_stats[key] != 0:
                change = ((current_stats[key] - previous_stats[key]) / previous_stats[key]) * 100
                changes[key] = change
        
        prompt = f"""
        Confronto tra due periodi di dati SEO:
        
        📊 PERIODO CORRENTE:
        - Clicks: {current_stats['clicks']:,}
        - Impressions: {current_stats['impressions']:,}
        - CTR: {current_stats['ctr']:.2%}
        - Posizione media: {current_stats['position']:.1f}
        
        📊 PERIODO PRECEDENTE:
        - Clicks: {previous_stats['clicks']:,}
        - Impressions: {previous_stats['impressions']:,}
        - CTR: {previous_stats['ctr']:.2%}
        - Posizione media: {previous_stats['position']:.1f}
        
        📈 VARIAZIONI:
        - Clicks: {changes.get('clicks', 0):+.1f}%
        - Impressions: {changes.get('impressions', 0):+.1f}%
        - CTR: {changes.get('ctr', 0):+.1f}%
        - Posizione: {changes.get('position', 0):+.1f}%
        
        Fornisci un'analisi che includa:
        1. Valutazione delle performance complessive
        2. Identificazione di trend positivi/negativi
        3. Possibili cause dei cambiamenti
        4. Raccomandazioni per il futuro
        
        Rispondi in italiano con insights actionable.
        """
        
        return self._get_ai_response(prompt)
    
    def analyze_branded_traffic(self, data: pd.DataFrame, brand_keywords: List[str]) -> str:
        """Analizza il traffico branded vs non-branded"""
        if data.empty or not self.client:
            return "Dati non disponibili per l'analisi"
        
        # Classifica le query
        brand_pattern = '|'.join([kw.lower() for kw in brand_keywords])
        data['is_branded'] = data['query'].str.lower().str.contains(brand_pattern, na=False)
        
        # Calcola statistiche
        branded_stats = data[data['is_branded']].agg({
            'clicks': 'sum',
            'impressions': 'sum',
            'ctr': 'mean',
            'position': 'mean'
        })
        
        nonbranded_stats = data[~data['is_branded']].agg({
            'clicks': 'sum',
            'impressions': 'sum',
            'ctr': 'mean',
            'position': 'mean'
        })
        
        total_clicks = branded_stats['clicks'] + nonbranded_stats['clicks']
        branded_percentage = (branded_stats['clicks'] / total_clicks * 100) if total_clicks > 0 else 0
        
        prompt = f"""
        Analisi del traffico branded vs non-branded:
        
        🏷️ TRAFFICO BRANDED:
        - Clicks: {branded_stats['clicks']:,} ({branded_percentage:.1f}%)
        - Impressions: {branded_stats['impressions']:,}
        - CTR: {branded_stats['ctr']:.2%}
        - Posizione media: {branded_stats['position']:.1f}
        
        🔍 TRAFFICO NON-BRANDED:
        - Clicks: {nonbranded_stats['clicks']:,} ({100-branded_percentage:.1f}%)
        - Impressions: {nonbranded_stats['impressions']:,}
        - CTR: {nonbranded_stats['ctr']:.2%}
        - Posizione media: {nonbranded_stats['position']:.1f}
        
        Brand keywords analizzate: {', '.join(brand_keywords)}
        
        Fornisci un'analisi che includa:
        1. Valutazione del brand awareness
        2. Opportunità di crescita nel traffico non-branded
        3. Strategie per bilanciare branded/non-branded
        4. Raccomandazioni per la brand strategy
        
        Rispondi in italiano con insights strategici.
        """
        
        return self._get_ai_response(prompt)
    
    def custom_analysis(self, data: pd.DataFrame, user_query: str) -> str:
        """Analisi personalizzata basata su query utente"""
        if data.empty or not self.client:
            return "Dati non disponibili per l'analisi"
        
        # Prepara summary dei dati
        data_summary = self._prepare_data_summary(data)
        
        prompt = f"""
        Dati di Google Search Console:
        {data_summary}
        
        Domanda specifica dell'utente: {user_query}
        
        Fornisci un'analisi dettagliata che risponda alla domanda specifica.
        Includi dati numerici quando possibile e suggerimenti actionable.
        Rispondi in italiano in modo professionale e chiaro.
        """
        
        return self._get_ai_response(prompt)
    
    def _get_ai_response(self, prompt: str) -> str:
        """Ottieni risposta da OpenAI"""
        try:
            response = self.client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "Sei un esperto consulente SEO e digital marketing. Fornisci sempre analisi dettagliate, basate sui dati e con suggerimenti pratici. Usa un linguaggio professionale ma accessibile."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Errore nell'analisi AI: {str(e)}"
    
    def _prepare_data_summary(self, data: pd.DataFrame) -> str:
        """Prepara summary dei dati"""
        if data.empty:
            return "Nessun dato disponibile"
        
        # Calcola statistiche di base
        stats = {
            'total_clicks': data['clicks'].sum(),
            'total_impressions': data['impressions'].sum(),
            'avg_ctr': data['ctr'].mean(),
            'avg_position': data['position'].mean(),
            'unique_queries': data['query'].nunique() if 'query' in data.columns else 0,
            'unique_pages': data['page'].nunique() if 'page' in data.columns else 0,
            'date_range': f"{data['date'].min()} - {data['date'].max()}" if 'date' in data.columns else "N/A"
        }
        
        # Top performers
        top_queries = ""
        if 'query' in data.columns:
            top_q = data.groupby('query')['clicks'].sum().sort_values(ascending=False).head(5)
            top_queries = ", ".join([f"{q}: {clicks}" for q, clicks in top_q.items()])
        
        summary = f"""
        📊 RIEPILOGO DATI:
        - Periodo: {stats['date_range']}
        - Clicks totali: {stats['total_clicks']:,}
        - Impressions totali: {stats['total_impressions']:,}
        - CTR medio: {stats['avg_ctr']:.2%}
        - Posizione media: {stats['avg_position']:.1f}
        - Query uniche: {stats['unique_queries']:,}
        - Pagine uniche: {stats['unique_pages']:,}
        - Top 5 query per clicks: {top_queries}
        """
        
        return summary
    
    def _calculate_trend(self, series: pd.Series) -> str:
        """Calcola il trend di una serie temporale"""
        if len(series) < 2:
            return "Dati insufficienti"
        
        # Calcola la pendenza usando regressione lineare semplice
        x = range(len(series))
        y = series.values
        
        # Correlazione di Pearson come indicatore di trend
        correlation = pd.Series(x).corr(pd.Series(y))
        
        if correlation > 0.3:
            return "Crescente"
        elif correlation < -0.3:
            return "Decrescente"
        else:
            return "Stabile"
    
    def _calculate_period_stats(self, data: pd.DataFrame) -> Dict:
        """Calcola statistiche per un periodo"""
        return {
            'clicks': data['clicks'].sum(),
            'impressions': data['impressions'].sum(),
            'ctr': data['ctr'].mean(),
            'position': data['position'].mean()
        }
