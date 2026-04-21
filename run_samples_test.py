import os
import glob
from app.core.container import Container

def main():
    """
    sample_logs 디렉토리의 모든 로그 파일을 읽어 위협 분석을 수행하는 테스트 스크립트입니다.
    """
    # 0. 의존성 주입 컨테이너 초기화
    container = Container()
    incident_service = container.incident_service()

    # 1. 샘플 로그 디렉토리 확인
    sample_dir = "sample_logs"
    
    if not os.path.exists(sample_dir):
        print(f"Error: '{sample_dir}' directory not found. Please make sure it exists in the project root.")
        return

    # 2. 모든 .log 파일 검색 및 정렬
    log_files = glob.glob(os.path.join(sample_dir, "*.log"))
    
    if not log_files:
        print(f"No .log files found in {sample_dir}/.")
        return

    print(f"🚀 Found {len(log_files)} sample logs. Starting analysis sequence...")

    # 3. 순차적으로 분석 실행
    for log_path in sorted(log_files):
        filename = os.path.basename(log_path)
        print("\n" + "#" * 70)
        print(f"### [TEST RUN] File: {filename}")
        print("#" * 70)
        
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                log_content = f.read()
            
            # 실제 서비스 로직 호출
            incident_service.incident_analysis(log_content)
            
        except Exception as e:
            print(f"!!! Error processing {filename}: {str(e)}")
            
    print("\n" + "=" * 70)
    print("✅ All sample log tests completed.")
    print("=" * 70)

if __name__ == "__main__":
    main()
