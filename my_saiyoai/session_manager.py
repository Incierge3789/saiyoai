# session_manager.py

class SessionManager:
    def __init__(self):
        self.reset_session()

    def reset_session(self):
        # セッションをリセットするロジック
        # 例: トークンカウンターのリセット
        self.token_counter = 0

    def check_session_state(self, token_count):
        # トークン制限を超えた場合にセッションをリセットする
        self.token_counter += token_count
        if self.token_counter > 8000:  # 8192 トークンに近づいたらリセット
            self.reset_session()
