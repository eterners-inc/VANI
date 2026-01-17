# free/main_free.py
import sys
import os
import hashlib
import numpy as np  # [특허 필수] 수학 연산을 위해 추가

# 실행 환경 경로 설정
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, base_path)

from PyQt6.QtWidgets import QApplication, QMessageBox

# 1. 엔진 로드
try:
    import evolution_wipe_core
except ImportError:
    app_dummy = QApplication(sys.argv)
    QMessageBox.critical(None, "Error", "Core Engine (pyd) not found.")
    sys.exit(1)

try:
    from gui.main_window import EvolutionWipeApp
except ImportError as e:
    app_dummy = QApplication(sys.argv)
    QMessageBox.critical(None, "Error", f"GUI Module Error: {e}")
    sys.exit(1)

# 2. Free 엔진 래퍼 (수학적 붕괴 기능 탑재)
class RustEngineWrapperFree:
    def __init__(self):
        # 통합된 RustWiper 사용
        if hasattr(evolution_wipe_core, 'RustWiper'):
            self.rust_wiper = evolution_wipe_core.RustWiper()
        else:
            self.rust_wiper = None
            
        if self.rust_wiper is None:
             raise ImportError("Version Mismatch: 'RustWiper' class missing in pyd.")

    def set_mode(self, is_pro):
        pass

    # [특허 청구항 3, 4 구현] 그램-슈미트 직교화 및 시드 다양화
    def gram_schmidt_header_wipe(self, filepath):
        """
        파일의 헤더(앞부분 4KB)를 읽어 원본과 수학적으로 직교하는(Orthogonal) 
        노이즈 패턴으로 덮어씀으로써 복구 알고리즘을 무력화함.
        """
        try:
            # 파일이 쓰기 가능한지 확인
            if not os.access(filepath, os.W_OK): return

            header_size = 4096
            f_size = os.path.getsize(filepath)
            if f_size < header_size:
                header_size = f_size

            with open(filepath, "r+b") as f:
                # 1. 원본 헤더 읽기 (상태 벡터 V)
                header_data = f.read(header_size)
                if not header_data: return

                # 2. 벡터화 (Byte -> Vector)
                v = np.frombuffer(header_data, dtype=np.uint8).astype(np.float32)

                # 3. 초기 노이즈 벡터 생성 (Vector U) - 시드 다양화 적용
                # 파일 경로와 크기를 기반으로 고유 시드 생성 (청구항 4)
                seed_str = f"{filepath}{f_size}".encode()
                # 32비트 정수 범위 내로 시드 제한
                seed_val = int(hashlib.sha256(seed_str).hexdigest(), 16) % (2**32)
                np.random.seed(seed_val)
                u = np.random.rand(len(v)) * 255.0

                # 4. 그램-슈미트 직교화 (Gram-Schmidt) (청구항 3)
                # proj = (<u,v> / <v,v>) * v
                dot_uv = np.dot(u, v)
                dot_vv = np.dot(v, v)

                if dot_vv == 0:
                    orthogonal_vector = u
                else:
                    projection = (dot_uv / dot_vv) * v
                    orthogonal_vector = u - projection

                # 5. 다시 바이트로 변환 및 덮어쓰기
                collapsed_bytes = np.mod(np.abs(orthogonal_vector), 256).astype(np.uint8).tobytes()
                
                f.seek(0)
                f.write(collapsed_bytes)
                f.flush()
                # Python 레벨에서 닫으면 OS가 처리함
                
        except Exception as e:
            # 수학적 붕괴 실패 시에도 Rust 엔진이 뒤에서 처리하므로 치명적 오류는 아님
            # 디버깅 시에만 출력: print(f"[Math Engine Warning] {e}")
            pass

    # [핵심] military_mode 인자를 받지만, Free 버전은 무조건 Fast Mode로 작동
    def wipe_targets(self, targets, progress_callback=None, military_mode=False):
        report = {"results": [], "cert_path": None}
        total = len(targets)
        
        if total > 0:
            path = targets[0] # Free는 파일 1개만 처리
            
            if progress_callback: 
                progress_callback(0, 1, f"Collapsing: {os.path.basename(path)}")
            
            result = {"file_path": path, "success": False, "error": None}
            
            try:
                # [STEP 1] Python Math Engine: 헤더 정밀 타격 (특허 기술 적용)
                self.gram_schmidt_header_wipe(str(path))

                # [STEP 2] Rust Core Engine: 전체 고속 삭제 (Flash Collapse)
                # passes=1, fixed_mode=True (초고속)
                self.rust_wiper.wipe(str(path), 1, True)
                
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)
            
            report["results"].append(result)
            
            if progress_callback: progress_callback(1, 1, "Completed")

        return report

def main():
    app = QApplication(sys.argv)
    try:
        wrapper = RustEngineWrapperFree()
        window = EvolutionWipeApp(engine_wrapper=wrapper, is_pro_version=False)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "Startup Error", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()