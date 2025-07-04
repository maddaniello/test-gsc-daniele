"""
Modulo per l'autenticazione con Google Search Console
"""

import streamlit as st
import json
import os
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle

class GSCAuthenticator:
    """Gestisce l'autenticazione con Google Search Console"""
    
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
        self.credentials = None
        self.service = None
        
    def setup_oauth_flow(self) -> Optional[Flow]:
        """Configura il flusso OAuth"""
        try:
            client_config = {
                "web": {
                    "client_id": st.secrets["GOOGLE_CLIENT_ID"],
                    "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [st.secrets.get("redirect_uri", "http://localhost:8501")]
                }
            }
            
            flow = Flow.from_client_config(
                client_config,
                scopes=self.SCOPES,
                redirect_uri=st.secrets.get("redirect_uri", "http://localhost:8501")
            )
            
            return flow
            
        except Exception as e:
            st.error(f"Errore nella configurazione OAuth: {str(e)}")
            return None
    
    def get_authorization_url(self) -> Optional[str]:
        """Ottieni URL di autorizzazione"""
        flow = self.setup_oauth_flow()
        if flow:
            auth_url, _ = flow.authorization_url(prompt='consent')
            return auth_url
        return None
    
    def handle_oauth_callback(self, authorization_code: str) -> bool:
        """Gestisce il callback OAuth"""
        try:
            flow = self.setup_oauth_flow()
            if not flow:
                return False
                
            flow.fetch_token(code=authorization_code)
            self.credentials = flow.credentials
            
            # Salva le credenziali
            self.save_credentials()
            
            return True
            
        except Exception as e:
            st.error(f"Errore nell'autenticazione: {str(e)}")
            return False
    
    def save_credentials(self):
        """Salva le credenziali"""
        if self.credentials:
            creds_data = {
                'token': self.credentials.token,
                'refresh_token': self.credentials.refresh_token,
                'token_uri': self.credentials.token_uri,
                'client_id': self.credentials.client_id,
                'client_secret': self.credentials.client_secret,
                'scopes': self.credentials.scopes
            }
            st.session_state['gsc_credentials'] = creds_data
    
    def load_credentials(self) -> bool:
        """Carica le credenziali salvate"""
        if 'gsc_credentials' in st.session_state:
            creds_data = st.session_state['gsc_credentials']
            
            self.credentials = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data['refresh_token'],
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
                scopes=creds_data['scopes']
            )
            
            # Verifica se il token è valido
            if self.credentials.expired:
                try:
                    self.credentials.refresh(Request())
                    self.save_credentials()
                except Exception as e:
                    st.error(f"Errore nel refresh del token: {str(e)}")
                    return False
            
            return True
        
        return False
    
    def get_service(self):
        """Ottieni il servizio GSC"""
        if self.credentials and not self.service:
            self.service = build('searchconsole', 'v1', credentials=self.credentials)
        return self.service
    
    def is_authenticated(self) -> bool:
        """Verifica se l'utente è autenticato"""
        return self.credentials is not None and not self.credentials.expired
    
    def logout(self):
        """Logout dell'utente"""
        self.credentials = None
        self.service = None
        if 'gsc_credentials' in st.session_state:
            del st.session_state['gsc_credentials']
