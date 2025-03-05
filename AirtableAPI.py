import os
from datetime import datetime
import pandas as pd
from pyairtable import Api
# from dotenv import load_dotenv
from typing import Optional

class AirtableAPI:
    def __init__(self):
        # load_dotenv()
        # self.api_key = os.getenv('AIRTABLE_API_KEY')
        # self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.api_key = "patXjWsIGN6VU5vxf.981a8a91a4a3d2d30be5dc3b0d62d189f1e53d93e104ae5d73db99f28763d741"
        self.base_id = "apppDcbSN4LaOXO1v"

        if not self.api_key or not self.base_id:
            raise ValueError("AIRTABLE_API_KEY와 AIRTABLE_BASE_ID 환경변수가 필요합니다.")

        self.api = Api(self.api_key)

        # 테이블 이름 매핑
        self.table_mapping = {
            "거래대금상위": "top_volume",
            "등락률상위": "top_rate",
            "테마별주도주": "theme_leaders",
            "앤트로픽API응답": "analysis_results"
        }

    def get_table(self, table_name: str):
        """테이블 인스턴스를 가져오는 헬퍼 메서드"""
        mapped_name = self.table_mapping.get(table_name, table_name)
        return self.api.table(self.base_id, mapped_name)

    def get_table_data(self, table_name: str, limit: int = None) -> Optional[pd.DataFrame]:
        """
        Airtable에서 데이터를 가져오는 메서드

        Args:
            table_name (str): 테이블 이름
            limit (int, optional): 가져올 레코드 수 제한. None이면 전체 데이터 가져옴

        Returns:
            Optional[pd.DataFrame]: 데이터프레임 또는 None
        """
        try:
            table = self.get_table(table_name)

            try:
                if limit:
                    records = table.all(max_records=limit)
                else:
                    records = table.all()

                if not records:
                    print(f"테이블 '{table_name}'에서 데이터를 찾을 수 없습니다.")
                    return pd.DataFrame()

                # 데이터 추출
                data = []
                for record in records:
                    if 'fields' in record:
                        fields = record['fields'].copy()  # 필드 복사
                        fields['record_id'] = record['id']  # ID 추가
                        data.append(fields)
                    else:
                        print(f"레코드 형식 오류: {record}")

                if not data:
                    print("변환 가능한 데이터가 없습니다.")
                    return pd.DataFrame()

                df = pd.DataFrame(data)

                # 컬럼 순서 정리 (있는 경우)
                if 'number' in df.columns:
                    df = df.sort_values('number')

                return df

            except Exception as e:
                print(f"데이터 처리 중 오류: {e}")
                return pd.DataFrame()

        except Exception as e:
            print(f"\nAirtable 데이터 가져오기 오류: {str(e)}")
            return None

    def update_table_data(self, df: pd.DataFrame, table_name: str) -> bool:
        """
        데이터프레임을 Airtable에 저장하는 메서드
        """
        try:
            table = self.get_table(table_name)

            # 기존 레코드 삭제
            existing_records = table.all()
            for record in existing_records:
                table.delete(record['id'])

            # 데이터 준비
            records_to_insert = df.to_dict('records')

            # 배치 처리로 레코드 생성 (10개씩 처리)
            chunk_size = 10
            for i in range(0, len(records_to_insert), chunk_size):
                chunk = records_to_insert[i:i + chunk_size]
                table.batch_create(chunk)

            print(f"{table_name}에 총 {len(df)} 개의 데이터가 저장되었습니다.")
            return True

        except Exception as e:
            print(f"\nAirtable 저장 중 오류 발생: {e}")
            return False

    def update_record(self, table_name: str, record_id: str, fields: dict) -> bool:
        """특정 레코드 업데이트"""
        try:
            table = self.get_table(table_name)
            table.update(record_id, fields)
            return True
        except Exception as e:
            print(f"레코드 업데이트 실패: {e}")
            return False

    def delete_record(self, table_name: str, record_id: str) -> bool:
        """특정 레코드 삭제"""
        try:
            table = self.get_table(table_name)
            table.delete(record_id)
            return True
        except Exception as e:
            print(f"레코드 삭제 실패: {e}")
            return False


def test_airtable_connection():
    """Airtable 연결 테스트 함수"""
    try:
        # 테스트 데이터 생성
        test_df = pd.DataFrame({
            'number': [1, 2, 3],
            'code': ['196170', '042660', '017860'],
            'name': ['알테오젠', '한화오션', 'DS단석'],
            'rate': [15.00, 6.94, 16.00],
            'volume': [11869, 5949, 2866],
            'timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')] * 3
        })

        airtable = AirtableAPI()
        success = airtable.update_table_data(test_df, "top_volume")

        if success:
            print("테스트 데이터 저장 성공")
            saved_data = airtable.get_table_data("top_volume")
            if saved_data is not None and not saved_data.empty:
                print("저장된 데이터 확인 성공")
                return True

        return False

    except Exception as e:
        print(f"Airtable 연결 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_airtable_connection()