"""
Modulo per l'analisi AI dei dati GSC
"""

import pandas as pd
import streamlit as st
import openai
from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta

class AIAnalyzer:
    """Analyzer AI per dati Google Search Console"""
    
    def __init__(self):
        self.client = None
        self.setup_openai()
        
    def setup_openai(self):
        """Configura OpenAI client"""
        if st.secrets.get("OPENAI_API_KEY"):
            openai.api_key = st.secrets["OPENAI_API_KEY"]
        else:
            st.warning("⚠️ OpenAI API key non configurata")
    
    def analyze_data(self, data: pd.DataFrame, query: str, context: Dict = None) -> str:
        """Analizza i dati con OpenAI"""
        if not st.secrets.get("OPENAI_API_KEY"):
            return self._generate_fallback_analysis(data, query)
        
        try:
            # Prepara il contesto dei dati
            data_summary = self._prepare_data_summary(data)
            
            # Aggiungi contesto aggiuntivo se fornito
            context_info = ""
            if context:
                context_info = f"\nContesto aggiuntivo: {json.dumps(context, indent=2)}"
            
            # Costruisci il prompt
            prompt = f"""
            Sei un esperto SEO analyst e digital marketer. Analizza i seguenti dati di Google Search Console e fornisci insights actionable in italiano.

            DATI GOOGLE SEARCH CONSOLE:
            {data_summary}
            {context_info}

            DOMANDA/RICHIESTA DELL'UTENTE:
            {query}

            ISTRUZIONI:
            1. Fornisci un'analisi dettagliata e specifica
            2. Identifica trends, opportunità e problemi
            3. Suggerisci azioni concrete e misurabili
            4. Usa un linguaggio professionale ma comprensibile
            5. Includi metriche specifiche quando possibile
            6. Struttura la risposta in modo chiaro con sezioni
            
            STRUTTURA RISPOSTA:
            📊 **Analisi dei Dati**
            🔍 **Insights Chiave**
            💡 **Raccomandazioni**
            📈 **Prossimi Passi**
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "Sei un esperto SEO analyst che fornisce insights basati su dati concreti. Rispondi sempre in italiano con analisi dettagliate e actionable."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Errore nell'analisi AI: {str(e)}\n\n{self._generate_fallback_analysis(data, query)}"
    
    def _prepare_data_summary(self, data: pd.DataFrame) -> str:
        """Prepara un riassunto dei dati per l'AI"""
        if data.empty:
            return "⚠️ Nessun dato disponibile per l'analisi"
        
        summary_parts = []
        
        # Informazioni generali
        summary_parts.append(f"📅 Periodo: {data['date'].min()} - {data['date'].max()}" if 'date' in data.columns else "")
        summary_parts.append(f"📊 Righe di dati: {len(data):,}")
        
        # Metriche principali
        if 'clicks' in data.columns:
            summary_parts.append(f"🖱️ Click totali: {data['clicks'].sum():,}")
        if 'impressions' in data.columns:
            summary_parts.append(f"👁️ Impressioni totali: {data['impressions'].sum():,}")
        if 'ctr' in data.columns:
            summary_parts.append(f"📊 CTR medio: {data['ctr'].mean():.2%}")
        if 'position' in data.columns:
            summary_parts.append(f"📍 Posizione media: {data['position'].mean():.1f}")
        
        # Analisi per query
        if 'query' in data.columns:
            top_queries = data.groupby('query')['clicks'].sum().sort_values(ascending=False).head(10)
            summary_parts.append(f"🔍 Query uniche: {data['query'].nunique():,}")
            summary_parts.append(f"🏆 Top 5 query per click: {top_queries.head().to_dict()}")
        
        # Analisi per pagina
        if 'page' in data.columns:
            top_pages = data.groupby('page')['clicks'].sum().sort_values(ascending=False).head(5)
            summary_parts.append(f"📄 Pagine uniche: {data['page'].nunique():,}")
            summary_parts.append(f"🏆 Top 5 pagine per click: {top_pages.to_dict()}")
        
        # Trend temporali
        if 'date' in data.columns:
            daily_data = data.groupby('date').agg({
                'clicks': 'sum',
                'impressions': 'sum' if 'impressions' in data.columns else 'count'
            }).reset_index()
            
            if len(daily_data) > 1:
                recent_avg = daily_data.tail(7)['clicks'].mean()
                older_avg = daily_data.head(7)['clicks'].mean()
                trend = "📈 Crescita" if recent_avg > older_avg else "📉 Calo"
                summary_parts.append(f"📊 Trend recente: {trend} ({recent_avg:.0f} vs {older_avg:.0f} click medi)")
        
        return "\n".join(filter(None, summary_parts))
    
    def _generate_fallback_analysis(self, data: pd.DataFrame, query: str) -> str:
        """Genera un'analisi base senza AI"""
        if data.empty:
            return "⚠️ Nessun dato disponibile per l'analisi richiesta."
        
        analysis = "📊 **Analisi Automatica dei Dati**\n\n"
        
        # Metriche base
        if 'clicks' in data.columns:
            total_clicks = data['clicks'].sum()
            analysis += f"🖱️ **Click totali**: {total_clicks:,}\n"
        
        if 'impressions' in data.columns:
            total_impressions = data['impressions'].sum()
            analysis += f"👁️ **Impressioni totali**: {total_impressions:,}\n"
        
        if 'ctr' in data.columns:
            avg_ctr = data['ctr'].mean()
            analysis += f"📊 **CTR medio**: {avg_ctr:.2%}\n"
        
        if 'position' in data.columns:
            avg_position = data['position'].mean()
            analysis += f"📍 **Posizione media**: {avg_position:.1f}\n"
        
        # Top performers
        if 'query' in data.columns:
            top_queries = data.groupby('query')['clicks'].sum().sort_values(ascending=False).head(5)
            analysis += f"\n🏆 **Top 5 Query per Click**:\n"
            for query, clicks in top_queries.items():
                analysis += f"• {query}: {clicks:,} click\n"
        
        analysis += "\n💡 **Raccomandazione**: Configura OpenAI API per analisi avanzate personalizzate."
        
        return analysis
    
    def get_suggested_queries(self) -> List[str]:
        """Ottieni query suggerite per l'analisi"""
        return [
            "Quanto traffico di brand abbiamo ottenuto negli ultimi 3 mesi rispetto ai 3 mesi precedenti?",
            "Quali sono le query con il miglior potenziale di crescita?",
            "Come sta performando il traffico branded vs non-branded?",
            "Quali pagine hanno perso più traffico nell'ultimo mese?",
            "Identifica opportunità di ottimizzazione basate sui dati CTR",
            "Analizza la cannibalizzazione delle keyword",
            "Quali query hanno posizione media alta ma CTR basso?",
            "Identifica le pagine con maggior potenziale di miglioramento",
            "Come si distribuisce il traffico per device (mobile vs desktop)?",
            "Quali sono i trend stagionali del nostro traffico organico?"
        ]
    
    def analyze_competitors(self, our_data: pd.DataFrame, competitor_keywords: List[str]) -> str:
        """Analizza la competizione per keyword specifiche"""
        if not competitor_keywords:
            return "⚠️ Nessuna keyword competitor specificata"
        
        # Filtra i dati per keyword competitor
        competitor_data = our_data[
            our_data['query'].str.contains('|'.join(competitor_keywords), case=False, na=False)
        ] if 'query' in our_data.columns else pd.DataFrame()
        
        if competitor_data.empty:
            return f"ℹ️ Nessun dato trovato per le keyword competitor: {', '.join(competitor_keywords)}"
        
        analysis = "🏆 **Analisi Competitiva**\n\n"
        
        total_clicks = competitor_data['clicks'].sum()
        avg_position = competitor_data['position'].mean()
        
        analysis += f"📊 **Metriche Competitor Keywords**:\n"
        analysis += f"• Click totali: {total_clicks:,}\n"
        analysis += f"• Posizione media: {avg_position:.1f}\n"
        analysis += f"• Query monitorate: {len(competitor_data)}\n"
        
        # Top performing competitor keywords
        if len(competitor_data) > 0:
            top_competitor_queries = competitor_data.groupby('query')['clicks'].sum().sort_values(ascending=False).head(5)
            analysis += f"\n🎯 **Top Competitor Keywords**:\n"
            for query, clicks in top_competitor_queries.items():
                analysis += f"• {query}: {clicks:,} click\n"
        
        return analysis
    
    def generate_report(self, data: pd.DataFrame, period: str = "monthly") -> str:
        """Genera un report completo"""
        if data.empty:
            return "⚠️ Nessun dato disponibile per il report"
        
        report = f"📋 **Report {period.title()} - Google Search Console**\n\n"
        
        # Executive Summary
        report += "## 📊 Executive Summary\n\n"
        
        if 'clicks' in data.columns and 'impressions' in data.columns:
            total_clicks = data['clicks'].sum()
            total_impressions = data['impressions'].sum()
            avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            
            report += f"• **Performance**: {total_clicks:,} click da {total_impressions:,} impressioni\n"
            report += f"• **CTR**: {avg_ctr:.2f}%\n"
        
        if 'position' in data.columns:
            avg_position = data['position'].mean()
            report += f"• **Posizione Media**: {avg_position:.1f}\n"
        
        if 'query' in data.columns:
            unique_queries = data['query'].nunique()
            report += f"• **Query Monitorate**: {unique_queries:,}\n"
        
        report += "\n💡 **Raccomandazione**: Utilizza l'analisi AI per insights più dettagliati e actionable.\n"
        
        return report
