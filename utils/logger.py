"""
Logger Anônimo para SciPubs
Registra métricas sem dados pessoais com rotação automática
"""

import json
import os
from datetime import datetime
from pathlib import Path
import gzip
import time

class AnonymousLogger:
    """
    Logger que não rastreia dados pessoais, com rotação automática
    """
    
    LOG_DIR = "logs"
    MAX_LOG_SIZE_MB = 10
    RETENTION_DAYS = 30
    
    def __init__(self):
        Path(self.LOG_DIR).mkdir(exist_ok=True)
        self._cleanup_old_logs()
    
    def _get_log_path(self) -> str:
        """Retorna caminho do arquivo de log atual"""
        data = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.LOG_DIR, f"scipubs_{data}.jsonl")
    
    def _should_rotate(self) -> bool:
        """Verifica se arquivo de log deve rotar"""
        log_path = self._get_log_path()
        
        if not os.path.exists(log_path):
            return False
        
        size_mb = os.path.getsize(log_path) / (1024 * 1024)
        return size_mb > self.MAX_LOG_SIZE_MB
    
    def _rotate_log(self):
        """Compacta e renomeia arquivo de log cheio"""
        log_path = self._get_log_path()
        
        if not os.path.exists(log_path):
            return
        
        timestamp = datetime.now().strftime("%H-%M-%S")
        rotated_path = log_path.replace(".jsonl", f"_{timestamp}.jsonl.gz")
        
        try:
            with open(log_path, 'rb') as f_in:
                with gzip.open(rotated_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            os.remove(log_path)
            print(f"📦 Log rotacionado: {rotated_path}")
        except Exception as e:
            print(f"❌ Erro ao rotar log: {e}")
    
    def _cleanup_old_logs(self):
        """Remove logs mais antigos que RETENTION_DAYS"""
        cutoff_time = time.time() - (self.RETENTION_DAYS * 86400)
        
        for filename in os.listdir(self.LOG_DIR):
            filepath = os.path.join(self.LOG_DIR, filename)
            
            if os.path.getmtime(filepath) < cutoff_time:
                try:
                    os.remove(filepath)
                    print(f"🗑️  Log antigo removido: {filename}")
                except Exception as e:
                    print(f"❌ Erro ao remover log antigo: {e}")
    
    def log_recommendation(self,
                          area_conhecimento: str,
                          tempo_resposta_segundos: float,
                          num_resultados: int,
                          sucesso: bool,
                          idioma: str = "Português",
                          backend: str = "unknown"):
        """Log anônimo de recomendação (SEM dados pessoais)"""
        
        if self._should_rotate():
            self._rotate_log()
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tipo": "recomendacao_ia",
            "area_conhecimento": area_conhecimento,
            "tempo_resposta_seg": round(tempo_resposta_segundos, 2),
            "num_resultados": num_resultados,
            "sucesso": sucesso,
            "idioma": idioma,
            "backend": backend,
        }
        
        self._escrever_log(log_entry)
    
    def log_error(self,
                 tipo_erro: str,
                 componente: str,
                 mensagem: str,
                 backend: str = "unknown"):
        """Log de erros sem informações sensíveis"""
        
        if self._should_rotate():
            self._rotate_log()
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tipo": "erro",
            "tipo_erro": tipo_erro,
            "componente": componente,
            "mensagem": mensagem[:200],
            "backend": backend
        }
        
        self._escrever_log(log_entry)
    
    def _escrever_log(self, entry: dict):
        """Escreve entrada JSON no arquivo de log"""
        log_path = self._get_log_path()
        
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"❌ Erro ao escrever log: {e}")
    
    def get_stats(self, dias: int = 7) -> dict:
        """Retorna estatísticas agregadas dos últimos N dias"""
        stats = {
            "total_recomendacoes": 0,
            "total_erros": 0,
            "tempo_medio_seg": 0,
            "taxa_sucesso": 0,
            "backend_count": {}
        }
        
        cutoff = datetime.now().timestamp() - (dias * 86400)
        
        for filename in os.listdir(self.LOG_DIR):
            filepath = os.path.join(self.LOG_DIR, filename)
            
            if os.path.getmtime(filepath) < cutoff:
                continue
            
            try:
                if filename.endswith('.gz'):
                    import gzip
                    with gzip.open(filepath, 'rt') as f:
                        lines = f.readlines()
                else:
                    with open(filepath, 'r') as f:
                        lines = f.readlines()
                
                for line in lines:
                    try:
                        entry = json.loads(line)
                        
                        if entry['tipo'] == 'recomendacao_ia':
                            stats['total_recomendacoes'] += 1
                            stats['tempo_medio_seg'] += entry.get('tempo_resposta_seg', 0)
                            
                            backend = entry.get('backend', 'unknown')
                            stats['backend_count'][backend] = stats['backend_count'].get(backend, 0) + 1
                        
                        elif entry['tipo'] == 'erro':
                            stats['total_erros'] += 1
                    
                    except json.JSONDecodeError:
                        continue
            
            except Exception as e:
                print(f"⚠️ Erro ao ler log {filename}: {e}")
        
        if stats['total_recomendacoes'] > 0:
            stats['tempo_medio_seg'] /= stats['total_recomendacoes']
            stats['taxa_sucesso'] = (
                (stats['total_recomendacoes'] - stats['total_erros']) /
                stats['total_recomendacoes'] * 100
            )
        
        return stats
