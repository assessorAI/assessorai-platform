import os
import base64
import tempfile
import sys

def ensure_google_credentials_file():
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.isfile(cred_path):
        return cred_path

    cred_b64 = os.getenv("GOOGLE_APPLICATION_BASE64")
    if cred_b64:
        creds_json = base64.b64decode(cred_b64).decode("utf-8")
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as f:
            f.write(creds_json)
            temp_path = f.name
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path
        return temp_path

    raise RuntimeError("Credenciais do Google não encontradas. Defina GOOGLE_APPLICATION_CREDENTIALS ou GOOGLE_APPLICATION_BASE64.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python utils/google_creds.py caminho/para/google-key.json")
        sys.exit(1)
    path = sys.argv[1]
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    print(b64)