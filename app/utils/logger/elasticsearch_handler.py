import logging
import json
from datetime import datetime
import socket
import requests
from requests.exceptions import RequestException

class ElasticsearchHandler(logging.Handler):
    """
    Elasticsearch에 로그를 직접 전송하는 로깅 핸들러
    """
    
    def __init__(self, es_host='localhost', es_port=9200, index_name='app-logs', auth=None):
        """
        Elasticsearch 핸들러 초기화
        
        Args:
            es_host (str): Elasticsearch 호스트
            es_port (int): Elasticsearch 포트
            index_name (str): 인덱스 이름 (날짜가 자동으로 추가됨)
            auth (tuple): (username, password) 인증 정보
        """
        super(ElasticsearchHandler, self).__init__()
        self.es_host = es_host
        self.es_port = es_port
        self.index_name = index_name
        self.auth = auth
        self.hostname = socket.gethostname()
    
    def emit(self, record):
        """
        로그 레코드를 Elasticsearch로 전송
        
        Args:
            record (LogRecord): 로그 레코드
        """
        try:
            # 오늘 날짜를 포함한 인덱스 이름 생성
            today = datetime.now().strftime('%Y.%m.%d')
            index = f"{self.index_name}-{today}"
            
            # 로그 메시지 형식화
            log_entry = self.format_log_entry(record)
            
            # Elasticsearch URL
            url = f"http://{self.es_host}:{self.es_port}/{index}/_doc"
            
            # 로그 전송
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                url, 
                data=json.dumps(log_entry), 
                headers=headers,
                auth=self.auth
            )
            
            # 응답 확인
            if response.status_code >= 400:
                print(f"Elasticsearch error: {response.text}")
        
        except RequestException as e:
            print(f"Error sending log to Elasticsearch: {str(e)}")
        except Exception as e:
            print(f"Unexpected error in ElasticsearchHandler: {str(e)}")
    
    def format_log_entry(self, record):
        """
        로그 레코드를 Elasticsearch에 맞는 형식으로 변환
        
        Args:
            record (LogRecord): 로그 레코드
            
        Returns:
            dict: Elasticsearch에 전송할 JSON 형식
        """
        # 기본 로그 데이터
        log_entry = {
            '@timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger_name': record.name,
            'message': self.format(record),
            'host': self.hostname,
            'path': record.pathname,
            'function': record.funcName,
            'line_number': record.lineno,
            'process': record.process,
            'thread': record.thread
        }
        
        # 예외 정보가 있는 경우 추가
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # 추가 속성이 있는 경우 추가
        if hasattr(record, 'props'):
            log_entry.update(record.props)
        
        return log_entry