"""
Modulo per la gestione dei dati di Google Search Console
"""

import pandas as pd
import streamlit as st
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError

class GSCDataManager:
    """Gestisce i dati di Google Search Console"""
    
    def __init__(self, service):
        self.service = service
        
    def get_properties(self) -> List[Dict]:
        """Ottieni lista delle proprietà GSC"""
        try:
            sites = self.service.sites().list().execute()
            properties = []
            
            for site in sites.get('siteEntry', []):
                properties.append({
                    'url': site['siteUrl'],
                    'permission': site['permissionLevel']
                })
            
            return properties
            
        except HttpError as e:
            st.error(f"Errore nel recupero delle proprietà: {str(e)}")
            return []
    
    def get_search_analytics(self, 
                           property_url: str, 
                           start_date: str, 
                           end_date: str,
                           dimensions: List[str] = None,
                           row_limit: int = 5000,
                           filters: List[Dict] = None) -> pd.DataFrame:
        """Ottieni dati di analytics da GSC"""
        
        if dimensions is None:
            dimensions = ['date', 'query']
        
        request_body = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': dimensions,
            'rowLimit': row_limit,
            'startRow': 0
        }
        
        if filters:
            request_body['dimensionFilterGroups'] = [{'filters': filters}]
        
        try:
            response = self.service.searchanalytics().query(
                siteUrl=property_url,
                body=request_body
            ).execute()
            
            # Converte la risposta in DataFrame
            rows = response.get('rows', [])
            if not rows:
                return pd.DataFrame()
            
            data = []
            for row in rows:
                row_data = dict(zip(dimensions, row['keys']))
                row_data.update({
                    'clicks': row['clicks'],
                    'impressions': row['impressions'],
                    'ctr': row['ctr'],
                    'position': row['position']
                })
                data.append(row_data)
            
            df = pd.DataFrame(data)
            
            # Converti la colonna date se presente
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            return df
            
        except HttpError as e:
            st.error(f"Errore nel recupero dei dati analytics: {str(e)}")
            return pd.DataFrame()
    
    def get_index_coverage(self, property_url: str) -> Dict:
        """Ottieni dati di copertura dell'indice"""
        try:
            # Endpoint per la copertura dell'indice
            request = self.service.sites().get(siteUrl=property_url)
            response = request.execute()
            
            # Nota: L'API GSC non fornisce direttamente dati di copertura
            # Questo è un esempio della struttura che potresti ottenere
            # In realtà dovrai usare altri endpoint o analizzare i dati diversamente
            
            return {
                'site_url': response.get('siteUrl', ''),
                'verification_status': response.get('verificationStatus', ''),
                'permission_level': response.get('permissionLevel', '')
            }
            
        except HttpError as e:
            st.error(f"Errore nel recupero della copertura: {str(e)}")
            return {}
    
    def get_sitemaps(self, property_url: str) -> List[Dict]:
        """Ottieni informazioni sulle sitemap"""
        try:
            response = self.service.sitemaps().list(siteUrl=property_url).execute()
            
            sitemaps = []
            for sitemap in response.get('sitemap', []):
                sitemaps.append({
                    'path': sitemap.get('path', ''),
                    'lastSubmitted': sitemap.get('lastSubmitted', ''),
                    'lastDownloaded': sitemap.get('lastDownloaded', ''),
                    'isPending': sitemap.get('isPending', False),
                    'isSitemapsIndex': sitemap.get('isSitemapsIndex', False),
                    'type': sitemap.get('type', ''),
                    'warnings': sitemap.get('warnings', 0),
                    'errors': sitemap.get('errors', 0)
                })
            
            return sitemaps
            
        except HttpError as e:
            st.error(f"Errore nel recupero delle sitemap: {str(e)}")
            return []
    
    def get_mobile_usability(self, property_url: str) -> Dict:
        """Ottieni dati di usabilità mobile"""
        # Nota: L'API GSC ha limitazioni sui dati di usabilità mobile
        # Questo è un placeholder per la struttura dei dati
        return {
            'mobile_friendly_pages': 0,
            'mobile_issues': 0,
            'total_pages': 0
        }
    
    def get_performance_summary(self, 
                              property_url: str, 
                              start_date: str, 
                              end_date: str) -> Dict:
        """Ottieni riassunto delle performance"""
        
        # Ottieni dati aggregati
        df = self.get_search_analytics(
            property_url, 
            start_date, 
            end_date,
            dimensions=['date']
        )
        
        if df.empty:
            return {
                'total_clicks': 0,
                'total_impressions': 0,
                'avg_ctr': 0,
                'avg_position': 0,
                'total_queries': 0
            }
        
        # Calcola metriche aggregate
        total_clicks = df['clicks'].sum()
        total_impressions = df['impressions'].sum()
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_position = df['position'].mean()
        
        # Ottieni conteggio query uniche
        query_df = self.get_search_analytics(
            property_url, 
            start_date, 
            end_date,
            dimensions=['query']
        )
        total_queries = len(query_df)
        
        return {
            'total_clicks': int(total_clicks),
            'total_impressions': int(total_impressions),
            'avg_ctr': round(avg_ctr, 2),
            'avg_position': round(avg_position, 1),
            'total_queries': total_queries
        }
    
    def get_top_queries(self, 
                       property_url: str, 
                       start_date: str, 
                       end_date: str,
                       limit: int = 100) -> pd.DataFrame:
        """Ottieni le top query"""
        
        df = self.get_search_analytics(
            property_url, 
            start_date, 
            end_date,
            dimensions=['query'],
            row_limit=limit
        )
        
        if not df.empty:
            df = df.sort_values('clicks', ascending=False)
        
        return df
    
    def get_top_pages(self, 
                     property_url: str, 
                     start_date: str, 
                     end_date: str,
                     limit: int = 100) -> pd.DataFrame:
        """Ottieni le top pagine"""
        
        df = self.get_search_analytics(
            property_url, 
            start_date, 
            end_date,
            dimensions=['page'],
            row_limit=limit
        )
        
        if not df.empty:
            df = df.sort_values('clicks', ascending=False)
        
        return df
    
    def get_branded_vs_nonbranded(self, 
                                 property_url: str, 
                                 start_date: str, 
                                 end_date: str,
                                 brand_keywords: List[str]) -> Dict:
        """Analizza traffico branded vs non-branded"""
        
        df = self.get_search_analytics(
            property_url, 
            start_date, 
            end_date,
            dimensions=['query']
        )
        
        if df.empty:
            return {'branded': 0, 'non_branded': 0}
        
        # Classifica query come branded o non-branded
        brand_pattern = '|'.join(brand_keywords)
        df['is_branded'] = df['query'].str.contains(brand_pattern, case=False, na=False)
        
        branded_clicks = df[df['is_branded']]['clicks'].sum()
        non_branded_clicks = df[~df['is_branded']]['clicks'].sum()
        
        return {
            'branded': int(branded_clicks),
            'non_branded': int(non_branded_clicks)
        }
